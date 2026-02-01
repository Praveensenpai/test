FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    xvfb \
    curl \
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    libxt6 \
    libpci3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy 

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

RUN uv run python -m camoufox fetch

RUN uv run playwright install --with-deps firefox

COPY . .

RUN uv sync --frozen

CMD ["uv", "run", "python", "main.py"]