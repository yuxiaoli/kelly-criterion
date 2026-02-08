FROM python:3.11-slim-bookworm

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Sync with locked dependencies
# --no-dev: Do not install dev dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY . .

# Entrypoint
ENTRYPOINT ["uv", "run", "kelly_criterion"]
