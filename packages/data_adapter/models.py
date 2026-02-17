from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import Diagnostic


@dataclass(frozen=True)
class CourseToken:
    course_code: str
    units: float | None


@dataclass(frozen=True)
class AlternativeBlock:
    block_index: int
    courses: tuple[CourseToken, ...]


@dataclass(frozen=True)
class ArticulationRow:
    source_file: str
    row_number: int
    mode: str  # filtered | district
    college_name: str | None
    uc_name: str
    group_id: str
    set_id: str
    num_required: int
    receiving_raw: str
    receiving_courses: tuple[str, ...]
    articulation_status: str  # ARTICULATED | NOT_ARTICULATED
    alternatives: tuple[AlternativeBlock, ...]


@dataclass(frozen=True)
class ParseResult:
    rows: tuple[ArticulationRow, ...]
    diagnostics: tuple[Diagnostic, ...]

