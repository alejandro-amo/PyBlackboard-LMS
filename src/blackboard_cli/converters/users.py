"""User-specific converters."""

from collections.abc import Iterable

from .common import flatten_dict, iterable_to_rows


def user_to_row(user: dict) -> dict:
    """Convert a user into a flattened row."""
    return flatten_dict(user)


def users_to_rows(users: Iterable[dict]) -> list[dict]:
    """Convert users into rows while preserving input order."""
    return iterable_to_rows(users, user_to_row)
