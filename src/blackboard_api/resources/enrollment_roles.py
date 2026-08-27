from __future__ import annotations

from typing import Any, Iterator


class EnrollmentRoleResource:
    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> list[dict]:
        """List all available course enrollment roles."""
        return list(self.iter())

    def iter(self) -> Iterator[dict]:
        """Iterate over all available course enrollment roles."""
        return self.client._iter_paginated("/learn/api/public/v1/courseRoles")
