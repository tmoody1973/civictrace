# CivicTrace service image (Slice 5.3, MOO-709). One image, two services:
#   api:    CIVICTRACE_APP=app.main:app    (CIVICTRACE_CLOUD=1, bearer gate)
#   worker: CIVICTRACE_APP=app.worker:app  (CIVICTRACE_WORKER=1, IAM-only)
# Build from the REPO ROOT so the reviewed fixture corpus and source manifests ship too:
#   docker build -f backend/Dockerfile .

FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
COPY backend/tests/fixtures ./tests/fixtures
COPY docs/sources /app/docs/sources

RUN useradd --create-home civictrace && chown -R civictrace /app
USER civictrace

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn ${CIVICTRACE_APP:-app.main:app} --host 0.0.0.0 --port ${PORT:-8080}"]
