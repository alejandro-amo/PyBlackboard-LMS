"""Facades that expose resources without revealing internal structure."""

from __future__ import annotations

from typing import Any
from collections.abc import Iterator


class ResourceFacade:
    """Expose atomic operations from a concrete resource."""

    def __init__(self, resource: Any) -> None:
        self._resource = resource


class NodeFacade(ResourceFacade):
    """Public facade for node operations."""

    def list(self) -> list[dict]:
        return self._resource.list()

    def iter(self) -> Iterator[dict]:
        return self._resource.iter()

    def get(self, *, node_identifier: str) -> dict:
        return self._resource.get(node_identifier=node_identifier)

    def create(self, data: dict) -> dict:
        """Create a node without Blackboard-generated ``id`` or UUID."""
        return self._resource.create(data)

    def update(self, *, node_identifier: str, data: dict) -> dict:
        return self._resource.update(
            node_identifier=node_identifier, data=data
        )

    def delete(self, *, node_identifier: str) -> None:
        return self._resource.delete(node_identifier=node_identifier)

    def list_by_course(self, *, course_identifier: str) -> list[dict]:
        return self._resource.list_by_course(
            course_identifier=course_identifier
        )

    def list_by_user(self, *, user_identifier: str) -> list[dict]:
        return self._resource.list_by_user(user_identifier=user_identifier)


class EnrollmentRoleFacade(ResourceFacade):
    """Public facade for enrollment roles, which has no mutating operations."""

    def list(self) -> list[dict]:
        return self._resource.list()

    def iter(self) -> Iterator[dict]:
        return self._resource.iter()
