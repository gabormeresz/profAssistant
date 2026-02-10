# ============================================================================
# Backend Dockerfile — FastAPI + uv
# ============================================================================
# Multi-stage build:
#   1. "builder" — installs dependencies with uv (no dev deps)
#   2. "runtime" — slim image that copies the venv and runs uvicorn
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Install dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install uv (fast Python package manager)
# Pin uv to a specific version for reproducible builds.
# Bump manually when upgrading: https://github.com/astral-sh/uv/releases
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment (no dev deps)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application source
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# Stage 2 — Runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Make sure the virtualenv's bin is on the PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATA_DIR=/app/data

# Create a directory for persistent data (SQLite DBs, ChromaDB) and set ownership
RUN mkdir -p /app/data && chown -R app:app /app/data

EXPOSE 8000

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
