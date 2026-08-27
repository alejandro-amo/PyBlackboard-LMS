"""Excel output."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from pathlib import Path

from .dataframe import rows_to_dataframe

LOGGER = logging.getLogger(__name__)


def rows_to_excel(
    rows: Iterable[dict],
    destination: str | Path,
    *,
    sheet_name: str = "Sheet1",
) -> None:
    """Write rows to an Excel worksheet."""
    dataframe = rows_to_dataframe(rows)
    LOGGER.debug("Preparing Excel: %d rows, %d columns", len(dataframe), len(dataframe.columns))
    dataframe.to_excel(destination, index=False, sheet_name=sheet_name)
