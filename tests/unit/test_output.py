import csv
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from blackboard_cli.output import rows_to_csv, rows_to_excel, rows_to_table


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"id": "1", "name": "Ana"},
            {"id": "2", "name": "Luis"},
        ]

    def test_table_returns_text_without_printing(self):
        table = rows_to_table(self.rows)
        self.assertIn("id", table)
        self.assertIn("Ana", table)
        self.assertIn("Luis", table)

    def test_csv_writes_rows_to_text_stream(self):
        stream = StringIO()
        rows_to_csv(self.rows, stream)
        parsed = list(csv.DictReader(StringIO(stream.getvalue())))
        self.assertEqual(parsed[0]["name"], "Ana")
        self.assertEqual(parsed[1]["id"], "2")

    def test_csv_writes_rows_to_standard_output_when_destination_is_none(self):
        stream = StringIO()
        with patch("sys.stdout", stream):
            rows_to_csv(self.rows, None)
        parsed = list(csv.DictReader(StringIO(stream.getvalue())))
        self.assertEqual(parsed[0]["name"], "Ana")

    def test_excel_writes_a_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "courses.xlsx"
            rows_to_excel(self.rows, path, sheet_name="Courses")
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 0)

    def test_empty_rows_have_empty_table(self):
        self.assertEqual(rows_to_table([]), "")


if __name__ == "__main__":
    unittest.main()
