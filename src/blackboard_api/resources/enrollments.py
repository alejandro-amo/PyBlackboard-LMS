from __future__ import annotations

import logging
from typing import Any, Iterator

from ..identifiers import (
    COURSE_IDENTIFIER_POLICY,
    USER_IDENTIFIER_POLICY,
    encode_identifier,
    validate_identifier,
)

logger = logging.getLogger(__name__)


class EnrollmentResource:
    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _path(course_identifier: str, user_identifier: str) -> str:
        course_identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        user_identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        return (
            "/learn/api/public/v1/courses/"
            f"{encode_identifier(course_identifier)}/users/"
            f"{encode_identifier(user_identifier)}"
        )

    def create(
        self,
        *,
        course_identifier,
        user_identifier,
        course_role_id="Student",
        availability=None,
        data_source_id=None,
        child_course_id=None,
    ) -> dict:
        """Create an enrollment using documented course and user identifiers."""
        body = {
            "courseRoleId": course_role_id,
            "availability": availability or {"available": "Yes"},
        }
        if data_source_id is not None:
            body["dataSourceId"] = data_source_id
        if child_course_id is not None:
            body["childCourseId"] = child_course_id
        return self.client._request_json(
            "PUT", self._path(course_identifier, user_identifier), json=body
        )

    def list_by_course(self, *, course_identifier: str) -> list[dict]:
        """List enrollments for a course."""
        return list(self.iter_by_course(course_identifier=course_identifier))

    def iter_by_course(self, *, course_identifier: str) -> Iterator[dict]:
        """Iterate over enrollments for a course."""
        course_identifier = validate_identifier(
            course_identifier, name="course_identifier",
            policy=COURSE_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/courses/{encode_identifier(course_identifier)}/users"
        return self.client._iter_paginated(path)

    def list_by_user(self, *, user_identifier: str) -> list[dict]:
        """List enrollments for a user."""
        return list(self.iter_by_user(user_identifier=user_identifier))

    def iter_by_user(self, *, user_identifier: str) -> Iterator[dict]:
        """Iterate over enrollments for a user."""
        user_identifier = validate_identifier(
            user_identifier, name="user_identifier",
            policy=USER_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/users/{encode_identifier(user_identifier)}/courses"
        return self.client._iter_paginated(path)

    def get(self, *, course_identifier: str, user_identifier: str) -> dict:
        """Get an enrollment for a course and user."""
        return self.client._request_json(
            "GET", self._path(course_identifier, user_identifier)
        )

    def update(
        self,
        *,
        course_identifier,
        user_identifier,
        course_role_id=None,
        availability=None,
        data_source_id=None,
        child_course_id=None,
    ) -> dict:
        """Update an enrollment for a course and user."""
        body = {}
        if course_role_id is not None:
            body["courseRoleId"] = course_role_id
        if availability is not None:
            body["availability"] = availability
        if data_source_id is not None:
            body["dataSourceId"] = data_source_id
        if child_course_id is not None:
            body["childCourseId"] = child_course_id
        if not body:
            raise ValueError("At least one field must be provided for update")
        return self.client._request_json(
            "PATCH", self._path(course_identifier, user_identifier), json=body
        )

    def set_available(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        """Make an enrollment available."""
        return self.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            availability={"available": "Yes"},
        )

    def set_unavailable(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        """Make an enrollment unavailable without disabling its record."""
        return self.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            availability={"available": "No"},
        )

    def set_disabled(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        """Disable an enrollment while preserving its data."""
        return self.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            availability={"available": "Disabled"},
        )

    def delete(self, *, course_identifier: str, user_identifier: str) -> None:
        """Delete an enrollment for a course and user."""
        self.client._request(
            "DELETE", self._path(course_identifier, user_identifier)
        )
