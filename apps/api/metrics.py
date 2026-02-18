"""Lightweight in-memory API metrics for reliability SLI/SLO checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from packages.shared_types.v1 import API_VERSION


GENERATE_ROUTE = ("POST", "/v1/pathways/generate")
_LATENCY_BUCKETS_MS = (50, 100, 250, 500, 1000, 2000)


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


@dataclass
class _ProductBucket:
    pathway_generation_requests_total: int = 0
    pathway_generation_valid_requests_total: int = 0
    pathway_generation_success_total: int = 0
    responses_with_warnings: int = 0
    total_terms_generated: int = 0
    total_courses_generated: int = 0
    uc_target_set_counts: dict[str, int] = field(default_factory=dict)
    ge_pattern_counts: dict[str, int] = field(default_factory=dict)
    latency_histogram_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in _latency_bucket_keys():
            self.latency_histogram_counts.setdefault(key, 0)

    def _record_target_set(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        raw = payload.get("target_ucs")
        if not isinstance(raw, list):
            return
        normalized = sorted(
            {
                str(item).strip()
                for item in raw
                if isinstance(item, str) and item.strip()
            }
        )
        if not normalized:
            return
        key = "|".join(normalized)
        self.uc_target_set_counts[key] = self.uc_target_set_counts.get(key, 0) + 1

    def _record_ge_pattern(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        ge_pattern = payload.get("ge_pattern")
        if not isinstance(ge_pattern, str):
            return
        ge_pattern = ge_pattern.strip()
        if not ge_pattern:
            return
        self.ge_pattern_counts[ge_pattern] = self.ge_pattern_counts.get(ge_pattern, 0) + 1

    def _record_latency(self, latency_ms: float | None) -> None:
        if latency_ms is None:
            return
        key = _latency_bucket_for_ms(latency_ms)
        self.latency_histogram_counts[key] = self.latency_histogram_counts.get(key, 0) + 1

    def _record_plan_shape(self, response_payload: Any) -> None:
        if not isinstance(response_payload, dict):
            return
        plan = response_payload.get("plan")
        if not isinstance(plan, list):
            return

        self.total_terms_generated += len(plan)
        for term in plan:
            if not isinstance(term, dict):
                continue
            courses = term.get("courses")
            if isinstance(courses, list):
                self.total_courses_generated += len(courses)

        warnings = response_payload.get("warnings")
        if isinstance(warnings, list) and len(warnings) > 0:
            self.responses_with_warnings += 1

    def record_generation(
        self,
        *,
        request_payload: Any,
        response_payload: Any,
        status_code: int,
        valid_request: bool | None,
        latency_ms: float | None,
    ) -> None:
        self.pathway_generation_requests_total += 1
        if valid_request is True:
            self.pathway_generation_valid_requests_total += 1
            self._record_target_set(request_payload)
            self._record_ge_pattern(request_payload)

        is_success = 200 <= int(status_code) < 400
        if valid_request is True and is_success:
            self.pathway_generation_success_total += 1
            self._record_plan_shape(response_payload)
            self._record_latency(latency_ms)

    def to_dict(self) -> dict[str, Any]:
        warning_rate = (
            float(self.responses_with_warnings) / float(self.pathway_generation_success_total)
            if self.pathway_generation_success_total > 0
            else None
        )
        average_terms_generated = (
            float(self.total_terms_generated) / float(self.pathway_generation_success_total)
            if self.pathway_generation_success_total > 0
            else None
        )
        average_courses_per_term = (
            float(self.total_courses_generated) / float(self.total_terms_generated)
            if self.total_terms_generated > 0
            else None
        )

        top_uc_sets = []
        for key, count in sorted(
            self.uc_target_set_counts.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            targets = [item for item in key.split("|") if item]
            top_uc_sets.append(
                {
                    "uc_targets": targets,
                    "count": count,
                }
            )

        ge_patterns = [
            {"ge_pattern": key, "count": count}
            for key, count in sorted(
                self.ge_pattern_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

        latency_histogram = [
            {"bucket": key, "count": self.latency_histogram_counts.get(key, 0)}
            for key in _latency_bucket_keys()
        ]

        return {
            "pathway_generation_requests_total": self.pathway_generation_requests_total,
            "pathway_generation_valid_requests_total": self.pathway_generation_valid_requests_total,
            "pathway_generation_success_total": self.pathway_generation_success_total,
            "top_target_uc_sets": top_uc_sets,
            "ge_pattern_usage": ge_patterns,
            "warnings": {
                "responses_with_warnings": self.responses_with_warnings,
                "warning_rate": warning_rate,
            },
            "plan_shape": {
                "average_terms_generated": average_terms_generated,
                "average_courses_per_term": average_courses_per_term,
            },
            "latency_histogram_ms": latency_histogram,
        }


def _latency_bucket_keys() -> list[str]:
    keys = [f"le_{value}ms" for value in _LATENCY_BUCKETS_MS]
    keys.append(f"gt_{_LATENCY_BUCKETS_MS[-1]}ms")
    return keys


def _latency_bucket_for_ms(latency_ms: float) -> str:
    for threshold in _LATENCY_BUCKETS_MS:
        if latency_ms <= float(threshold):
            return f"le_{threshold}ms"
    return f"gt_{_LATENCY_BUCKETS_MS[-1]}ms"


class APIMetrics:
    """Thread-safe API metrics collector."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._total = _CounterBucket()
        self._by_route: dict[tuple[str, str], _CounterBucket] = {}
        self._product = _ProductBucket()

    def record(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        error_code: str | None = None,
        valid_request: bool | None = None,
        request_payload: Any = None,
        response_payload: Any = None,
        latency_ms: float | None = None,
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
            if (method_norm, path_norm) == GENERATE_ROUTE:
                self._product.record_generation(
                    request_payload=request_payload,
                    response_payload=response_payload,
                    status_code=status_code,
                    valid_request=valid_request,
                    latency_ms=latency_ms,
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
                "product": self._product.to_dict(),
            }
