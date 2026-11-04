FROM mcr.microsoft.com/playwright:v1.53.0-noble
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

USER root
WORKDIR /app
ENV UV_LINK_MODE=copy UV_NO_DEV=1

RUN apt-get update && apt-get install -y --no-install-recommends xvfb tini \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install 3.12 && uv sync --frozen --no-dev --python 3.12
# Python and Node Playwright tags can bundle different Firefox revisions.
RUN uv run --frozen playwright install --with-deps firefox
COPY scripts/install_camoufox.py scripts/install_camoufox.py
RUN uv run --frozen python scripts/install_camoufox.py
COPY app/ app/
COPY LICENSE ./
