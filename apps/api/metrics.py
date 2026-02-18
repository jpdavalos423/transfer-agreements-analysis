"""Lightweight in-memory API metrics for reliability SLI/SLO checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from packages.shared_types.v1 import API_VERSION


@dataclass
class _CounterBucket:
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    valid_request_count: int = 0
    valid_success_count: int = 0
    valid_error_count: int = 0
    error_count_by_code: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        status_code: int,
        error_code: str | None,
        valid_request: bool | None,
    ) -> None:
        self.request_count += 1
        is_success = 200 <= status_code < 400
        if is_success:
            self.success_count += 1
        else:
            self.error_count += 1
            code = str(error_code or f"HTTP_{status_code}")
            self.error_count_by_code[code] = self.error_count_by_code.get(code, 0) + 1

        if valid_request is True:
            self.valid_request_count += 1
            if is_success:
                self.valid_success_count += 1
            else:
                self.valid_error_count += 1

    def to_dict(self) -> dict[str, Any]:
        rate = (
            float(self.valid_success_count) / float(self.valid_request_count)
            if self.valid_request_count > 0
            else None
        )
        return {
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_count_by_code": {
                key: self.error_count_by_code[key]
                for key in sorted(self.error_count_by_code)
            },
            "valid_request_count": self.valid_request_count,
            "valid_success_count": self.valid_success_count,
            "valid_error_count": self.valid_error_count,
            "valid_success_rate": rate,
        }


class APIMetrics:
    """Thread-safe API metrics collector."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._total = _CounterBucket()
        self._by_route: dict[tuple[str, str], _CounterBucket] = {}

    def record(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        error_code: str | None = None,
        valid_request: bool | None = None,
    ) -> None:
        method_norm = str(method or "").upper()
        path_norm = str(path or "")
        with self._lock:
            self._total.record(
                status_code=status_code,
                error_code=error_code,
                valid_request=valid_request,
            )
            key = (method_norm, path_norm)
            bucket = self._by_route.setdefault(key, _CounterBucket())
            bucket.record(
                status_code=status_code,
                error_code=error_code,
                valid_request=valid_request,
            )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            routes = []
            for (method, path), bucket in sorted(
                self._by_route.items(),
                key=lambda item: (item[0][0], item[0][1]),
            ):
                route_metrics = bucket.to_dict()
                route_metrics["method"] = method
                route_metrics["path"] = path
                routes.append(route_metrics)

            return {
                "version": API_VERSION,
                "sli": "valid_request_success_rate",
                "totals": self._total.to_dict(),
                "by_route": routes,
            }

