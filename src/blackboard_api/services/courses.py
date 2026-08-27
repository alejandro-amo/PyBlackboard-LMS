"""Composite operations related to courses."""

from __future__ import annotations

from typing import Any


class CourseService:
    """Coordinate courses and terms when the API requires several requests."""

    def __init__(self, courses_resource: Any, terms_resource: Any) -> None:
        self.courses = courses_resource
        self.terms = terms_resource

    def assign_term(self, *, course_identifier: str, term_identifier: str) -> dict:
        """Associate a course with a term using the term primary ID."""
        term = self.terms.get(term_identifier=term_identifier)
        term_id = term.get("id") if isinstance(term, dict) else None
        if not term_id:
            raise ValueError("Term response does not contain its primary ID")
        return self.courses.update(
            course_identifier=course_identifier,
            data={"termId": term_id},
        )

    def unassign_term(self, *, course_identifier: str) -> dict:
        """Remove a course term using a PATCH with a null ``termId``."""
        return self.courses.update(
            course_identifier=course_identifier,
            data={"termId": None},
        )

    def list_by_term(self, *, term_identifier: str) -> list[dict]:
        """List courses assigned to a term identified by a supported term ID."""
        term = self.terms.get(term_identifier=term_identifier)
        term_id = term.get("id") if isinstance(term, dict) else None
        if not term_id:
            raise ValueError("Term response does not contain its primary ID")
        return self.courses._list_by_term_primary_id(term_id=term_id)

    def get_copy_history(self, *, course_identifier: str) -> list[dict] | None:
        """Return the copy history reported for a course."""
        course = self.courses.get(course_identifier=course_identifier)
        return course.get("copyHistory")


class TermService:
    """Retrieve terms from the relationship stored on a course."""

    def __init__(self, courses_resource: Any, terms_resource: Any) -> None:
        self.courses = courses_resource
        self.terms = terms_resource

    def get_by_course(self, *, course_identifier: str) -> dict | None:
        """Return the course term, or ``None`` when no term is assigned."""
        course = self.courses.get(course_identifier=course_identifier)
        term_id = course.get("termId") if isinstance(course, dict) else None
        if not term_id:
            return None
        return self.terms.get(term_identifier=term_id)
