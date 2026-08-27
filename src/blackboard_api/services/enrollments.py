"""Composite operations related to enrollments."""

from __future__ import annotations

import logging
from typing import Any, Iterable

from ..errors import NotFoundError

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Coordinate resources to keep enrollments consistent."""

    def __init__(self, enrollments_resource: Any, roles_resource: Any) -> None:
        self.enrollments = enrollments_resource
        self.roles = roles_resource
        self._course_roles: dict[str, dict] | None = None

    def find(self, *, course_identifier: str, user_identifier: str) -> dict | None:
        """Return an enrollment, or ``None`` when Blackboard returns 404."""
        try:
            return self.enrollments.get(
                course_identifier=course_identifier,
                user_identifier=user_identifier,
            )
        except NotFoundError:
            return None

    def upsert(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        course_role_id: str = "Student",
        availability: dict | None = None,
        data_source_id: str | None = None,
        child_course_id: str | None = None,
    ) -> dict:
        """Create or update an enrollment to reach the desired state."""
        self.validate_course_role(course_role_id=course_role_id)
        desired = self._desired_fields(
            course_role_id=course_role_id,
            availability=availability,
            data_source_id=data_source_id,
            child_course_id=child_course_id,
        )
        current = self.find(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )
        if current is None:
            return self.enrollments.create(
                course_identifier=course_identifier,
                user_identifier=user_identifier,
                course_role_id=course_role_id,
                availability=availability,
                data_source_id=data_source_id,
                child_course_id=child_course_id,
            )
        changes = {
            key: value for key, value in desired.items()
            if current.get(key) != value
        }
        if not changes:
            return current
        return self.enrollments.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            **self._update_arguments(changes),
        )

    def ensure_enrolled(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        course_role_id: str = "Student",
        availability: dict | None = None,
    ) -> dict:
        """Ensure that an enrollment exists with the requested fields."""
        return self.upsert(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
            availability=availability,
        )

    def change_role(
        self, *, course_identifier: str, user_identifier: str,
        course_role_id: str,
    ) -> dict:
        """Change only the role of an existing enrollment."""
        return self.enrollments.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
        )

    def set_availability(
        self, *, course_identifier: str, user_identifier: str, available: str
    ) -> dict:
        """Set enrollment availability."""
        if available not in {"Yes", "No", "Disabled"}:
            raise ValueError("available must be 'Yes', 'No', or 'Disabled'")
        return self.enrollments.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            availability={"available": available},
        )

    def deactivate(self, *, course_identifier: str, user_identifier: str) -> dict:
        """Deactivate an enrollment without deleting it."""
        return self.set_availability(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            available="No",
        )

    def activate(self, *, course_identifier: str, user_identifier: str) -> dict:
        """Activate an existing enrollment."""
        return self.set_availability(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            available="Yes",
        )

    def delete_if_exists(
        self, *, course_identifier: str, user_identifier: str
    ) -> bool:
        """Delete an enrollment and return whether it existed."""
        if self.find(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        ) is None:
            return False
        self.enrollments.delete(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )
        return True

    def validate_course_role(self, *, course_role_id: str) -> dict:
        """Return an available role or fail when it does not exist."""
        if self._course_roles is None:
            self._course_roles = {
                role["id"]: role
                for role in self.roles.list()
                if isinstance(role, dict) and role.get("id")
            }
            logger.debug("Course-role cache loaded (%s roles)", len(self._course_roles))
        role = self._course_roles.get(course_role_id)
        if role is not None:
            return role
        raise ValueError(f"Unknown course role: {course_role_id}")

    def list_for_courses(
        self, *, course_identifiers: Iterable[str]
    ) -> list[dict]:
        """Combine enrollments from multiple courses."""
        result = []
        seen = set()
        for identifier in course_identifiers:
            if identifier in seen:
                continue
            seen.add(identifier)
            result.extend(
                self.enrollments.list_by_course(course_identifier=identifier)
            )
        return result

    def list_for_users(self, *, user_identifiers: Iterable[str]) -> list[dict]:
        """Combine enrollments from multiple users."""
        result = []
        seen = set()
        for identifier in user_identifiers:
            if identifier in seen:
                continue
            seen.add(identifier)
            result.extend(self.enrollments.list_by_user(user_identifier=identifier))
        return result

    def enroll_user_in_courses(
        self, *, user_identifier: str, course_identifiers: Iterable[str],
        course_role_id: str = "Student",
    ) -> list[dict]:
        """Ensure that the user is enrolled in each specified course."""
        return [
            self.upsert(
                course_identifier=course_identifier,
                user_identifier=user_identifier,
                course_role_id=course_role_id,
            )
            for course_identifier in course_identifiers
        ]

    def enroll_users_in_course(
        self, *, course_identifier: str, user_identifiers: Iterable[str],
        course_role_id: str = "Student",
    ) -> list[dict]:
        """Ensure that each specified user is enrolled in the course."""
        return [
            self.upsert(
                course_identifier=course_identifier,
                user_identifier=user_identifier,
                course_role_id=course_role_id,
            )
            for user_identifier in user_identifiers
        ]

    @staticmethod
    def _desired_fields(**kwargs: Any) -> dict:
        availability = kwargs["availability"] or {"available": "Yes"}
        if not isinstance(availability, dict) or availability.get("available") not in {
            "Yes", "No", "Disabled"
        }:
            raise ValueError(
                "availability must contain available='Yes', 'No', or 'Disabled'"
            )
        fields = {
            "courseRoleId": kwargs["course_role_id"],
            "availability": availability,
        }
        if kwargs["data_source_id"] is not None:
            fields["dataSourceId"] = kwargs["data_source_id"]
        if kwargs["child_course_id"] is not None:
            fields["childCourseId"] = kwargs["child_course_id"]
        return fields

    @staticmethod
    def _update_arguments(changes: dict) -> dict:
        names = {
            "courseRoleId": "course_role_id",
            "availability": "availability",
            "dataSourceId": "data_source_id",
            "childCourseId": "child_course_id",
        }
        return {names[key]: value for key, value in changes.items()}
