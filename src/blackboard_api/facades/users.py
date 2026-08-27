"""Public facade for atomic and composite user operations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .resources import ResourceFacade


class UserFacade(ResourceFacade):
    """Expose user resource operations and convenience services."""

    def __init__(self, resource: Any, service: Any) -> None:
        super().__init__(resource)
        self._service = service

    def list(self) -> list[dict]:
        return self._resource.list()

    def iter(self) -> Iterator[dict]:
        return self._resource.iter()

    def get(self, *, user_identifier: str) -> dict:
        return self._resource.get(user_identifier=user_identifier)

    def create(self, data: dict) -> dict:
        """Create a user without Blackboard-generated ``id`` or UUID."""
        return self._resource.create(data)

    def update(self, *, user_identifier: str, data: dict) -> dict:
        return self._resource.update(
            user_identifier=user_identifier, data=data
        )

    def delete(self, *, user_identifier: str) -> None:
        return self._resource.delete(user_identifier=user_identifier)

    def set_available(self, *, user_identifier: str) -> dict:
        return self._resource.set_available(user_identifier=user_identifier)

    def set_unavailable(self, *, user_identifier: str) -> dict:
        return self._resource.set_unavailable(user_identifier=user_identifier)

    def set_disabled(self, *, user_identifier: str) -> dict:
        return self._resource.set_disabled(user_identifier=user_identifier)

    def assign_node(
        self,
        *,
        user_identifier: str,
        node_identifier: str,
        primary: bool | None = None,
    ) -> dict:
        return self._resource.assign_node(
            user_identifier=user_identifier,
            node_identifier=node_identifier,
            primary=primary,
        )

    def unassign_node(
        self, *, user_identifier: str, node_identifier: str
    ) -> None:
        return self._resource.unassign_node(
            user_identifier=user_identifier,
            node_identifier=node_identifier,
        )

    def list_by_node(self, *, node_identifier: str) -> list[dict]:
        return self._resource.list_by_node(node_identifier=node_identifier)

    def iter_by_node(self, *, node_identifier: str) -> Iterator[dict]:
        return self._resource.iter_by_node(node_identifier=node_identifier)

    def change_username(
        self, *, current_username: str, new_username: str
    ) -> dict:
        return self._service.change_username(
            current_username=current_username,
            new_username=new_username,
        )
