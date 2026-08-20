#!/usr/bin/env bash
# Live local session for the e2e run: replays the reviewed TID 121 corpus in-process
# (fake agent runner, no cloud) and enables the Slice 4 approval/packet write endpoints.
set -euo pipefail
cd "$(dirname "$0")/../../backend"
exec env CIVICTRACE_LIVE=1 uv run uvicorn app.main:app --port "${CIVICTRACE_E2E_API_PORT:-8000}" --log-level warning
