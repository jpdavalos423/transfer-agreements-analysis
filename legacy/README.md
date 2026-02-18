# legacy

Preserved legacy scripts and workflows kept for parity/regression checks.

- `legacy/pathway_generator/`: original pathway generation implementation (read-only baseline).
- `legacy/cc_agreements/`, `legacy/cs_urls/`, `legacy/results/`: original scraping pipeline artifacts.
- `legacy/creating_districts/`: original district CSV generation scripts.
- `legacy/question_1/`, `legacy/question_2-3/`, `legacy/question_4/`: research analysis scripts and outputs.
- Runtime API/planner flows should use `packages/planner_core` + `data/runtime` instead.
