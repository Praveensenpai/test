FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy 

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv run python -m camoufox fetch

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/ms-playwright \
    uv run playwright install --with-deps firefox

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x960x24", "uv", "run", "python", "main.py"]