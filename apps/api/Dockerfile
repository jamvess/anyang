# Build from the REPO ROOT so config/ and prompts/ are in the context:
#   docker build -f apps/api/Dockerfile -t anyang-api .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/srv/api/.venv/bin:$PATH" \
    CONFIG_DIR=/srv/config \
    PROMPTS_DIR=/srv/prompts \
    PORT=8080

WORKDIR /srv/api

# Dependencies first for layer caching.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY config/ /srv/config/
COPY prompts/ /srv/prompts/
COPY apps/api/app/ ./app/

RUN useradd --system --no-create-home appuser
USER appuser

# Cloud Run injects $PORT; shell form so it expands.
CMD exec fastapi run app/main.py --host 0.0.0.0 --port "$PORT"
