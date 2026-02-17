from __future__ import annotations

import csv
import re
from pathlib import Path

from .diagnostics import DataParseError, Diagnostic, RowReference, Severity
from .models import AlternativeBlock, ArticulationRow, CourseToken, ParseResult

_COURSE_GROUP_PREFIX = "Courses Group "
_COURSE_TOKEN_RE = re.compile(r"^(?P<code>.+?)\s*\((?P<units>\d+(?:\.\d+)?)\)\s*$")

_FILTERED_REQUIRED_COLUMNS = {
    "UC Name",
    "Group ID",
    "Set ID",
    "Num Required",
    "Receiving",
    "Courses Group 1",
}
_DISTRICT_REQUIRED_COLUMNS = _FILTERED_REQUIRED_COLUMNS | {"College Name"}


def _group_columns(headers: list[str]) -> list[str]:
    cols = [h for h in headers if h.startswith(_COURSE_GROUP_PREFIX)]
    return sorted(cols, key=lambda h: int(h.replace(_COURSE_GROUP_PREFIX, "").strip()))


def _parse_num_required(value: str, diagnostics: list[Diagnostic], file_path: str, row_number: int) -> int:
    raw = (value or "").strip()
    if not raw:
        diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message="Num Required is missing.",
                row_ref=RowReference(file_path=file_path, row_number=row_number, column="Num Required"),
            )
        )
        return 0
    try:
        parsed = int(raw)
        if parsed <= 0:
            raise ValueError
        return parsed
    except ValueError:
        diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message=f"Num Required must be a positive integer, got '{raw}'.",
                row_ref=RowReference(file_path=file_path, row_number=row_number, column="Num Required"),
            )
        )
        return 0


def _parse_course_token(
    token: str,
    *,
    diagnostics: list[Diagnostic],
    file_path: str,
    row_number: int,
    column: str,
) -> CourseToken:
    raw = token.strip()
    # Minimal formatting warning rule for P1-3.
    if "  " in raw:
        diagnostics.append(
            Diagnostic(
                severity=Severity.WARN,
                message=f"Course token '{raw}' contains repeated spaces; normalized.",
                row_ref=RowReference(file_path=file_path, row_number=row_number, column=column),
            )
        )
        raw = re.sub(r"\s{2,}", " ", raw)

    match = _COURSE_TOKEN_RE.match(raw)
    if match:
        return CourseToken(course_code=match.group("code").strip(), units=float(match.group("units")))

    diagnostics.append(
        Diagnostic(
            severity=Severity.WARN,
            message=f"Course token '{raw}' missing '(units)' format; units set to null.",
            row_ref=RowReference(file_path=file_path, row_number=row_number, column=column),
        )
    )
    return CourseToken(course_code=raw, units=None)


def _parse_row(
    row: dict[str, str],
    *,
    mode: str,
    required_columns: set[str],
    group_columns: list[str],
    file_path: str,
    row_number: int,
    diagnostics: list[Diagnostic],
) -> ArticulationRow | None:
    for column in required_columns:
        if column not in row:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    message=f"Missing required field '{column}' in row.",
                    row_ref=RowReference(file_path=file_path, row_number=row_number, column=column),
                )
            )
            return None

    uc_name = (row.get("UC Name") or "").strip()
    group_id = (row.get("Group ID") or "").strip()
    set_id = (row.get("Set ID") or "").strip()
    receiving_raw = (row.get("Receiving") or "").strip()
    college_name = (row.get("College Name") or "").strip() if mode == "district" else None

    for column, value in (("UC Name", uc_name), ("Group ID", group_id), ("Set ID", set_id), ("Receiving", receiving_raw)):
        if not value:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    message=f"Required field '{column}' cannot be empty.",
                    row_ref=RowReference(file_path=file_path, row_number=row_number, column=column),
                )
            )
    if mode == "district" and not college_name:
        diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message="Required field 'College Name' cannot be empty.",
                row_ref=RowReference(file_path=file_path, row_number=row_number, column="College Name"),
            )
        )

    num_required = _parse_num_required(row.get("Num Required", ""), diagnostics, file_path, row_number)
    receiving_courses = tuple(part.strip() for part in receiving_raw.split(";") if part.strip())

    alternatives: list[AlternativeBlock] = []
    articulation_status = "ARTICULATED"
    for idx, column in enumerate(group_columns, start=1):
        cell = (row.get(column) or "").strip()
        if not cell:
            continue
        if cell == "Not Articulated":
            articulation_status = "NOT_ARTICULATED"
            continue

        raw_tokens = [part.strip() for part in cell.split(";") if part.strip()]
        courses = tuple(
            _parse_course_token(
                raw_token,
                diagnostics=diagnostics,
                file_path=file_path,
                row_number=row_number,
                column=column,
            )
            for raw_token in raw_tokens
        )
        alternatives.append(AlternativeBlock(block_index=idx, courses=courses))

    if articulation_status == "ARTICULATED" and not alternatives:
        diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message="No course alternatives found and row is not marked 'Not Articulated'.",
                row_ref=RowReference(file_path=file_path, row_number=row_number, column="Courses Group 1"),
            )
        )

    return ArticulationRow(
        source_file=file_path,
        row_number=row_number,
        mode=mode,
        college_name=college_name or None,
        uc_name=uc_name,
        group_id=group_id,
        set_id=set_id,
        num_required=num_required,
        receiving_raw=receiving_raw,
        receiving_courses=receiving_courses,
        articulation_status=articulation_status,
        alternatives=tuple(alternatives),
    )


