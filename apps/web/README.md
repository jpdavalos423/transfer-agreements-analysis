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

## Web Logic Tests

```bash
node --test tests/web/test_planner_form_logic.mjs
```
