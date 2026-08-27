"""Convert normalized rows to a DataFrame."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def rows_to_dataframe(rows: Iterable[dict]) -> pd.DataFrame:
    """Build a DataFrame without changing row order."""
    return pd.DataFrame(list(rows))
