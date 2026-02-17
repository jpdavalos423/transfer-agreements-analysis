# tests/golden

Golden-truth scenarios, fixtures, expected outputs, and comparator harness.

## Comparison Rules
Semantic comparison is used (not raw JSON byte equality):
1. Warning ordering is ignored (`code` + `message` compared after sorting).
2. `meta.target_ucs` ordering is ignored (sorted unique values).
3. Plan term ordering is ignored (terms compared by normalized term key).
4. Course ordering within each term is ignored (sorted by `courseCode`, `units`).
5. After canonicalization, all compared fields must match logically.

## Run
```bash
scripts/golden --suite phase_a
scripts/golden --suite full
scripts/golden --suite full --repeat 5
```

## Unittest Targets
```bash
python3 -m unittest tests/golden/test_phase_a_scenarios.py
python3 -m unittest tests/golden/test_full_suite_scenarios.py
python3 -m unittest tests/golden/test_golden_runner.py
python3 -m unittest tests/golden/test_legacy_pathway_units_golden.py
```

## Bootstrap New Scenario
Create request JSON (example `tmp/request.json`):
```json
{
  "college_id": "de_anza",
  "target_ucs": ["UCLA", "UCSD"],
  "ge_pattern": "IGETC",
  "completed_courses": ["MATH 1A"]
}
```

Generate scenario + expected:
```bash
scripts/bootstrap_golden_scenario \
  --id de_anza_ucla_ucsd_igetc \
  --request-file tmp/request.json \
  --description "De Anza with UCLA+UCSD under IGETC"
```

This writes:
1. `tests/golden/scenarios/de_anza_ucla_ucsd_igetc.json`
2. `tests/golden/expected/de_anza_ucla_ucsd_igetc_expected.json`
