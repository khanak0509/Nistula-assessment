"""
FastAPI entry point.

Kept thin on purpose — the actual work lives in services/ and models/ so we
can unit test pieces without standing up a server.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.routes.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Villa guest message handler", version="1.0.0")

app.include_router(webhook_router)


@app.get("/")
def health() -> dict[str, str]:
    """health check."""
    return {"status": "ok"}
