from __future__ import annotations

import logging
from typing import Any, Iterator

from ..identifiers import (
    NODE_IDENTIFIER_POLICY,
    USER_IDENTIFIER_POLICY,
    encode_identifier,
    validate_creation_data,
    validate_data,
    validate_identifier,
    validate_primary,
)

logger = logging.getLogger(__name__)


class UserResource:
    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> list[dict]:
        """List users; identifiers are not accepted."""
        return list(self.iter())

    def iter(self) -> Iterator[dict]:
        """Iterate over users; identifiers are not accepted."""
        return self.client._iter_paginated("/learn/api/public/v1/users")

    def get(self, *, user_identifier: str) -> dict:
        """Get a user by primary ID, externalId, userName, or UUID."""
        identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/users/{encode_identifier(identifier)}"
        return self.client._request_json("GET", path)

    def list_by_node(self, *, node_identifier: str) -> list[dict]:
        """Return users belonging to a node by primary ID or ``externalId``."""
        return list(self.iter_by_node(node_identifier=node_identifier))

    def iter_by_node(self, *, node_identifier: str) -> Iterator[dict]:
        """Iterate over users belonging to a node."""
        node_identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        associations = self.client._iter_paginated(
            f"/learn/api/public/v1/institutionalHierarchy/nodes/{encode_identifier(node_identifier)}/users"
        )
        return associations

    def create(self, data: dict) -> dict:
        """Create a user; Blackboard generates its primary ID and UUID."""
        return self.client._request_json(
            "POST",
            "/learn/api/public/v1/users",
            json=validate_creation_data(data),
        )

    def update(self, *, user_identifier: str, data: dict) -> dict:
        """Update a user by primary ID, externalId, userName, or UUID."""
        identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/users/{encode_identifier(identifier)}"
        return self.client._request_json(
            "PATCH", path, json=validate_data(data)
        )

    def set_available(self, *, user_identifier: str) -> dict:
        """Make a user account available."""
        return self.update(
            user_identifier=user_identifier,
            data={"availability": {"available": "Yes"}},
        )

    def set_unavailable(self, *, user_identifier: str) -> dict:
        """Make a user account unavailable without disabling its record."""
        return self.update(
            user_identifier=user_identifier,
            data={"availability": {"available": "No"}},
        )

    def set_disabled(self, *, user_identifier: str) -> dict:
        """Disable a user record while preserving its data."""
        return self.update(
            user_identifier=user_identifier,
            data={"availability": {"available": "Disabled"}},
        )

    def delete(self, *, user_identifier: str) -> None:
        """Delete a user by primary ID, externalId, userName, or UUID."""
        identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        self.client._request(
            "DELETE", f"/learn/api/public/v1/users/{encode_identifier(identifier)}"
        )

    def assign_node(
        self, *, user_identifier: str, node_identifier: str,
        primary: bool | None = None,
    ) -> dict:
        """Associate a user with a node using valid identifiers."""
        user_identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        node_identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        primary = validate_primary(primary)
        body = {} if primary is None else {"isPrimary": primary}
        return self.client._request_json(
            "PUT",
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(node_identifier)}/users/"
            f"{encode_identifier(user_identifier)}",
            json=body,
        )

    def unassign_node(
        self, *, user_identifier: str, node_identifier: str
    ) -> None:
        """Remove a user association from a node."""
        user_identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        node_identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        self.client._request(
            "DELETE",
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(node_identifier)}/users/"
            f"{encode_identifier(user_identifier)}",
        )
