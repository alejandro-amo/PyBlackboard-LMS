"""HTTP transport with timeout, API quota, and retry handling."""

from __future__ import annotations

import email.utils
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any

import requests

from .errors import QuotaExhaustedError, TransportError
from .api_quota import ApiQuotaState

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 5.0
MAX_RETRY_DELAY_SECONDS = 60.0
RETRYABLE_STATUS_CODES = frozenset({408, 429, 502, 503, 504})
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ReadTimeout,
    requests.exceptions.ConnectionError,
)


class Transport:
    """Centralize tolerant HTTP requests for the API."""

    def __init__(
        self,
        api_quota: ApiQuotaState | None = None,
        timeout: float | tuple[float, float] = (10, 60),
        session: requests.Session | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be zero or greater")
        self.session = session or requests.Session()
        self._api_quota = api_quota or ApiQuotaState()
        self.timeout = timeout
        self.max_retries = max_retries

    def request(
        self,
        method: str,
        url: str,
        max_retries: int | None = None,
        backoff: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        track_api_quota: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute a request and retry transient failures."""
        max_retries = self.max_retries if max_retries is None else max_retries
        if max_retries < 0:
            raise ValueError("max_retries must be zero or greater")
        if backoff < 0:
            raise ValueError("backoff must not be negative")
        if track_api_quota and self._api_quota.remaining == 0:
            logger.error("Request blocked because known API quota is zero")
            raise QuotaExhaustedError("Blackboard API quota is exhausted")

        kwargs.setdefault("timeout", self.timeout)
        response: requests.Response | None = None
        total_attempts = max_retries + 1
        for attempt in range(1, total_attempts + 1):
            logger.debug(
                "HTTP request %s (attempt %s/%s)",
                method.upper(), attempt, total_attempts,
            )
            try:
                response = self.session.request(method, url, **kwargs)
            except RETRYABLE_EXCEPTIONS as exc:
                if attempt == total_attempts:
                    logger.error("Network error after retry limit")
                    raise TransportError(
                        f"Network error for {method.upper()} {url}"
                    ) from exc
                time.sleep(_exponential_jitter(attempt, backoff))
                continue
            except requests.exceptions.RequestException as exc:
                raise TransportError(
                    f"Network error for {method.upper()} {url}"
                ) from exc

            if track_api_quota:
                self._api_quota.update_from_response(response)
            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response
            if attempt == total_attempts:
                logger.warning(
                    "HTTP response %s after retry limit",
                    response.status_code,
                )
                return response
            delay = _retry_delay(response, attempt, backoff)
            logger.warning(
                "HTTP response %s; retrying in %.2f seconds",
                response.status_code,
                delay,
            )
            time.sleep(delay)

        assert response is not None
        return response


def _exponential_jitter(attempt: int, backoff: float) -> float:
    maximum = min(MAX_RETRY_DELAY_SECONDS, backoff * (2 ** (attempt - 1)))
    return random.uniform(0, maximum)


def _retry_delay(response: requests.Response, attempt: int, backoff: float) -> float:
    """Return Retry-After when valid and safe; otherwise use backoff."""
    header = response.headers.get("Retry-After")
    if header:
        delay = _parse_retry_after(header)
        if delay is not None:
            if delay > MAX_RETRY_DELAY_SECONDS:
                raise TransportError(
                    f"Retry-After is too long: {delay:.0f} seconds"
                )
            return max(0.0, delay)
    return _exponential_jitter(attempt, backoff)


def _parse_retry_after(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        pass
    try:
        target = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return (target - datetime.now(timezone.utc)).total_seconds()
