# Product Metrics (MVP)

## Scope

Metrics are aggregated only and contain no PII.

Source: `GET /v1/metrics`

## Metric Definitions

1. `product.pathway_generation_requests_total`
   - Total `POST /v1/pathways/generate` requests observed.
2. `product.pathway_generation_valid_requests_total`
   - Generate requests that passed request validation.
3. `product.pathway_generation_success_total`
   - Valid generate requests that returned success (`2xx`/`3xx`).
4. `product.top_target_uc_sets`
   - Ranked counts of selected UC target combinations from valid requests.
   - Canonicalized by sorted unique UC codes.
5. `product.ge_pattern_usage`
   - Ranked counts of GE patterns from valid requests.
6. `product.warnings.responses_with_warnings`
   - Number of successful generate responses containing one or more warnings.
7. `product.warnings.warning_rate`
   - `responses_with_warnings / pathway_generation_success_total`.
8. `product.plan_shape.average_terms_generated`
   - Average term count per successful generate response.
9. `product.plan_shape.average_courses_per_term`
   - `total_courses_generated / total_terms_generated` across successful responses.
10. `product.latency_histogram_ms`
   - Histogram of successful generate latencies using buckets:
   - `le_50ms`, `le_100ms`, `le_250ms`, `le_500ms`, `le_1000ms`, `le_2000ms`, `gt_2000ms`.

## Determinism

`/v1/metrics` returns deterministic key ordering and sorted aggregate lists:

1. `top_target_uc_sets` sorted by count descending, then UC-set key.
2. `ge_pattern_usage` sorted by count descending, then GE pattern.
3. `latency_histogram_ms` returned in fixed bucket order.

## Local Validation

Run API integration metrics checks:

```bash
python3 -m unittest tests/api/test_generate_endpoint.py
```

Manual endpoint check:

```bash
curl -s http://127.0.0.1:8000/v1/metrics | jq
```
