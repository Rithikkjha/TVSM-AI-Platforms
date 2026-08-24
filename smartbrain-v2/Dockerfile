# syntax=docker/dockerfile:1.6
# ---------------------------------------------------------------------------
# Multi-stage Dockerfile for the engineering-memory-graph FastAPI service.
# - `base`    : shared Python runtime + system deps
# - `dev`     : editable install with [dev] extras, used by docker-compose
# - `builder` : wheel build stage for production
# - `prod`    : minimal runtime image
# ---------------------------------------------------------------------------

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Minimal system deps. build-essential kept out of `prod` via the builder stage.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Development image — editable install with dev extras, used by docker-compose.
# src/ is bind-mounted at runtime so hot-reload picks up local edits.
# ---------------------------------------------------------------------------
FROM base AS dev

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
# Copy a minimal package skeleton so `pip install -e` can resolve the project
# before the full source tree is bind-mounted by docker-compose.
COPY src ./src

RUN pip install --upgrade pip \
 && pip install -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "src.query.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Builder — builds a wheel in isolation so the prod image stays slim.
# ---------------------------------------------------------------------------
FROM base AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip build \
 && python -m build --wheel --outdir /dist

# ---------------------------------------------------------------------------
# Production image — installs only the built wheel + runtime deps.
# ---------------------------------------------------------------------------
FROM base AS prod

# Drop privileges.
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY --from=builder /dist /tmp/dist
RUN pip install --upgrade pip \
 && pip install /tmp/dist/*.whl \
 && rm -rf /tmp/dist

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.query.app:app", "--host", "0.0.0.0", "--port", "8000"]
