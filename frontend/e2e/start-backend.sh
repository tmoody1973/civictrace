#!/usr/bin/env bash
# Replays the reviewed TID 121 corpus (fake agent runner, no cloud) and serves it for the e2e run.
set -euo pipefail
cd "$(dirname "$0")/../../backend"
LEDGER="${CIVICTRACE_E2E_LEDGER:-/tmp/civictrace-e2e-ledger.json}"
uv run python scripts/replay_corpus.py ../docs/sources/corpus-manifest.yaml --replay-duplicate --out "$LEDGER" \
  --vault-dir "${CIVICTRACE_E2E_VAULT:-/tmp/civictrace-e2e-vault}"
exec env CIVICTRACE_LEDGER_JSON="$LEDGER" uv run uvicorn app.main:app --port "${CIVICTRACE_E2E_API_PORT:-8000}" --log-level warning
