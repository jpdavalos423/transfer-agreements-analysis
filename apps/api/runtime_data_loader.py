"""Runtime artifact loader/validator for normalized planner inputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.data_adapter.models import AlternativeBlock, ArticulationRow, CourseToken
from packages.planner_core import PlannerRuntimeModel


MANIFEST_FILE = "manifest.json"
FILTERED_ROWS_FILE = "filtered_rows.json"
DISTRICT_ROWS_FILE = "district_rows.json"
FILTERED_DIAGNOSTICS_FILE = "filtered_diagnostics.json"
DISTRICT_DIAGNOSTICS_FILE = "district_diagnostics.json"


class RuntimeDataError(ValueError):
    """Raised when runtime artifacts are missing or invalid."""


@dataclass(frozen=True)
class LoadedRuntimeData:
    model: PlannerRuntimeModel
    diagnostics: dict[str, Any]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_manifest_shape(manifest: dict[str, Any]) -> None:
    required = {"checksums", "generated_at", "row_counts", "source_files", "version"}
    missing = sorted(required - set(manifest.keys()))
    if missing:
        raise RuntimeDataError(f"Manifest missing required field(s): {missing}")

    checksums = manifest.get("checksums")
    if not isinstance(checksums, dict):
        raise RuntimeDataError("Manifest checksums must be an object.")
    for artifact in [
        FILTERED_ROWS_FILE,
        DISTRICT_ROWS_FILE,
        FILTERED_DIAGNOSTICS_FILE,
        DISTRICT_DIAGNOSTICS_FILE,
    ]:
        if artifact not in checksums:
            raise RuntimeDataError(f"Manifest checksums missing '{artifact}'.")

    row_counts = manifest.get("row_counts")
    if not isinstance(row_counts, dict):
        raise RuntimeDataError("Manifest row_counts must be an object.")
    for key in ["filtered_rows", "district_rows"]:
        if key not in row_counts:
            raise RuntimeDataError(f"Manifest row_counts missing '{key}'.")


def _to_articulation_row(raw: dict[str, Any]) -> ArticulationRow:
    alternatives = tuple(
        AlternativeBlock(
            block_index=int(alt.get("block_index") or 0),
            courses=tuple(
                CourseToken(
                    course_code=str(course.get("course_code") or ""),
                    units=(
                        float(course["units"])
                        if course.get("units") is not None
                        else None
                    ),
                )
                for course in alt.get("courses", [])
                if str(course.get("course_code") or "")
            ),
        )
        for alt in raw.get("alternatives", [])
    )

    return ArticulationRow(
        source_file=str(raw.get("source_file") or ""),
        row_number=int(raw.get("row_number") or 0),
        mode=str(raw.get("mode") or ""),
        college_name=(raw.get("college_name") if raw.get("college_name") is None else str(raw.get("college_name"))),
        uc_name=str(raw.get("uc_name") or ""),
        group_id=str(raw.get("group_id") or ""),
        set_id=str(raw.get("set_id") or ""),
        num_required=int(raw.get("num_required") or 0),
        receiving_raw=str(raw.get("receiving_raw") or ""),
        receiving_courses=tuple(str(x) for x in raw.get("receiving_courses", [])),
        articulation_status=str(raw.get("articulation_status") or ""),
        alternatives=alternatives,
    )


def _canonical_row_sort_key(row: ArticulationRow) -> tuple[Any, ...]:
    return (
        row.mode,
        row.source_file,
        row.row_number,
        row.uc_name,
        row.group_id,
        row.set_id,
        row.receiving_raw,
    )


def load_runtime_data(runtime_dir: str | Path) -> LoadedRuntimeData:
    root = Path(runtime_dir)
    manifest_path = root / MANIFEST_FILE
    if not manifest_path.exists():
        raise RuntimeDataError(f"Runtime manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeDataError("Runtime manifest must be a JSON object.")
    _require_manifest_shape(manifest)

    artifact_paths = {
        FILTERED_ROWS_FILE: root / FILTERED_ROWS_FILE,
        DISTRICT_ROWS_FILE: root / DISTRICT_ROWS_FILE,
        FILTERED_DIAGNOSTICS_FILE: root / FILTERED_DIAGNOSTICS_FILE,
        DISTRICT_DIAGNOSTICS_FILE: root / DISTRICT_DIAGNOSTICS_FILE,
    }
    for name, path in artifact_paths.items():
        if not path.exists():
            raise RuntimeDataError(f"Runtime artifact missing: {name}")

    checksums = manifest["checksums"]
    for name, path in artifact_paths.items():
        actual = _sha256_file(path)
        expected = checksums.get(name)
        if expected != actual:
            raise RuntimeDataError(
                f"Checksum mismatch for '{name}'. expected={expected} actual={actual}"
            )

    filtered_rows_raw = json.loads(artifact_paths[FILTERED_ROWS_FILE].read_text(encoding="utf-8"))
    district_rows_raw = json.loads(artifact_paths[DISTRICT_ROWS_FILE].read_text(encoding="utf-8"))
    if not isinstance(filtered_rows_raw, list) or not isinstance(district_rows_raw, list):
        raise RuntimeDataError("Runtime rows artifacts must be JSON arrays.")

    filtered_rows = tuple(sorted((_to_articulation_row(row) for row in filtered_rows_raw), key=_canonical_row_sort_key))
    district_rows = tuple(sorted((_to_articulation_row(row) for row in district_rows_raw), key=_canonical_row_sort_key))

    row_counts = manifest["row_counts"]
    if int(row_counts.get("filtered_rows", -1)) != len(filtered_rows):
        raise RuntimeDataError(
            f"Manifest filtered_rows count mismatch. manifest={row_counts.get('filtered_rows')} actual={len(filtered_rows)}"
        )
    if int(row_counts.get("district_rows", -1)) != len(district_rows):
        raise RuntimeDataError(
            f"Manifest district_rows count mismatch. manifest={row_counts.get('district_rows')} actual={len(district_rows)}"
        )

    model = PlannerRuntimeModel(
        filtered_rows=filtered_rows,
        district_rows=district_rows,
        manifest=manifest,
    )
    diagnostics = {
        "filtered_diagnostics": json.loads(artifact_paths[FILTERED_DIAGNOSTICS_FILE].read_text(encoding="utf-8")),
        "district_diagnostics": json.loads(artifact_paths[DISTRICT_DIAGNOSTICS_FILE].read_text(encoding="utf-8")),
    }
    return LoadedRuntimeData(model=model, diagnostics=diagnostics)

