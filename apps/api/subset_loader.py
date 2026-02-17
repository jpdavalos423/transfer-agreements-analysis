"""Subset loader backed by normalized runtime artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class SubsetMetadata:
    colleges: list[str]
    target_ucs: list[str]
    ge_patterns: list[str]
    sources: dict[str, str]


SUBSET_COLLEGE_FILES = {
    "de_anza": "De_Anza_College_filtered.csv",
    "lassen": "Lassen_Community_College_filtered.csv",
}
SUBSET_UCS = {"UCLA", "UCSD", "UCM"}
GE_PATTERNS = ["IGETC", "7CoursePattern"]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_subset_metadata() -> SubsetMetadata:
    root = _project_root()
    runtime_dir = root / "data" / "runtime"
    manifest_path = runtime_dir / "manifest.json"

    sources = {
        "runtime_dir": str(runtime_dir),
        "manifest": str(manifest_path),
    }

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        filtered_sources = set((manifest.get("source_files", {}) or {}).get("filtered_results", []))
        missing_subset_sources = sorted(set(SUBSET_COLLEGE_FILES.values()) - filtered_sources)
        if missing_subset_sources:
            raise ValueError(
                "Runtime manifest missing subset filtered source files: "
                + ", ".join(missing_subset_sources)
            )
        # Keep static subset policy, but expose source list in metadata.
        sources["filtered_results_count"] = str(len(filtered_sources))
        sources["district_csvs_count"] = str(
            len((manifest.get("source_files", {}) or {}).get("district_csvs", []))
        )

    return SubsetMetadata(
        colleges=sorted(SUBSET_COLLEGE_FILES.keys()),
        target_ucs=sorted(SUBSET_UCS),
        ge_patterns=GE_PATTERNS[:],
        sources=sources,
    )
