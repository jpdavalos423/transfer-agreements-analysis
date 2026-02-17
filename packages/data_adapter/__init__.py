"""CSV parsing and in-memory normalization utilities for articulation data."""

from .diagnostics import DataParseError, Diagnostic, RowReference, Severity
from .models import AlternativeBlock, ArticulationRow, CourseToken, ParseResult
from .parsers import (
    parse_district_csv_file,
    parse_district_csvs_dir,
    parse_filtered_csv_file,
    parse_filtered_results_dir,
)

__all__ = [
    "AlternativeBlock",
    "ArticulationRow",
    "CourseToken",
    "DataParseError",
    "Diagnostic",
    "ParseResult",
    "RowReference",
    "Severity",
    "parse_district_csv_file",
    "parse_district_csvs_dir",
    "parse_filtered_csv_file",
    "parse_filtered_results_dir",
]

