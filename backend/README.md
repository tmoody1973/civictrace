# CivicTrace Python Backend

## Purpose

The backend is the CivicTrace control plane and intelligence plane. It owns source-event intake, raw artifact preservation, deterministic validation, bounded ADK invocations, case/ledger persistence, approval checks, and internal asynchronous worker execution. It never lets a model directly write case state or perform an external side effect.

## Intended Runtime

| Service | Deployment | Responsibility |
|---|---|---|
| `civictrace-api` | Authenticated Cloud Run service | Health, cases, evidence inspection, corrections, review and approval requests. |
| `civictrace-worker` | Internal IAM-authenticated Cloud Run service | Cloud Task work: source retrieval, artifact vault, ADK runs, validation, case update, packet rendering. |

## Initial Dependencies

Create `pyproject.toml` with a modern supported Python version and the smallest dependency set necessary for the first replay loop. The expected categories are FastAPI/Uvicorn, Pydantic, Google ADK, Google Cloud Storage/Firestore/PubSub/Tasks/BigQuery clients, HTTP client, structured logging, `pytest`, `pytest-asyncio`, and type/lint tools. Add PDF/media libraries only once a reviewed fixture demands them.

## Local Setup Sequence

1. Copy the root `.env.example` to `.env` and fill only non-secret local values.
2. Authenticate to a dedicated development Google Cloud project through supported local credentials; do not place service-account JSON in the repository.
3. Create the reviewed City replay corpus manifest from `docs/sources/corpus-manifest.example.yaml`.
4. Implement/test domain schemas and deterministic validators first.
5. Add an in-memory/fake repository implementation for local tests before a Firestore implementation.
6. Add the City source adapter and raw artifact vault; use a local fixture/replay mode before live polling.
7. Add one Document Evidence ADK agent and a fixture-based evaluation before adding the full agent team.

## Slice 1 — run it (local, no model, no cloud)

```bash
cd backend
uv sync                                    # Python >=3.12, pydantic, fastapi, pypdf, pyyaml

# 1. Replay the reviewed TID 121 corpus through the workflow (plus the duplicate delivery)
uv run python scripts/replay_corpus.py ../docs/sources/corpus-manifest.yaml \
    --replay-duplicate --out /tmp/civictrace-ledger.json
#   prints one line per event: SUCCEEDED / NOT_PUBLISHED / DUPLICATE_SUPPRESSED, exit 0 when clean

# 2. Serve the Evidence Trace from that ledger
CIVICTRACE_LEDGER_JSON=/tmp/civictrace-ledger.json uv run uvicorn app.main:app --port 8000
curl -s localhost:8000/healthz
curl -s localhost:8000/cases/case-tid121-bronzeville-arts-tech-hub/trace | jq
curl -s localhost:8000/cases | jq '.data[].case_id'                      # case rail (Slice 3)
curl -sI localhost:8000/artifacts/tid121-project-plan-2024/file          # exact PDF bytes + hash header
curl -s localhost:8000/cases/nope/trace          # 404 envelope, never a stack trace

# checks
uv run pytest            # unit + integration
uv run ruff check .
uv run mypy app
```

What the replay proves: artifact stored and hashed before anything else; anchored evidence accepted only
when the quoted words are on the anchored page; the missing 2025 annual report recorded as
`NOT_PUBLISHED`; the same record delivered twice produces one ledger. `# ponytail: no auth on the API
yet — add user auth before any deploy.`

## Required Commands Once Tooling Exists

```bash
# run lint/type/tests from backend/
uv run ruff check .
uv run mypy app
uv run pytest tests/unit tests/evaluations

# run the local API (needs CIVICTRACE_LEDGER_JSON, see Slice 1 above)
CIVICTRACE_LEDGER_JSON=/tmp/civictrace-ledger.json uv run uvicorn app.main:app --reload --port 8000

# replay only reviewed public fixture corpus
uv run python scripts/replay_corpus.py ../docs/sources/corpus-manifest.yaml --replay-duplicate
```

Do not invent test data representing public records. Use reviewed public fixture files or synthetic non-sensitive failure fixtures only.


## Slice 2.2 — real Gemini Flash for Document Evidence (`--runner adk`)

```bash
# needs docs/runbooks/local-vertex-setup.md done once (GOOGLE_CLOUD_PROJECT + ADC; no key file)
set -a; source ../.env; set +a
uv run python scripts/replay_corpus.py ../docs/sources/corpus-manifest.yaml \
    --runner adk --replay-duplicate --out /tmp/ledger-adk.json
cat /tmp/usage.jsonl        # per-call tokens, latency, estimated cost (a full run ≈ $0.016)

# grounding eval vs the hand-anchored fixtures (writes docs/evaluations/runs/<date>-document-evidence.md)
CIVICTRACE_LIVE=1 uv run pytest tests/evaluations -q
```

Only the Document Evidence role uses the real model; the Delta Investigator and Quality Reviewer
stay on fixtures until issues 2.3/2.4. Expected consequence: with `--runner adk` the case ends
`NO_DELTA`, because the fixture delta cites the human-written evidence ids and the bundle check
refuses ids the live run did not produce (`DELTA_REJECTED … not in bundle`) — the gate failing
closed, on purpose. The default `--runner fake` needs no credentials and is what CI runs.
