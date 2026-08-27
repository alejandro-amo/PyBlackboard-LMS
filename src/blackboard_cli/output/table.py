"""Human-readable terminal output."""

from __future__ import annotations

from collections.abc import Iterable

from .dataframe import rows_to_dataframe


def rows_to_table(rows: Iterable[dict]) -> str:
    """Return rows as tabular text without printing them."""
    dataframe = rows_to_dataframe(rows)
    if dataframe.empty and len(dataframe.columns) == 0:
        return ""
    return dataframe.to_string(index=False)
