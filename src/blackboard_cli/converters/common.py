"""Utilities for converting JSON objects into rows."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested dictionaries using periods as separators."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        column = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(flatten_dict(value, column))
        elif isinstance(value, list) and all(not isinstance(item, dict) for item in value):
            result[column] = ";".join(str(item) for item in value)
        else:
            result[column] = value
    return result


def iterable_to_rows(items: Iterable[dict], converter) -> list[dict]:
    """Convert an iterable of objects while preserving input order."""
    return [converter(item) for item in items]
