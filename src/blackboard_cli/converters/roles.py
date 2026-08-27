"""Course-role-specific converters."""

from collections.abc import Iterable

from .common import flatten_dict, iterable_to_rows


def role_to_row(role: dict) -> dict:
    """Convert a role into a flattened row."""
    return flatten_dict(role)


def roles_to_rows(roles: Iterable[dict]) -> list[dict]:
    """Convert roles into rows while preserving input order."""
    return iterable_to_rows(roles, role_to_row)
