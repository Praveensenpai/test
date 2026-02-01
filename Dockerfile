FROM python:3.12-slim-bookworm

# ADDED "xauth" here to fix the xvfb-run error
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy 

COPY pyproject.toml uv.lock ./

# Install Python deps
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Camoufox fetch
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run python -m camoufox fetch

# Playwright install (handles system libraries like GTK, ALSA, etc.)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/ms-playwright \
    uv run playwright install --with-deps firefox

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Run with xvfb-run
CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x960x24", "uv", "run", "python", "main.py"]