def _parse_file(path: Path, *, mode: str, required_columns: set[str]) -> ParseResult:
    diagnostics: list[Diagnostic] = []
    rows: list[ArticulationRow] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        missing_columns = sorted(required_columns - set(headers))
        if missing_columns:
            for col in missing_columns:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        message=f"Missing required column '{col}'.",
                        row_ref=RowReference(file_path=str(path), column=col),
                    )
                )
            raise DataParseError(diagnostics)

        group_cols = _group_columns(headers)
        for row_num, row in enumerate(reader, start=2):
            parsed = _parse_row(
                row,
                mode=mode,
                required_columns=required_columns,
                group_columns=group_cols,
                file_path=str(path),
                row_number=row_num,
                diagnostics=diagnostics,
            )
            if parsed is not None:
                rows.append(parsed)

    if any(diag.severity == Severity.ERROR for diag in diagnostics):
        raise DataParseError(diagnostics)

    rows_sorted = sorted(
        rows,
        key=lambda r: (r.source_file, r.row_number, r.uc_name, r.group_id, r.set_id, r.receiving_raw),
    )
    diagnostics_sorted = sorted(
        diagnostics,
        key=lambda d: (d.severity.value, d.row_ref.file_path, d.row_ref.row_number or 0, d.row_ref.column or "", d.message),
    )
    return ParseResult(rows=tuple(rows_sorted), diagnostics=tuple(diagnostics_sorted))


def _parse_dir(path: Path, *, mode: str, required_columns: set[str]) -> ParseResult:
    all_rows: list[ArticulationRow] = []
    all_diags: list[Diagnostic] = []

    for csv_path in sorted(path.glob("*.csv"), key=lambda p: p.name):
        result = _parse_file(csv_path, mode=mode, required_columns=required_columns)
        all_rows.extend(result.rows)
        all_diags.extend(result.diagnostics)
        all_diags.append(
            Diagnostic(
                severity=Severity.INFO,
                message=f"Parsed {len(result.rows)} rows from '{csv_path.name}'.",
                row_ref=RowReference(file_path=str(csv_path)),
            )
        )

    rows_sorted = sorted(
        all_rows,
        key=lambda r: (Path(r.source_file).name, r.row_number, r.uc_name, r.group_id, r.set_id, r.receiving_raw),
    )
    diags_sorted = sorted(
        all_diags,
        key=lambda d: (d.severity.value, d.row_ref.file_path, d.row_ref.row_number or 0, d.row_ref.column or "", d.message),
    )
    return ParseResult(rows=tuple(rows_sorted), diagnostics=tuple(diags_sorted))


def parse_filtered_csv_file(path: str | Path) -> ParseResult:
    return _parse_file(Path(path), mode="filtered", required_columns=_FILTERED_REQUIRED_COLUMNS)


def parse_district_csv_file(path: str | Path) -> ParseResult:
    return _parse_file(Path(path), mode="district", required_columns=_DISTRICT_REQUIRED_COLUMNS)


def parse_filtered_results_dir(path: str | Path) -> ParseResult:
    return _parse_dir(Path(path), mode="filtered", required_columns=_FILTERED_REQUIRED_COLUMNS)


def parse_district_csvs_dir(path: str | Path) -> ParseResult:
    return _parse_dir(Path(path), mode="district", required_columns=_DISTRICT_REQUIRED_COLUMNS)

