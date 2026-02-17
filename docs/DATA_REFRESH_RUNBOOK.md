# Data Refresh Runbook

Version: v0.1  
Owner: Data Refresh Owner (see Ownership section)

## 1. Purpose
This runbook defines how to refresh runtime data artifacts used by the Transfer Pathway Planner.

Runtime artifacts are built from source-of-truth CSV inputs:
1. `filtered_results/`
2. `district_csvs/`

Artifacts are generated into:
1. `data/runtime/`

Golden tests and CI must pass before merge.

## 2. Refresh Cadence
Recommended cadence:
1. Quarterly baseline refresh.
2. Additional refresh per articulation update cycle from upstream data source.

Manual refresh triggers:
1. New or corrected files added to `filtered_results/`.
2. New or corrected files added to `district_csvs/`.
3. Parser/normalization logic changes in `packages/data_adapter/`.
4. Golden suite update approved for expected semantic drift.

## 3. Pre-Refresh Checklist
1. Pull latest `main`.
2. Confirm working tree is clean.
3. Create a branch for refresh.
4. Confirm source CSV updates are present and reviewed.

Example:
```bash
cd /Users/jpdavalos/Documents/transfer-pathways-website/transfer-agreements-analysis
git checkout main
git pull
git checkout -b codex/data-refresh-YYYYMMDD
```

## 4. Refresh Process (Step-by-Step)
### Step 1: Update source CSV inputs
1. Apply new data to `filtered_results/` and/or `district_csvs/`.
2. Review file-level changes.

Example:
```bash
git status
```

### Step 2: Rebuild runtime artifacts
Run the runtime builder script:
```bash
scripts/build_runtime_dataset
```

Custom paths (optional):
```bash
scripts/build_runtime_dataset \
  --filtered-results-dir filtered_results \
  --district-csvs-dir district_csvs \
  --output-dir data/runtime
```

Expected outputs:
1. `data/runtime/filtered_rows.json`
2. `data/runtime/district_rows.json`
3. `data/runtime/filtered_diagnostics.json`
4. `data/runtime/district_diagnostics.json`
5. `data/runtime/manifest.json`

### Step 3: Validate manifest and checksums
Inspect manifest summary:
```bash
cat data/runtime/manifest.json
```

Verify required fields exist:
1. `version`
2. `generated_at`
3. `row_counts`
4. `checksums`
5. `source_files`

### Step 4: Run tests
Run data adapter tests:
```bash
python3 -m unittest discover -s tests/data_adapter -p 'test_*.py'
```

Run API/web regression smoke:
```bash
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
```

Run CI-equivalent quick checks:
```bash
python3 -m compileall -q apps packages tests
```

### Step 5: Golden validation
Run golden suite (when available in repo) and verify no unreviewed drift.

If golden fixtures need updates, follow Section 5 before merging.

### Step 6: Open PR
PR must include:
1. Source data changes summary.
2. Manifest diff summary (`version`, `row_counts`, changed source file list).
3. Test results.
4. Golden outcome (pass/no-change or reviewed update rationale).

## 5. Golden Update Workflow
When golden scenarios should change:
1. Intended behavior change in planner semantics.
2. Intended policy/data interpretation change.
3. Upstream data correction that changes expected outputs.

When golden scenarios should NOT change:
1. Test flakiness or nondeterministic ordering bug.
2. Accidental parser regression.
3. Unreviewed unexpected drift.

Review process before accepting drift:
1. Author documents why drift is expected.
2. Data Refresh Owner verifies source-data cause vs code bug.
3. Planner Approver reviews sample scenario diffs.
4. Update golden fixtures only after explicit approval in PR discussion.

## 6. Failure Handling
### Parser ERROR
Symptoms:
1. `scripts/build_runtime_dataset` exits non-zero.
2. Error diagnostics reference missing/invalid required fields.

Action:
1. Fix source CSV issues or parser bug.
2. Re-run build script.
3. Do not merge partial runtime artifacts.

### Golden mismatch
Symptoms:
1. Golden tests fail after refresh.

Action:
1. Determine if mismatch is intended.
2. If unintended: fix parser/data issue and re-run.
3. If intended: follow Golden Update Workflow and document rationale.

### Unexpected manifest change
Symptoms:
1. `version`/`checksums` changed without expected source changes.

Action:
1. Confirm source file set and parser code diff.
2. Re-run build twice and compare output for determinism.
3. If artifacts differ across runs, treat as determinism bug and block merge.

Determinism check example:
```bash
scripts/build_runtime_dataset --output-dir /tmp/runtime_a
scripts/build_runtime_dataset --output-dir /tmp/runtime_b
diff -r /tmp/runtime_a /tmp/runtime_b
```

## 7. Ownership
Data Refresh Owner responsibilities:
1. Execute refresh process.
2. Validate manifest and test outcomes.
3. Prepare PR with operational summary.

Review Approver responsibilities:
1. Approve source data changes and runtime artifact changes.
2. Approve any golden fixture updates.
3. Block merge for unresolved parser errors, unexplained manifest drift, or unapproved golden drift.

Recommended role mapping:
1. Data Refresh Owner: engineer or analyst responsible for articulation data updates.
2. Review Approver: tech lead/product owner for planner semantics and release quality.

## 8. Quick Command Reference
Build runtime artifacts:
```bash
scripts/build_runtime_dataset
```

Data adapter tests:
```bash
python3 -m unittest discover -s tests/data_adapter -p 'test_*.py'
```

API/web smoke:
```bash
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
```

CI-style syntax check:
```bash
python3 -m compileall -q apps packages tests
```
