from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .diagnostics import DataParseError, Diagnostic, Severity
from .models import ArticulationRow, ParseResult
from .parsers import parse_district_csvs_dir, parse_filtered_results_dir

FILTERED_ROWS_FILE = "filtered_rows.json"
DISTRICT_ROWS_FILE = "district_rows.json"
FILTERED_DIAGNOSTICS_FILE = "filtered_diagnostics.json"
DISTRICT_DIAGNOSTICS_FILE = "district_diagnostics.json"
MANIFEST_FILE = "manifest.json"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _write_json(path: Path, payload: Any) -> None:
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False, default=_json_default)
    path.write_text(text + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _serialize_row(row: ArticulationRow) -> dict[str, Any]:
    return {
        "source_file": row.source_file,
        "row_number": row.row_number,
        "mode": row.mode,
        "college_name": row.college_name,
        "uc_name": row.uc_name,
        "group_id": row.group_id,
        "set_id": row.set_id,
        "num_required": row.num_required,
        "receiving_raw": row.receiving_raw,
        "receiving_courses": list(row.receiving_courses),
        "articulation_status": row.articulation_status,
        "alternatives": [
            {
                "block_index": block.block_index,
                "courses": [
                    {"course_code": course.course_code, "units": course.units}
                    for course in block.courses
                ],
            }
            for block in row.alternatives
        ],
    }


def _serialize_diagnostic(diag: Diagnostic) -> dict[str, Any]:
    return {
        "severity": diag.severity.value,
        "message": diag.message,
        "row_ref": asdict(diag.row_ref),
    }


def _source_file_list(directory: Path) -> list[str]:
    return [p.name for p in sorted(directory.glob("*.csv"), key=lambda p: p.name)]


def _generated_at(filtered_dir: Path, district_dir: Path) -> str:
    files = list(filtered_dir.glob("*.csv")) + list(district_dir.glob("*.csv"))
    if not files:
        return "1970-01-01T00:00:00Z"
    max_mtime = max(p.stat().st_mtime for p in files)
    return datetime.fromtimestamp(max_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dataset_version(checksums: dict[str, str]) -> str:
    seed = "|".join(f"{name}:{value}" for name, value in sorted(checksums.items()))
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"v1-{digest}"


def _write_parse_artifacts(output_dir: Path, parse: ParseResult, *, rows_file: str, diagnostics_file: str) -> None:
    rows_payload = [_serialize_row(row) for row in parse.rows]
    diagnostics_payload = [_serialize_diagnostic(diag) for diag in parse.diagnostics]
    _write_json(output_dir / rows_file, rows_payload)
    _write_json(output_dir / diagnostics_file, diagnostics_payload)


def build_runtime_dataset(
    *,
    filtered_results_dir: str | Path,
    district_csvs_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    filtered_dir = Path(filtered_results_dir)
    district_dir = Path(district_csvs_dir)
    runtime_dir = Path(output_dir)

    filtered_parse = parse_filtered_results_dir(filtered_dir)
    district_parse = parse_district_csvs_dir(district_dir)

    runtime_dir.mkdir(parents=True, exist_ok=True)
    _write_parse_artifacts(
        runtime_dir,
        filtered_parse,
        rows_file=FILTERED_ROWS_FILE,
        diagnostics_file=FILTERED_DIAGNOSTICS_FILE,
    )
    _write_parse_artifacts(
        runtime_dir,
        district_parse,
        rows_file=DISTRICT_ROWS_FILE,
        diagnostics_file=DISTRICT_DIAGNOSTICS_FILE,
    )

    artifact_files = [
        FILTERED_ROWS_FILE,
        DISTRICT_ROWS_FILE,
        FILTERED_DIAGNOSTICS_FILE,
        DISTRICT_DIAGNOSTICS_FILE,
    ]
    checksums = {name: _sha256_file(runtime_dir / name) for name in artifact_files}

    manifest = {
        "checksums": checksums,
        "generated_at": _generated_at(filtered_dir, district_dir),
        "row_counts": {
            "filtered_rows": len(filtered_parse.rows),
            "district_rows": len(district_parse.rows),
            "filtered_diagnostics": len(filtered_parse.diagnostics),
            "district_diagnostics": len(district_parse.diagnostics),
        },
        "source_files": {
            "filtered_results": _source_file_list(filtered_dir),
            "district_csvs": _source_file_list(district_dir),
        },
    }
    manifest["version"] = _dataset_version(checksums)
    _write_json(runtime_dir / MANIFEST_FILE, manifest)
    return manifest


def load_runtime_dataset(runtime_dir: str | Path) -> dict[str, Any]:
    root = Path(runtime_dir)
    manifest = json.loads((root / MANIFEST_FILE).read_text(encoding="utf-8"))
    filtered_rows = json.loads((root / FILTERED_ROWS_FILE).read_text(encoding="utf-8"))
    district_rows = json.loads((root / DISTRICT_ROWS_FILE).read_text(encoding="utf-8"))
    return {
        "manifest": manifest,
        "filtered_rows": filtered_rows,
        "district_rows": district_rows,
    }


__all__ = [
    "DataParseError",
    "MANIFEST_FILE",
    "build_runtime_dataset",
    "load_runtime_dataset",
]

