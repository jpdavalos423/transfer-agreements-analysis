# apps/web

Frontend web app for student pathway input, results, and warnings.

## Run locally

From repo root:

```bash
python3 -m apps.api.server
```

In a second terminal:

```bash
python3 -m apps.web.server
```

Then open:

```text
http://127.0.0.1:5173
```

Optional environment variable:

1. `TPP_WEB_API_BASE_URL` (default: `http://127.0.0.1:8000`)

Example:

```bash
TPP_WEB_API_BASE_URL=http://127.0.0.1:9000 python3 -m apps.web.server
```

## Web Logic Tests

```bash
node --test tests/web/test_planner_form_logic.mjs
node --test tests/web/test_results_view_logic.mjs
node --test tests/web/test_status_panel_logic.mjs
```

## Accessibility + Mobile Baseline

Automated baseline check:

```bash
python3 -m unittest tests/web/test_accessibility_baseline.py
```

Manual QA checklist:

1. Keyboard only:
   - Press `Tab` from top of page and confirm the skip link appears.
   - Confirm focus ring is visible on all form controls and submit button.
2. Labels and field guidance:
   - Confirm each input has a visible label (`College`, `Target UCs`, `GE Pattern`, `Completed Courses`).
   - Confirm `Target UCs` help text is announced via `aria-describedby`.
3. Error/status announcements:
   - Trigger a validation error and verify the `Form Validation` panel updates.
   - Trigger an API error and verify the `Request Error` panel updates.
4. Mobile viewport (<= 640px):
   - Confirm `Plan Status` and `Pathway Results` stack vertically.
   - Confirm no horizontal page scrolling.
   - Confirm controls remain readable and tappable.

Quick run-all web checks:

```bash
node --test tests/web/test_planner_form_logic.mjs tests/web/test_results_view_logic.mjs tests/web/test_status_panel_logic.mjs
python3 -m unittest tests/web/test_accessibility_baseline.py
```
