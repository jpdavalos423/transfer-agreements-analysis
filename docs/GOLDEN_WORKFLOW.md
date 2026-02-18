# Golden Update Workflow

Goldens are a contract. They should only change when behavior changes are intentional and reviewed.

## 1) When Goldens Should Change

Update goldens when:
1. Product behavior changed intentionally and was approved.
2. Request/response contract changed intentionally.
3. Scenario coverage needs to expand (new valid scenario IDs/inputs).

Do **not** update goldens when:
1. A regression appears and expected behavior should stay the same.
2. Output order is unstable or non-deterministic.
3. Behavior changed accidentally.

Rule of thumb:
1. If behavior is wrong: fix code.
2. If behavior is correct and intentionally changed: update golden with review.

## 2) Propose a Golden Update

Use candidate outputs first. Do not overwrite `tests/golden/expected` directly.

### Generate candidate output

Single scenario:
```bash
scripts/golden_update candidate --suite full --scenario-id full_17_lassen_ucsd_igetc
```

Suite:
```bash
scripts/golden_update candidate --suite phase_a
scripts/golden_update candidate --suite full
```

This writes candidate files to:
`tests/golden/_candidate/`

The command prints:
1. `UNCHANGED` / `CHANGED` / `NEW` status per scenario.
2. A diff summary against `tests/golden/expected/`.

### Promote candidates (explicit step)

Preview only (no file writes):
```bash
scripts/golden_update promote --suite full
```

Apply promotion:
```bash
scripts/golden_update promote --suite full --yes
```

Promote one scenario:
```bash
scripts/golden_update promote --suite full --scenario-id full_17_lassen_ucsd_igetc --yes
```

## 3) Review Checklist (Required)

Before approving golden updates:
1. Confirm linked code/product change that justifies each diff.
2. Confirm scenario input is valid for subset constraints.
3. Confirm no invented IDs/course codes.
4. Run deterministic check:
```bash
scripts/golden --suite full --repeat 5
```
5. Confirm no unrelated scenario drift in the same PR.
6. Confirm CI golden gate passes.

## 4) Non-Determinism Policy

Non-determinism must be fixed in code/comparator, not accepted via golden updates.

If repeated runs differ:
1. Stop promotion.
2. Identify unstable ordering/randomness/time-dependent behavior.
3. Add deterministic sort/canonicalization or fix logic.
4. Re-run:
```bash
scripts/golden --suite full --repeat 5
```
5. Only then regenerate/promote candidates.

## 5) CI Policy for Golden File Changes

When files under `tests/golden/scenarios/` or `tests/golden/expected/` change, PRs must include one of:
1. `docs/GOLDEN_WORKFLOW.md` updated in the same PR, or
2. PR description marker: `[golden-update-approved]`, or
3. PR label: `golden-update-approved`

Without one of these, CI fails intentionally.
