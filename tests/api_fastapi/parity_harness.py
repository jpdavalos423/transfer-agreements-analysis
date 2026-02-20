from __future__ import annotations

import difflib
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.api.server import create_server as create_stdlib_server
from tests.golden.runner import GoldenScenario, load_scenarios

# Allowed dynamic fields that are intentionally ignored for parity.
# request_id/trace_id are generated per request and can differ across stacks.
_VOLATILE_FIELDS = {"request_id", "trace_id"}


@dataclass(frozen=True)
class ParitySummary:
    suite: str
    scenario_count: int
    compared_calls: int
    metadata_paths: tuple[str, ...]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_json(url: str, timeout_seconds: float = 20.0) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if payload is not None else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return int(response.status), json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return int(exc.code), json.loads(exc.read().decode("utf-8"))


def _normalize(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key in sorted(payload.keys()):
            if key in _VOLATILE_FIELDS:
                continue
            out[key] = _normalize(payload[key])
        return out
    if isinstance(payload, list):
        return [_normalize(item) for item in payload]
    return payload


def _compare_recursive(left: Any, right: Any, path: str, diffs: list[str]) -> None:
    if type(left) is not type(right):
        diffs.append(
            f"{path}: type mismatch ({type(left).__name__} != {type(right).__name__})"
        )
        return

    if isinstance(left, dict):
        left_keys = set(left.keys())
        right_keys = set(right.keys())
        missing = sorted(left_keys - right_keys)
        extra = sorted(right_keys - left_keys)
        if missing:
            diffs.append(f"{path}: missing keys on right: {missing}")
        if extra:
            diffs.append(f"{path}: extra keys on right: {extra}")
        for key in sorted(left_keys & right_keys):
            _compare_recursive(left[key], right[key], f"{path}.{key}", diffs)
        return

    if isinstance(left, list):
        if len(left) != len(right):
            diffs.append(f"{path}: list length mismatch ({len(left)} != {len(right)})")
            return
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            _compare_recursive(left_item, right_item, f"{path}[{index}]", diffs)
        return

    if left != right:
        diffs.append(f"{path}: value mismatch ({left!r} != {right!r})")


def semantic_parity_compare(stdlib_payload: dict[str, Any], fastapi_payload: dict[str, Any]) -> tuple[bool, str]:
    left = _normalize(stdlib_payload)
    right = _normalize(fastapi_payload)

    diffs: list[str] = []
    _compare_recursive(left, right, "$", diffs)
    if not diffs:
        return True, ""

    left_text = json.dumps(left, sort_keys=True, indent=2).splitlines()
    right_text = json.dumps(right, sort_keys=True, indent=2).splitlines()
    unified = "\n".join(
        difflib.unified_diff(
            left_text,
            right_text,
            fromfile="stdlib",
            tofile="fastapi",
            lineterm="",
        )
    )

    details = "\n".join(diffs[:20])
    if len(diffs) > 20:
        details += f"\n... ({len(diffs) - 20} more differences)"

    return False, f"Semantic diffs:\n{details}\n\nUnified diff:\n{unified}"


def run_parity_gate(
    *,
    suite: str,
    scenarios_dir: str | Path,
    metadata_paths: tuple[str, ...] = (
        "/v1/health",
        "/v1/metadata/colleges",
        "/v1/metadata/districts",
        "/v1/metadata/ucs",
    ),
) -> ParitySummary:
    scenarios = load_scenarios(scenarios_dir, suite=suite)
    if not scenarios:
        raise AssertionError(f"No scenarios found for suite '{suite}'.")

    stdlib_server = create_stdlib_server(host="127.0.0.1", port=0)
    stdlib_port = int(stdlib_server.server_address[1])
    stdlib_base = f"http://127.0.0.1:{stdlib_port}"
    stdlib_thread = threading.Thread(target=stdlib_server.serve_forever, daemon=True)
    stdlib_thread.start()

    fastapi_port = _find_free_port()
    fastapi_base = f"http://127.0.0.1:{fastapi_port}"
    fastapi_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "apps.backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(fastapi_port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    compared_calls = 0
    try:
        _wait_json(f"{fastapi_base}/v1/health", timeout_seconds=25.0)

        for path in metadata_paths:
            std_status, std_payload = _request_json(stdlib_base, "GET", path)
            fast_status, fast_payload = _request_json(fastapi_base, "GET", path)
            compared_calls += 1

            if std_status != fast_status:
                raise AssertionError(
                    f"Metadata status mismatch for {path}: stdlib={std_status}, fastapi={fast_status}"
                )

            ok, diff = semantic_parity_compare(std_payload, fast_payload)
            if not ok:
                raise AssertionError(
                    f"Metadata parity mismatch for {path}.\n{diff}"
                )

        for scenario in scenarios:
            std_status, std_payload = _request_json(
                stdlib_base,
                "POST",
                "/v1/pathways/generate",
                scenario.request,
            )
            fast_status, fast_payload = _request_json(
                fastapi_base,
                "POST",
                "/v1/pathways/generate",
                scenario.request,
            )
            compared_calls += 1

            if std_status != fast_status:
                raise AssertionError(
                    "Status mismatch for scenario "
                    f"'{scenario.scenario_id}': stdlib={std_status}, fastapi={fast_status}"
                )

            ok, diff = semantic_parity_compare(std_payload, fast_payload)
            if not ok:
                raise AssertionError(
                    f"Scenario parity mismatch for '{scenario.scenario_id}'.\n"
                    f"Description: {scenario.description}\n{diff}"
                )

        return ParitySummary(
            suite=suite,
            scenario_count=len(scenarios),
            compared_calls=compared_calls,
            metadata_paths=metadata_paths,
        )
    finally:
        stdlib_server.shutdown()
        stdlib_server.server_close()
        stdlib_thread.join(timeout=2)

        fastapi_proc.terminate()
        try:
            fastapi_proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            fastapi_proc.kill()
            fastapi_proc.wait(timeout=3)
