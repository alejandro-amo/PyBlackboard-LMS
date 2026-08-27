"""Public facade for the API usage quota."""

from __future__ import annotations

from typing import Callable


class ApiQuotaFacade:
    """Expose API quota state separately from pagination settings."""

    def __init__(
        self,
        get_state: Callable[[], dict[str, int | None]],
    ) -> None:
        self._get_state = get_state

    def get(self) -> dict[str, int | None]:
        """Return remaining requests and the daily request maximum."""
        return self._get_state()
