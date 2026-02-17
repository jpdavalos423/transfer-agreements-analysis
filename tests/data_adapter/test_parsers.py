from __future__ import annotations

import unittest
from pathlib import Path

from packages.data_adapter import DataParseError, Severity
from packages.data_adapter.parsers import (
    parse_district_csv_file,
    parse_filtered_csv_file,
    parse_filtered_results_dir,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "data_adapter"


class DataAdapterParserTests(unittest.TestCase):
    def test_valid_filtered_csv_parses_cleanly(self):
        result = parse_filtered_csv_file(FIXTURES / "filtered_valid.csv")
        self.assertEqual(len(result.rows), 2)
        severities = {diag.severity for diag in result.diagnostics}
        self.assertNotIn(Severity.ERROR, severities)
        self.assertNotIn(Severity.WARN, severities)

    def test_valid_district_csv_parses_cleanly(self):
        result = parse_district_csv_file(FIXTURES / "district_valid.csv")
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.rows[0].mode, "district")
        self.assertIsNotNone(result.rows[0].college_name)

    def test_formatting_issue_produces_warn(self):
        result = parse_filtered_csv_file(FIXTURES / "filtered_warn.csv")
        warns = [d for d in result.diagnostics if d.severity == Severity.WARN]
        self.assertGreaterEqual(len(warns), 1)
        self.assertEqual(len(result.rows), 2)

    def test_missing_required_field_produces_error(self):
        with self.assertRaises(DataParseError) as ctx:
            parse_filtered_csv_file(FIXTURES / "filtered_missing_required_column.csv")

        errors = [d for d in ctx.exception.diagnostics if d.severity == Severity.ERROR]
        self.assertGreaterEqual(len(errors), 1)
        self.assertTrue(any("Receiving" in err.message for err in errors))

    def test_deterministic_ordering_across_repeated_runs(self):
        fixture_dir = FIXTURES / "deterministic"
        run_one = parse_filtered_results_dir(fixture_dir)
        run_two = parse_filtered_results_dir(fixture_dir)

        keys_one = [(row.source_file, row.row_number, row.uc_name, row.group_id) for row in run_one.rows]
        keys_two = [(row.source_file, row.row_number, row.uc_name, row.group_id) for row in run_two.rows]
        self.assertEqual(keys_one, keys_two)

        file_order = [Path(k[0]).name for k in keys_one]
        self.assertEqual(file_order, ["a_filtered.csv", "b_filtered.csv"])


if __name__ == "__main__":
    unittest.main()

