# syntax=docker/dockerfile:1.18
FROM python:3.14.7-slim-bookworm@sha256:23c59390fc717bf09f9336908199a0ae75d9c4264bf296123f94ad772fea3b52 AS build

WORKDIR /workspace
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.12.2
COPY apps/cloud/pyproject.toml apps/cloud/uv.lock apps/cloud/README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY apps/cloud/app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.14.7-slim-bookworm@sha256:23c59390fc717bf09f9336908199a0ae75d9c4264bf296123f94ad772fea3b52

ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="Lemoo Stage 1A API" \
      org.opencontainers.image.description="Simulator-only synthetic control plane; production unsupported" \
      org.opencontainers.image.source="https://github.com/keyboardgdy/lemoo-ai-teaching-platform" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN python -m pip uninstall --yes pip \
    && groupadd --system --gid 10001 lemoo \
    && useradd --system --uid 10001 --gid 10001 --no-create-home lemoo
COPY --from=build --chown=10001:10001 /workspace/.venv /workspace/.venv

ENV PATH="/workspace/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]
CMD ["uvicorn", "app.entrypoints.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
