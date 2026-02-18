from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any

from apps.api.planner_service import generate_pathway_response
from tests.golden.runner import load_scenarios


@dataclass(frozen=True)
class LatencySample:
    scenario_id: str
    run_index: int
    seconds: float


@dataclass(frozen=True)
class LatencySummary:
    suite: str
    threshold_seconds: float
    scenarios: tuple[str, ...]
    samples: tuple[LatencySample, ...]
    p50_seconds: float
    p95_seconds: float
    per_scenario_mean: dict[str, float]
    per_scenario_max: dict[str, float]

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def passes_threshold(self) -> bool:
        return self.p95_seconds <= self.threshold_seconds


def _nearest_rank_percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Cannot compute percentile of an empty list.")
    if percentile < 0 or percentile > 100:
        raise ValueError("percentile must be in [0, 100].")

    ordered = sorted(values)
    # Nearest-rank percentile: rank = ceil(p/100 * N), 1-indexed.
    rank = int((percentile / 100.0) * len(ordered))
    if (percentile / 100.0) * len(ordered) > rank:
        rank += 1
    rank = max(1, rank)
    return ordered[rank - 1]


def measure_latency(
    *,
    scenarios_dir: str | Path,
    suite: str = "phase_a",
    repeat: int = 3,
    warmup: int = 1,
    threshold_seconds: float = 2.0,
) -> LatencySummary:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    selected = load_scenarios(scenarios_dir, suite=suite)
    if not selected:
        raise ValueError(f"No scenarios selected for suite '{suite}'.")

    requests = [(scenario.scenario_id, dict(scenario.request)) for scenario in selected]

    for _ in range(warmup):
        for _, payload in requests:
            generate_pathway_response(payload)

    samples: list[LatencySample] = []
    per_scenario_values: dict[str, list[float]] = {scenario_id: [] for scenario_id, _ in requests}

    for run_index in range(1, repeat + 1):
        for scenario_id, payload in requests:
            start = perf_counter()
            generate_pathway_response(payload)
            elapsed = perf_counter() - start
            samples.append(
                LatencySample(
                    scenario_id=scenario_id,
                    run_index=run_index,
                    seconds=elapsed,
                )
            )
            per_scenario_values[scenario_id].append(elapsed)

    durations = [sample.seconds for sample in samples]
    per_scenario_mean = {sid: mean(vals) for sid, vals in per_scenario_values.items()}
    per_scenario_max = {sid: max(vals) for sid, vals in per_scenario_values.items()}

    return LatencySummary(
        suite=suite,
        threshold_seconds=threshold_seconds,
        scenarios=tuple(sid for sid, _ in requests),
        samples=tuple(samples),
        p50_seconds=_nearest_rank_percentile(durations, 50),
        p95_seconds=_nearest_rank_percentile(durations, 95),
        per_scenario_mean=per_scenario_mean,
        per_scenario_max=per_scenario_max,
    )


def format_summary(summary: LatencySummary) -> str:
    lines: list[str] = []
    lines.append(
        f"Perf suite={summary.suite} scenarios={len(summary.scenarios)} samples={summary.sample_count}"
    )
    lines.append(
        "p50={:.3f}s p95={:.3f}s threshold={:.3f}s status={}".format(
            summary.p50_seconds,
            summary.p95_seconds,
            summary.threshold_seconds,
            "PASS" if summary.passes_threshold else "FAIL",
        )
    )

    lines.append("Top slow scenarios by max latency:")
    ranked = sorted(
        summary.per_scenario_max.items(),
        key=lambda item: (-item[1], item[0]),
    )
    for scenario_id, max_value in ranked[:5]:
        lines.append(
            "  - {}: max={:.3f}s mean={:.3f}s".format(
                scenario_id,
                max_value,
                summary.per_scenario_mean[scenario_id],
            )
        )

    return "\n".join(lines)

