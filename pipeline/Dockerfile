FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install deps (frozen, no dev, no project install yet)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source
COPY . .

# NOTE: hermes CLI must be installed separately.
# On Fly.io, install via fly.toml [build.args] or a custom base image.
# For local development: pip install hermes-ai (or your hermes package name)
# Uncomment the line below once the hermes package name is confirmed:
# RUN pip install hermes-ai

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
