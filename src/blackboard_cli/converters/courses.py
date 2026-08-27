"""Course-specific converters."""

from collections.abc import Iterable

from .common import flatten_dict, iterable_to_rows


def course_to_row(course: dict) -> dict:
    """Convert a course into a row while preserving nested fields."""
    return flatten_dict(course)


def courses_to_rows(courses: Iterable[dict]) -> list[dict]:
    """Convert courses into rows while preserving input order."""
    return iterable_to_rows(courses, course_to_row)
