"""Output adapters for tabular rows."""

from .dataframe import rows_to_dataframe
from .table import rows_to_table
from .csv import rows_to_csv
from .excel import rows_to_excel

__all__ = ["rows_to_dataframe", "rows_to_table", "rows_to_csv", "rows_to_excel"]
