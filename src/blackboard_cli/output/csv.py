"""CSV output."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from pathlib import Path
import sys
from typing import TextIO

from .dataframe import rows_to_dataframe

LOGGER = logging.getLogger(__name__)


def rows_to_csv(
    rows: Iterable[dict],
    destination: str | Path | TextIO | None,
    *,
    encoding: str = "utf-8",
) -> None:
    """Write rows as CSV to a path, text stream, or standard output."""
    dataframe = rows_to_dataframe(rows)
    LOGGER.debug(
        "Preparing CSV: %d rows, %d columns",
        len(dataframe),
        len(dataframe.columns),
    )
    if destination is None:
        dataframe.to_csv(sys.stdout, index=False)
        return
    if hasattr(destination, "write"):
        dataframe.to_csv(destination, index=False)
        return
    dataframe.to_csv(destination, index=False, encoding=encoding)
