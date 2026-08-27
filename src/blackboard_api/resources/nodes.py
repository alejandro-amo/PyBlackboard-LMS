from __future__ import annotations

import logging
from typing import Any, Iterator

from ..identifiers import (
    COURSE_IDENTIFIER_POLICY,
    NODE_IDENTIFIER_POLICY,
    USER_IDENTIFIER_POLICY,
    encode_identifier,
    validate_creation_data,
    validate_data,
    validate_identifier,
)

logger = logging.getLogger(__name__)


class NodeResource:
    """Atomic operations for institutional nodes."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> list[dict]:
        """Return all nodes, collecting every page."""
        return list(self.iter())

    def iter(self) -> Iterator[dict]:
        """Iterate over nodes without accumulating the full collection."""
        return self.client._iter_paginated(
            "/learn/api/public/v1/institutionalHierarchy/nodes"
        )

    def get(self, *, node_identifier: str) -> dict:
        """Get a node by primary ID or ``externalId``."""
        identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(identifier)}"
        )
        return self.client._request_json("GET", path)

    def create(self, data: dict) -> dict:
        """Create a node; Blackboard generates its primary ID."""
        return self.client._request_json(
            "POST",
            "/learn/api/public/v1/institutionalHierarchy/nodes",
            json=validate_creation_data(data),
        )

    def update(self, *, node_identifier: str, data: dict) -> dict:
        """Update a node by primary ID or ``externalId``."""
        identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(identifier)}"
        )
        return self.client._request_json(
            "PATCH", path, json=validate_data(data)
        )

    def delete(self, *, node_identifier: str) -> None:
        """Delete a node by primary ID or ``externalId``."""
        identifier = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(identifier)}"
        )
        self.client._request("DELETE", path)

    def list_by_course(self, *, course_identifier: str) -> list[dict]:
        """List nodes associated with a course."""
        identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        path = (
            f"/learn/api/public/v1/courses/{encode_identifier(identifier)}/nodes"
        )
        return list(self.client._iter_paginated(path))

    def list_by_user(self, *, user_identifier: str) -> list[dict]:
        """List nodes associated with a user."""
        identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/users/{encode_identifier(identifier)}/nodes"
        return list(self.client._iter_paginated(path))
