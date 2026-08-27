"""Enrollment-specific converters."""

from collections.abc import Iterable

from .common import flatten_dict, iterable_to_rows


def enrollment_to_row(enrollment: dict) -> dict:
    """Convert an enrollment into a flattened row."""
    return flatten_dict(enrollment)


def enrollments_to_rows(enrollments: Iterable[dict]) -> list[dict]:
    """Convert enrollments into rows while preserving input order."""
    return iterable_to_rows(enrollments, enrollment_to_row)
