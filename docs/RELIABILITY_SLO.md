# Reliability SLI/SLO

## SLI Definition

SLI: `valid_request_success_rate`

For a measurement window:

1. `valid_request_count`: requests that target a known endpoint and contain valid request payloads for that endpoint.
2. `valid_success_count`: valid requests that return a success status (`2xx` or `3xx`).
3. `valid_request_success_rate = valid_success_count / valid_request_count`.

Instrumentation source:

1. In-memory API collector at `/v1/metrics`.
2. Includes:
   - total request/success/error counts
   - `error_count_by_code`
   - route-level counters and valid-request SLI counters

## MVP SLO

SLO: `valid_request_success_rate >= 0.99` for `POST /v1/pathways/generate` during reliability runs.

## Reliability Check Command

Run deterministic reliability check using golden request sets:

```bash
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
```

Optional full suite:

```bash
scripts/reliability_check --suite full --repeat 1 --threshold 0.99
```

Behavior:

1. Starts API server on an ephemeral local port.
2. Replays selected golden scenarios as valid requests.
3. Reads `/v1/metrics`.
4. Evaluates SLO on route `POST /v1/pathways/generate`.
5. Exits non-zero when below threshold.

## Alerting Path (Current + Next)

Current:

1. Run `scripts/reliability_check` in CI.
2. Any non-zero exit fails the pipeline and triggers standard repository notifications.

Next (recommended):

1. Ship metrics snapshots to centralized telemetry (Datadog, Prometheus, or CloudWatch).
2. Configure alert:
   - condition: `valid_request_success_rate < 0.99` over rolling window
   - route filter: `POST /v1/pathways/generate`
3. Notify on-call channel and attach latest `error_count_by_code` breakdown.
