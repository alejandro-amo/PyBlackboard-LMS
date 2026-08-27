"""Public facade for atomic and composite term operations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .resources import ResourceFacade


class TermFacade(ResourceFacade):
    """Expose term resource operations and course-related lookups."""

    def __init__(self, resource: Any, service: Any) -> None:
        super().__init__(resource)
        self._service = service

    def list(self) -> list[dict]:
        return self._resource.list()

    def iter(self) -> Iterator[dict]:
        return self._resource.iter()

    def get(self, *, term_identifier: str) -> dict:
        return self._resource.get(term_identifier=term_identifier)

    def create(self, data: dict) -> dict:
        """Create a term without Blackboard-generated ``id`` or UUID."""
        return self._resource.create(data)

    def update(self, *, term_identifier: str, data: dict) -> dict:
        return self._resource.update(
            term_identifier=term_identifier, data=data
        )

    def delete(self, *, term_identifier: str) -> None:
        return self._resource.delete(term_identifier=term_identifier)

    def get_by_course(self, *, course_identifier: str) -> dict | None:
        return self._service.get_by_course(
            course_identifier=course_identifier
        )
