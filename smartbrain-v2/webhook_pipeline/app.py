"""Minimal FastAPI application for the Steering Webhook Pipeline.

Start with:
    uvicorn webhook_pipeline.app:app --host 0.0.0.0 --port 8002 --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from webhook_pipeline.router import router

app = FastAPI(title="SmartBrain Steering Webhook")
app.include_router(router)

__all__ = ["app"]
