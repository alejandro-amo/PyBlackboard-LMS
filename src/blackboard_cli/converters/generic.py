"""Generic converters for responses without a specialized format."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import logging
from typing import Any

from .common import flatten_dict, iterable_to_rows

LOGGER = logging.getLogger(__name__)


def object_to_row(
    data: dict[str, Any], *, excluded_fields: Sequence[str] = ()
) -> dict[str, Any]:
    """Convert a JSON object into a flattened row."""
    if not isinstance(data, dict):
        raise TypeError("Object must be a dictionary")
    included_data = {
        key: value for key, value in data.items() if key not in excluded_fields
    }
    return flatten_dict(included_data)


def objects_to_rows(
    items: Iterable[dict[str, Any]], *, excluded_fields: Sequence[str] = ()
) -> list[dict[str, Any]]:
    """Convert JSON objects into flattened rows."""
    rows = [
        object_to_row(item, excluded_fields=excluded_fields) for item in items
    ]
    LOGGER.debug("Converted %d JSON objects to rows", len(rows))
    return rows
