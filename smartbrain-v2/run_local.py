"""LOCAL dev launcher for the SmartBrain UI + SSO flow (no nginx needed).

WHAT THIS IS
------------
On the VM, nginx sits in front of the app and does two things the app relies on:
  1. Strips the public ``/brain`` prefix before forwarding (the app runs with
     ``--root-path /brain`` so it re-adds the prefix in any URLs it builds).
  2. Terminates TLS, so the app is reached over https and the login session
     cookie (``https_only=True``) is accepted by the browser.

Locally there is no nginx, so without a shim:
  - ``/brain/...`` paths 404, and
  - the login cookie won't stick over plain http.

This launcher stands in for nginx locally. It:
  - mounts the REAL app (``api.app:app``) under ``/brain`` so
    ``http://localhost:8000/brain/...`` resolves exactly like production and
    matches the registered Azure redirect URI
    ``http://localhost:8000/brain/auth/callback``; and
  - re-adds the session cookie with ``https_only=False`` so login persists
    over local http.

It changes NOTHING about the app's own code or behavior — same routes, same
auth, same scope gate. It is for local testing only and is excluded from the
deployment zip.

HOW TO RUN
----------
From this directory, with the venv:

    .venv/bin/python run_local.py

(or:  .venv/bin/uvicorn run_local:outer --host 0.0.0.0 --port 8000)

Then open:  http://localhost:8000/brain/chatbot/

Prereqs: Neo4j (emg2-neo4j) + Qdrant (emg2-qdrant) running locally
(`docker compose up -d neo4j qdrant`), and a populated .env in this folder.
"""

from __future__ import annotations

import os

# Load .env from this folder so AZURE_*, SESSION_SECRET, NEO4J_*, etc. are set
# the same way the production process gets them, before the app is imported.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:  # noqa: BLE001 - dotenv is optional; env may already be set
    pass

from fastapi import FastAPI  # noqa: E402
from starlette.middleware.sessions import SessionMiddleware  # noqa: E402

from api.app import app as inner_app  # noqa: E402
from config.settings import get_settings  # noqa: E402

# Relax the session cookie for local http so login actually persists. The
# production app keeps https_only=True; this only applies to this local run.
_secret = get_settings().session_secret or "local-dev-session-secret"
inner_app.add_middleware(
    SessionMiddleware,
    secret_key=_secret,
    https_only=False,
    same_site="lax",
)

# Mount the real app under /brain so public paths resolve like production.
outer = FastAPI(title="SmartBrain local dev shell")
outer.mount("/brain", inner_app)


@outer.get("/")
def _root_redirect():
    """Convenience: bare localhost:8000 -> the chatbot."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/brain/chatbot/")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("LOCAL_HOST", "0.0.0.0")
    port = int(os.environ.get("LOCAL_PORT", "8000"))
    print("\n  SmartBrain local dev server")
    print(f"  → open  http://localhost:{port}/brain/chatbot/\n")
    uvicorn.run(outer, host=host, port=port)
