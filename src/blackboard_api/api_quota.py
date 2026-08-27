import logging
from dataclasses import dataclass
from typing import Optional
import requests

from .errors import QuotaExhaustedError

logger = logging.getLogger(__name__)


@dataclass
class ApiQuotaState:
    max_requests_per_day: Optional[int] = None
    remaining: Optional[int] = None
    retry_after: Optional[int] = None

    def update_from_response(self, response: requests.Response) -> None:
        quota_limit = response.headers.get("X-Rate-Limit-Limit")
        remaining = response.headers.get("X-Rate-Limit-Remaining")
        retry_after = response.headers.get("Retry-After")
        if remaining is None and (
            self.max_requests_per_day is not None or self.remaining is not None
        ):
            logger.warning(
                "Blackboard did not send the remaining-requests header; "
                "preserving the last known value."
            )
        parsed_limit = _parse_int(quota_limit)
        parsed_remaining = _parse_int(remaining)
        parsed_retry_after = _parse_int(retry_after)
        if quota_limit is not None and parsed_limit is None:
            logger.warning(
                "Invalid X-Rate-Limit-Limit header; preserving the prior value."
            )
        if remaining is not None and parsed_remaining is None:
            logger.warning(
                "Invalid X-Rate-Limit-Remaining header; preserving the prior "
                "value."
            )
        if retry_after is not None and parsed_retry_after is None:
            logger.warning(
                "Invalid Retry-After header; preserving the prior value."
            )
        if parsed_limit is not None:
            self.max_requests_per_day = parsed_limit
        if parsed_remaining is not None:
            self.remaining = parsed_remaining
        if parsed_retry_after is not None:
            self.retry_after = parsed_retry_after
        if self.remaining == 0:
            logger.error("Blackboard reported zero remaining API requests")
            raise QuotaExhaustedError("Blackboard API quota is exhausted")


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
