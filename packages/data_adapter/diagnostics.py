from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass(frozen=True)
class RowReference:
    file_path: str
    row_number: int | None = None
    column: str | None = None


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    message: str
    row_ref: RowReference


class DataParseError(Exception):
    """Raised when parse diagnostics include one or more ERROR entries."""

    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        errors = [d for d in self.diagnostics if d.severity == Severity.ERROR]
        if not errors:
            return "Data parse failed."
        first = errors[0]
        row = f":{first.row_ref.row_number}" if first.row_ref.row_number is not None else ""
        col = f" ({first.row_ref.column})" if first.row_ref.column else ""
        return f"Data parse failed with {len(errors)} error(s). First: {first.row_ref.file_path}{row}{col}: {first.message}"

