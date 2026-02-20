"""FastAPI migration scaffold entrypoint.

This scaffold is intentionally minimal and does not replace the stdlib API.
"""

from fastapi import FastAPI

app = FastAPI(title="Transfer Pathway Planner (Migration Scaffold)")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "mode": "scaffold"}
