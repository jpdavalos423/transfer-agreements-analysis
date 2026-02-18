# Operations Runbook

## 1. Purpose

This runbook is for operational troubleshooting and rollback for the MVP API/web stack.

## 2. Common Issues

## 2.1 Runtime artifacts missing or invalid

Symptoms:

1. `GET /v1/health` returns `RUNTIME_METADATA_ERROR`
2. `POST /v1/pathways/generate` returns `PLANNER_RUNTIME_ERROR`
3. Logs mention missing manifest/artifact or checksum mismatch

Steps:

```bash
ls -la data/runtime
cat data/runtime/manifest.json
```

Rebuild runtime data:

```bash
scripts/build_runtime_dataset
```

Re-check health:

```bash
curl -s http://127.0.0.1:8000/v1/health
```

## 2.2 Golden failures

Symptoms:

1. `scripts/golden --suite phase_a|full` fails
2. CI golden gate fails

Steps:

1. Re-run deterministic harness locally:

```bash
scripts/golden --suite full
scripts/determinism --suite full --repeat 10
```

2. If mismatch persists, generate candidate outputs (do not auto-promote):

```bash
scripts/golden_update candidate --suite full
```

3. Follow approval workflow before promotion:

```bash
scripts/golden_update promote --suite full --yes
```

Reference: `docs/GOLDEN_WORKFLOW.md`

## 2.3 Performance regression

Symptoms:

1. Perf suite p95 exceeds threshold

Steps:

```bash
scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0
```

If failed:

1. Capture output and top slow scenarios.
2. Verify runtime dataset did not change unexpectedly:

```bash
cat data/runtime/manifest.json
```

3. Run determinism suite to rule out unstable output ordering:

```bash
scripts/determinism --suite phase_a --repeat 10
```

4. Open a targeted optimization ticket (do not silently change semantics).

## 2.4 Reliability regression

Symptoms:

1. SLO check fails (< 99% valid-request success rate)

Steps:

```bash
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
curl -s http://127.0.0.1:8000/v1/metrics
```

Inspect:

1. `totals.error_count_by_code`
2. `by_route` entry for `POST /v1/pathways/generate`

## 3. Rollback

## 3.1 Runtime-data rollback

Use this when code is fine but new runtime artifacts are bad.

1. Identify last known good commit:

```bash
git log --oneline -- data/runtime
```

2. Restore runtime folder from good commit:

```bash
git checkout <GOOD_COMMIT_SHA> -- data/runtime
```

3. Restart API and verify:

```bash
python3 -m apps.api.server
curl -s http://127.0.0.1:8000/v1/health
```

## 3.2 Application rollback

Use this when a code change regressed API/web behavior.

1. Revert offending commit(s):

```bash
git revert <BAD_COMMIT_SHA>
```

2. Run verification suite:

```bash
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
scripts/golden --suite phase_a
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
```

3. Deploy reverted branch/commit.

## 4. Incident Notes Template

Capture in PR/issue:

1. Impact window and affected endpoint(s)
2. Error code distribution from `/v1/metrics`
3. Runtime manifest version involved
4. Recovery action taken (rebuild/rollback/revert)
5. Follow-up ticket(s)

