"""Public facade combining enrollment resources and services."""

from __future__ import annotations

from typing import Any
from collections.abc import Iterable, Iterator

from .resources import ResourceFacade


class EnrollmentFacade(ResourceFacade):
    """Expose atomic and composite operations under ``client.enrollments``."""

    def __init__(self, resource: Any, service: Any) -> None:
        super().__init__(resource)
        self._service = service

    def list_by_course(self, *, course_identifier: str) -> list[dict]:
        return self._resource.list_by_course(
            course_identifier=course_identifier
        )

    def iter_by_course(self, *, course_identifier: str) -> Iterator[dict]:
        return self._resource.iter_by_course(
            course_identifier=course_identifier
        )

    def list_by_user(self, *, user_identifier: str) -> list[dict]:
        return self._resource.list_by_user(user_identifier=user_identifier)

    def iter_by_user(self, *, user_identifier: str) -> Iterator[dict]:
        return self._resource.iter_by_user(user_identifier=user_identifier)

    def get(self, *, course_identifier: str, user_identifier: str) -> dict:
        return self._resource.get(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def create(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        course_role_id: str = "Student",
        availability: dict | None = None,
        data_source_id: str | None = None,
        child_course_id: str | None = None,
    ) -> dict:
        return self._resource.create(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
            availability=availability,
            data_source_id=data_source_id,
            child_course_id=child_course_id,
        )

    def update(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        course_role_id: str | None = None,
        availability: dict | None = None,
        data_source_id: str | None = None,
        child_course_id: str | None = None,
    ) -> dict:
        return self._resource.update(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
            availability=availability,
            data_source_id=data_source_id,
            child_course_id=child_course_id,
        )

    def delete(self, *, course_identifier: str, user_identifier: str) -> None:
        return self._resource.delete(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def set_available(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        return self._resource.set_available(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def set_unavailable(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        return self._resource.set_unavailable(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def set_disabled(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict:
        return self._resource.set_disabled(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def find(
        self, *, course_identifier: str, user_identifier: str
    ) -> dict | None:
        return self._service.find(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

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
        """Create or update an enrollment to reach the requested state."""
        return self._service.upsert(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
            availability=availability,
            data_source_id=data_source_id,
            child_course_id=child_course_id,
        )

    def change_role(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        course_role_id: str,
    ) -> dict:
        """Change the role of an existing enrollment."""
        return self._service.change_role(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            course_role_id=course_role_id,
        )

    def set_availability(
        self,
        *,
        course_identifier: str,
        user_identifier: str,
        available: str,
    ) -> dict:
        """Set enrollment availability to ``Yes``, ``No``, or ``Disabled``."""
        return self._service.set_availability(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
            available=available,
        )

    def activate(self, *, course_identifier: str, user_identifier: str) -> dict:
        """Set an existing enrollment as available."""
        return self._service.activate(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def deactivate(self, *, course_identifier: str, user_identifier: str) -> dict:
        """Set an existing enrollment as unavailable."""
        return self._service.deactivate(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def delete_if_exists(
        self, *, course_identifier: str, user_identifier: str
    ) -> bool:
        """Delete an enrollment only when it exists."""
        return self._service.delete_if_exists(
            course_identifier=course_identifier,
            user_identifier=user_identifier,
        )

    def validate_course_role(self, *, course_role_id: str) -> dict:
        """Return a known course role or raise an error."""
        return self._service.validate_course_role(course_role_id=course_role_id)

    def list_for_courses(
        self, *, course_identifiers: Iterable[str]
    ) -> list[dict]:
        """Return enrollments for multiple courses in input order."""
        return self._service.list_for_courses(
            course_identifiers=course_identifiers
        )

    def list_for_users(
        self, *, user_identifiers: Iterable[str]
    ) -> list[dict]:
        """Return enrollments for multiple users in input order."""
        return self._service.list_for_users(user_identifiers=user_identifiers)

    def enroll_user_in_courses(
        self,
        *,
        user_identifier: str,
        course_identifiers: Iterable[str],
        course_role_id: str = "Student",
    ) -> list[dict]:
        """Ensure one user is enrolled in multiple courses."""
        return self._service.enroll_user_in_courses(
            user_identifier=user_identifier,
            course_identifiers=course_identifiers,
            course_role_id=course_role_id,
        )

    def enroll_users_in_course(
        self,
        *,
        course_identifier: str,
        user_identifiers: Iterable[str],
        course_role_id: str = "Student",
    ) -> list[dict]:
        """Ensure multiple users are enrolled in one course."""
        return self._service.enroll_users_in_course(
            course_identifier=course_identifier,
            user_identifiers=user_identifiers,
            course_role_id=course_role_id,
        )
