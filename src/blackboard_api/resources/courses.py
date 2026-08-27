from __future__ import annotations

import logging
from typing import Any, Iterator

from ..identifiers import (
    COURSE_IDENTIFIER_POLICY,
    NODE_IDENTIFIER_POLICY,
    encode_identifier,
    validate_creation_data,
    validate_data,
    validate_identifier,
    validate_primary,
)

logger = logging.getLogger(__name__)


class CourseResource:
    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> list[dict]:
        """List courses; identifiers are not accepted."""
        return list(self.iter())

    def iter(self) -> Iterator[dict]:
        """Iterate over courses; identifiers are not accepted."""
        return self.client._iter_paginated("/learn/api/public/v2/courses")

    def get(self, *, course_identifier: str) -> dict:
        """Get a course by primary ID, externalId, courseId, or UUID."""
        identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v2/courses/{encode_identifier(identifier)}"
        return self.client._request_json("GET", path)

    def create(self, data: dict) -> dict:
        """Create a course; Blackboard generates its primary ID and UUID."""
        return self.client._request_json(
            "POST",
            "/learn/api/public/v2/courses",
            json=validate_creation_data(data),
        )

    def update(self, *, course_identifier: str, data: dict) -> dict:
        """Update a course by primary ID, externalId, courseId, or UUID."""
        identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v2/courses/{encode_identifier(identifier)}"
        return self.client._request_json(
            "PATCH", path, json=validate_data(data)
        )

    def set_available(self, *, course_identifier: str) -> dict:
        """Make a course available to users."""
        return self.update(
            course_identifier=course_identifier,
            data={"availability": {"available": "Yes"}},
        )

    def set_unavailable(self, *, course_identifier: str) -> dict:
        """Make a course unavailable without disabling its record."""
        return self.update(
            course_identifier=course_identifier,
            data={"availability": {"available": "No"}},
        )

    def set_disabled(self, *, course_identifier: str) -> dict:
        """Disable a course record while preserving its data."""
        return self.update(
            course_identifier=course_identifier,
            data={"availability": {"available": "Disabled"}},
        )

    def delete(self, *, course_identifier: str) -> None:
        """Delete a course by primary ID, externalId, courseId, or UUID."""
        identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v2/courses/{encode_identifier(identifier)}"
        self.client._request("DELETE", path)

    def assign_node(
        self, *, course_identifier: str, node_identifier: str,
        primary: bool | None = None,
    ) -> dict:
        """Associate a course with a node."""
        course_id = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        node_id = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        primary = validate_primary(primary)
        body = {} if primary is None else {"isPrimary": primary}
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(node_id)}/courses/{encode_identifier(course_id)}"
        )
        return self.client._request_json("PUT", path, json=body)

    def unassign_node(
        self, *, course_identifier: str, node_identifier: str
    ) -> None:
        """Remove a course association from a node."""
        course_id = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        node_id = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(node_id)}/courses/{encode_identifier(course_id)}"
        )
        self.client._request("DELETE", path)

    def list_by_node(self, *, node_identifier: str) -> list[dict]:
        """List courses belonging to a node identified by primary ID or externalId."""
        return list(self.iter_by_node(node_identifier=node_identifier))

    def iter_by_node(self, *, node_identifier: str) -> Iterator[dict]:
        """Iterate over courses belonging to a node."""
        node_id = validate_identifier(
            node_identifier, name="node_identifier",
            policy=NODE_IDENTIFIER_POLICY,
        )
        path = (
            "/learn/api/public/v1/institutionalHierarchy/nodes/"
            f"{encode_identifier(node_id)}/courses"
        )
        return self.client._iter_paginated(path)

    def _list_by_term_primary_id(self, *, term_id: str) -> list[dict]:
        """List courses for a known term primary ID."""
        return list(
            self.client._iter_paginated(
                f"/learn/api/public/v2/courses?termId={term_id}"
            )
        )
