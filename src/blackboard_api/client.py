import time
import logging
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from typing import Any

from .auth import AuthService
from .config import api_config_from_environment
from .errors import (
    NotFoundError,
    QuotaExhaustedError,
    WriteNotEnabledError,
    ResponseFormatError,
)
from .api_quota import ApiQuotaState
from .transport import Transport
from .resources.courses import CourseResource
from .resources.users import UserResource
from .resources.enrollments import EnrollmentResource
from .resources.nodes import NodeResource
from .resources.enrollment_roles import EnrollmentRoleResource
from .resources.terms import TermResource
from .services.enrollments import EnrollmentService
from .services.users import UserService
from .services.courses import CourseService, TermService
from .facades.resources import NodeFacade, EnrollmentRoleFacade
from .facades.enrollments import EnrollmentFacade
from .facades.users import UserFacade
from .facades.courses import CourseFacade
from .facades.terms import TermFacade
from .facades.api_quota import ApiQuotaFacade

logger = logging.getLogger(__name__)


class BlackboardAPI:
    def __init__(
        self, url: str | None = None, client_id: str | None = None,
        client_secret: str | None = None,
        env_file: str | None = None,
        enable_write: bool = False,
        max_retries: int | None = None,
        results_per_page: int = 100,
    ) -> None:
        if url is None and client_id is None and client_secret is None:
            if env_file is None:
                raise ValueError(
                    "env_file is required when credentials are not provided"
                )
            config = api_config_from_environment(env_file)
            url = config["url"]
            client_id = config["client_id"]
            client_secret = config["client_secret"]
            timeout = (config["connect_timeout"], config["read_timeout"])
        elif not all((url, client_id, client_secret)):
            raise ValueError("Provide all three credentials or none")
        else:
            timeout = (10, 60)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("BB_INSTANCE_URL must be a valid HTTPS URL")
        self._url = url.rstrip("/")
        self.enable_write = enable_write
        if not isinstance(self.enable_write, bool):
            raise TypeError("enable_write must be a boolean")
        self.results_per_page = results_per_page
        self._api_quota = ApiQuotaState()
        self._transport = Transport(
            self._api_quota,
            timeout=timeout,
            max_retries=(3 if max_retries is None else max_retries),
        )
        self._auth = AuthService(
            self._url, client_id, client_secret, self._transport
        )
        self._courses_resource = CourseResource(self)
        self._users_resource = UserResource(self)
        self._enrollments_resource = EnrollmentResource(self)
        self._nodes_resource = NodeResource(self)
        self._enrollment_roles_resource = EnrollmentRoleResource(self)
        self._terms_resource = TermResource(self)
        self._enrollment_service = EnrollmentService(
            self._enrollments_resource, self._enrollment_roles_resource
        )
        self._user_service = UserService(self._users_resource)
        self._course_service = CourseService(
            self._courses_resource, self._terms_resource
        )
        self._term_service = TermService(
            self._courses_resource, self._terms_resource
        )
        self.courses = CourseFacade(self._courses_resource, self._course_service)
        self.users = UserFacade(self._users_resource, self._user_service)
        self.enrollments = EnrollmentFacade(
            self._enrollments_resource, self._enrollment_service
        )
        self.nodes = NodeFacade(self._nodes_resource)
        self.enrollment_roles = EnrollmentRoleFacade(self._enrollment_roles_resource)
        self.terms = TermFacade(self._terms_resource, self._term_service)
        self.api_quota = ApiQuotaFacade(
            self._get_api_quota,
        )

    @property
    def token(self) -> str | None:
        return self._auth.token

    @property
    def api_quota_remaining(self) -> int | None:
        return self._api_quota.remaining

    @property
    def max_requests_per_day(self) -> int | None:
        return self._api_quota.max_requests_per_day

    @property
    def results_per_page(self) -> int:
        """Return the default number of results requested per collection page."""
        return self._results_per_page

    @results_per_page.setter
    def results_per_page(self, value: int) -> None:
        """Set the default collection result count for future requests."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("results_per_page must be a positive integer")
        self._results_per_page = value

    def _ensure_api_quota(self) -> None:
        """Probe Blackboard once when no quota headers are known yet."""
        if (
            self._api_quota.max_requests_per_day is None
            and self._api_quota.remaining is None
        ):
            self._update_api_quota()

    def _get_api_quota(self) -> dict[str, int | None]:
        self._ensure_api_quota()
        return {
            "remaining": self.api_quota_remaining,
            "max_requests_per_day": self.max_requests_per_day,
        }

    def _authenticate(self) -> None:
        previous_token = self._auth.token
        token = self._auth.authenticate(time.time())
        if token != previous_token:
            self._update_api_quota()

    def _get_headers(self) -> dict[str, str]:
        self._authenticate()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path_or_url: str, **kwargs: Any) -> requests.Response:
        if not self.enable_write and method.upper() not in {"GET", "HEAD", "OPTIONS"}:
            logger.warning("Writes are disabled; blocked %s", method.upper())
            raise WriteNotEnabledError(
                f"{method.upper()} requires enable_write=True"
            )
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else urljoin(self._url + "/", path_or_url.lstrip("/"))
        )
        headers = kwargs.pop("headers", None)
        if headers is None:
            headers = self._get_headers()
        response = self._transport.request(method, url, headers=headers, **kwargs)
        logger.debug("HTTP request completed: %s", method.upper())
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {url}") from exc
            raise
        return response

    def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            return self._request(method, path, **kwargs).json()
        except ValueError as exc:
            raise ResponseFormatError(
                f"Invalid JSON response for {method.upper()} {path}"
            ) from exc

    def _iter_paginated(self, path: str):
        """Yield collection items one page at a time without accumulating them."""
        url = BlackboardAPI._with_results_per_page(self, path)
        while url:
            data = self._request_json("GET", url)
            if not isinstance(data, dict):
                raise ResponseFormatError(
                    "Blackboard collection is not a JSON object"
                )
            if "results" not in data:
                raise ResponseFormatError("Collection does not contain results")
            results = data["results"]
            paging = data.get("paging", {})
            if not isinstance(results, list):
                raise ResponseFormatError("Collection results is not a list")
            if not isinstance(paging, dict):
                raise ResponseFormatError("Collection paging is not an object")
            next_page = paging.get("nextPage")
            if next_page is not None and not isinstance(next_page, str):
                raise ResponseFormatError("Collection paging.nextPage is not text")
            yield from results
            url = next_page

    def _with_results_per_page(self, path: str) -> str:
        """Add the configured pagination limit without changing an explicit one."""
        parsed = urlparse(path)
        query = parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key == "limit" for key, _ in query):
            query.append((
                "limit",
                str(getattr(self, "_results_per_page", 100)),
            ))
        return urlunparse(parsed._replace(query=urlencode(query)))

    def _update_api_quota(self) -> dict[str, int | None]:
        self._request("GET", "/learn/api/public/v1/users/me")
        return {
            "max_requests_per_day": self._api_quota.max_requests_per_day,
            "remaining": self._api_quota.remaining,
        }
