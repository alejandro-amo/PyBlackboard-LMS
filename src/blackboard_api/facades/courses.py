"""Public facade for atomic and composite course operations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .resources import ResourceFacade


class CourseFacade(ResourceFacade):
    """Expose course resource operations and convenience services."""

    def __init__(self, resource: Any, service: Any) -> None:
        super().__init__(resource)
        self._service = service

    def list(self) -> list[dict]:
        return self._resource.list()

    def iter(self) -> Iterator[dict]:
        return self._resource.iter()

    def get(self, *, course_identifier: str) -> dict:
        return self._resource.get(course_identifier=course_identifier)

    def create(self, *, data: dict) -> dict:
        """Create a course without Blackboard-generated ``id`` or UUID."""
        return self._resource.create(data)

    def update(self, *, course_identifier: str, data: dict) -> dict:
        return self._resource.update(
            course_identifier=course_identifier, data=data
        )

    def delete(self, *, course_identifier: str) -> None:
        return self._resource.delete(course_identifier=course_identifier)

    def set_available(self, *, course_identifier: str) -> dict:
        return self._resource.set_available(course_identifier=course_identifier)

    def set_unavailable(self, *, course_identifier: str) -> dict:
        return self._resource.set_unavailable(course_identifier=course_identifier)

    def set_disabled(self, *, course_identifier: str) -> dict:
        return self._resource.set_disabled(course_identifier=course_identifier)

    def assign_node(
        self,
        *,
        course_identifier: str,
        node_identifier: str,
        primary: bool | None = None,
    ) -> dict:
        return self._resource.assign_node(
            course_identifier=course_identifier,
            node_identifier=node_identifier,
            primary=primary,
        )

    def unassign_node(
        self, *, course_identifier: str, node_identifier: str
    ) -> None:
        return self._resource.unassign_node(
            course_identifier=course_identifier,
            node_identifier=node_identifier,
        )

    def list_by_node(self, *, node_identifier: str) -> list[dict]:
        return self._resource.list_by_node(node_identifier=node_identifier)

    def iter_by_node(self, *, node_identifier: str) -> Iterator[dict]:
        return self._resource.iter_by_node(node_identifier=node_identifier)

    def assign_term(
        self, *, course_identifier: str, term_identifier: str
    ) -> dict:
        return self._service.assign_term(
            course_identifier=course_identifier,
            term_identifier=term_identifier,
        )

    def unassign_term(self, *, course_identifier: str) -> dict:
        return self._service.unassign_term(
            course_identifier=course_identifier
        )

    def list_by_term(self, *, term_identifier: str) -> list[dict]:
        """List courses assigned to a term by primary ID or ``externalId``."""
        return self._service.list_by_term(term_identifier=term_identifier)

    def get_copy_history(
        self, *, course_identifier: str
    ) -> list[dict] | None:
        """Return the copy history of a given course."""
        return self._service.get_copy_history(course_identifier=course_identifier)
