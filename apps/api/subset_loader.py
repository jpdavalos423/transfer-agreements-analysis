"""Temporary subset loader for P0-3 from source-of-truth CSV inputs."""

from __future__ import annotations

import csv
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


def _read_uc_names_from_csv(path: Path) -> set[str]:
    uc_names: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            uc = (row.get("UC Name") or "").strip()
            if uc:
                uc_names.add(uc)
    return uc_names


def _scan_district_csvs(district_dir: Path) -> set[str]:
    """Collect subset UCs found in district CSVs for the selected colleges."""
    uc_names: set[str] = set()
    tracked_college_names = {"De Anza College", "Lassen Community College"}

    for csv_file in sorted(district_dir.glob("*.csv")):
        with csv_file.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if "College Name" not in (reader.fieldnames or []):
                continue
            for row in reader:
                college = (row.get("College Name") or "").strip()
                uc = (row.get("UC Name") or "").strip()
                if college in tracked_college_names and uc:
                    uc_names.add(uc)
    return uc_names


@lru_cache(maxsize=1)
def load_subset_metadata() -> SubsetMetadata:
    root = _project_root()
    filtered_dir = root / "filtered_results"
    district_dir = root / "district_csvs"

    if not filtered_dir.exists():
        raise FileNotFoundError(f"Missing filtered_results directory: {filtered_dir}")
    if not district_dir.exists():
        raise FileNotFoundError(f"Missing district_csvs directory: {district_dir}")

    ucs_from_filtered: set[str] = set()
    for college_id, file_name in SUBSET_COLLEGE_FILES.items():
        csv_path = filtered_dir / file_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing subset CSV for {college_id}: {csv_path}")
        ucs_from_filtered |= _read_uc_names_from_csv(csv_path)

    ucs_from_district = _scan_district_csvs(district_dir)
    loaded_ucs = (ucs_from_filtered | ucs_from_district) & SUBSET_UCS
    if loaded_ucs != SUBSET_UCS:
        missing = sorted(SUBSET_UCS - loaded_ucs)
        raise ValueError(f"Subset UC coverage incomplete in source CSVs: missing {missing}")

    return SubsetMetadata(
        colleges=sorted(SUBSET_COLLEGE_FILES.keys()),
        target_ucs=sorted(SUBSET_UCS),
        ge_patterns=GE_PATTERNS[:],
        sources={
            "filtered_results": str(filtered_dir),
            "district_csvs": str(district_dir),
        },
    )

