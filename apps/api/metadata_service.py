"""Runtime-backed metadata extraction for API endpoints."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from apps.api.runtime_data_loader import RuntimeDataError, load_runtime_data
from packages.shared_types.v1 import sort_metadata_items


_NON_ALNUM = re.compile(r"[^a-z0-9_]+")
_REPEATED_UNDERSCORE = re.compile(r"_+")


class MetadataServiceError(RuntimeError):
    """Raised when runtime-backed metadata cannot be loaded."""


@dataclass(frozen=True)
class RuntimeMetadata:
    colleges: list[dict[str, str]]
    districts: list[dict[str, str]]
    ucs: list[dict[str, str]]
    manifest: dict[str, Any]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime_dir() -> Path:
    configured = os.environ.get("TPP_RUNTIME_DIR")
    if configured and configured.strip():
        return Path(configured.strip())
    return _project_root() / "data" / "runtime"


def _normalize_id(value: str) -> str:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    lowered = _NON_ALNUM.sub("_", lowered)
    lowered = _REPEATED_UNDERSCORE.sub("_", lowered).strip("_")
    return lowered


def _strip_suffixes(value: str, suffixes: tuple[str, ...]) -> str:
    out = value
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if out.endswith(suffix):
                out = out[: -len(suffix)]
                changed = True
    return out.rstrip("_")


def _college_entry_from_filtered_filename(filename: str) -> dict[str, str] | None:
    suffix = "_filtered.csv"
    if not filename.endswith(suffix):
        return None
    stem = filename[: -len(suffix)]
    display_name = stem.replace("_", " ")
    normalized = _normalize_id(stem)
    college_id = _strip_suffixes(normalized, ("_community_college", "_college"))
    if not college_id:
        college_id = normalized
    return {"id": college_id, "name": display_name}


def _district_entry_from_filename(filename: str) -> dict[str, str] | None:
    if not filename.endswith(".csv"):
        return None
    stem = filename[: -len(".csv")]
    display_name = stem.replace("_", " ")
    normalized = _normalize_id(stem)
    district_id = _strip_suffixes(
        normalized,
        (
            "_joint_community_college_district",
            "_community_college_district",
            "_district",
        ),
    )
    if not district_id:
        district_id = normalized
    return {"id": district_id, "name": display_name}


@lru_cache(maxsize=1)
def load_runtime_metadata() -> RuntimeMetadata:
    runtime_dir = _runtime_dir()
    try:
        loaded = load_runtime_data(runtime_dir)
    except RuntimeDataError as exc:
        raise MetadataServiceError(str(exc)) from exc

    source_files = loaded.model.manifest.get("source_files", {})
    filtered_sources = source_files.get("filtered_results", [])
    district_sources = source_files.get("district_csvs", [])

    colleges_unsorted = []
    for source in filtered_sources:
        entry = _college_entry_from_filtered_filename(str(source))
        if entry is not None:
            colleges_unsorted.append(entry)

    districts_unsorted = []
    for source in district_sources:
        entry = _district_entry_from_filename(str(source))
        if entry is not None:
            districts_unsorted.append(entry)

    uc_codes = {
        row.uc_name
        for row in loaded.model.filtered_rows + loaded.model.district_rows
        if row.uc_name
    }
    ucs_unsorted = [{"id": uc, "name": uc} for uc in uc_codes]

    return RuntimeMetadata(
        colleges=sort_metadata_items(colleges_unsorted),
        districts=sort_metadata_items(districts_unsorted),
        ucs=sort_metadata_items(ucs_unsorted),
        manifest=loaded.model.manifest,
    )


def _build_static_fallback_metadata() -> RuntimeMetadata:
    project_root = _project_root()
    filtered_dir = project_root / "filtered_results"
    district_dir = project_root / "district_csvs"

    colleges_unsorted: list[dict[str, str]] = []
    if filtered_dir.exists():
        for path in sorted(filtered_dir.glob("*_filtered.csv")):
            entry = _college_entry_from_filtered_filename(path.name)
            if entry is not None:
                colleges_unsorted.append(entry)

    districts_unsorted: list[dict[str, str]] = []
    if district_dir.exists():
        for path in sorted(district_dir.glob("*.csv")):
            entry = _district_entry_from_filename(path.name)
            if entry is not None:
                districts_unsorted.append(entry)

    manifest = {
        "version": "",
        "generated_at": "",
        "row_counts": {},
        "safe_mode": True,
    }
    return RuntimeMetadata(
        colleges=sort_metadata_items(colleges_unsorted),
        districts=sort_metadata_items(districts_unsorted),
        ucs=[],
        manifest=manifest,
    )


def load_runtime_metadata_with_safe_mode() -> tuple[RuntimeMetadata, bool, str | None]:
    try:
        return load_runtime_metadata(), False, None
    except Exception as exc:
        return _build_static_fallback_metadata(), True, str(exc)


def clear_metadata_cache() -> None:
    load_runtime_metadata.cache_clear()
