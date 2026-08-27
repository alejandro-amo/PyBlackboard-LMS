"""Node and association-specific converters."""

from collections.abc import Iterable

from .common import flatten_dict, iterable_to_rows


def node_to_row(node: dict) -> dict:
    """Convert a node into a flattened row."""
    return flatten_dict(node)


def nodes_to_rows(nodes: Iterable[dict]) -> list[dict]:
    """Convert nodes into rows while preserving input order."""
    return iterable_to_rows(nodes, node_to_row)


def node_course_association_to_row(association: dict) -> dict:
    """Convert a node-course association into a row."""
    return flatten_dict(association)


def node_user_association_to_row(association: dict) -> dict:
    """Convert a node-user association into a row."""
    return flatten_dict(association)
