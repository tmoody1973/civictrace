# MOO-691 — Real Gemini Flash agent behind the same seam

## Context

Every agent call today goes through one interface (`StructuredAgentRunner.run`) and is answered by a fixture-backed fake. That proved the pipeline without spending money. MOO-691 puts a real model behind that seam for **one role only — Document Evidence** — so the same unchanged validators accept or refuse what a real Gemini Flash proposes. The fake stays the default; CI never needs credentials. A live eval compares the model's output to Tarik's hand-anchored fixtures. Cloud project (`civictrace-dev-tm`), model (`gemini-3.7-flash`), and location (`global`) are already verified working.

**What the product gets:** the first honest answer to "does a real model survive our gates?" — plus a per-call cost log so we know what a run costs before Slice 5.

## Design decisions (the load-bearing ones)

1. **Hybrid runner, not a big switch.** `--runner adk` routes only `document_evidence` to the real model; `delta_investigator` and `quality_reviewer` keep using fixtures (their real versions are issues 2.3/2.4). A tiny `RoleRoutingRunner` delegates by `definition.role`. Everything else in the workflow is untouched.
2. **The agent must read, not be told.** Payload gives metadata + the manifest's `required_anchors` pages as *hints*; the only way to see text is the read-only page tool. This is the "bounded evidence package" rule made physical.
3. **ADK facts (from live docs, `ctx7 /google/adk-python`):** `Agent(name, model, instruction, tools, output_schema=PydanticModel)`; when `output_schema` + tools are both set, ADK adds a `set_model_response` tool and validates — supported on Vertex Gemini ≥2.0 (our 3.7-flash qualifies). Invoke via `InMemoryRunner.run_async(...)`; final event carries text + `usage_metadata` (tokens). Vertex backend via env: `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` (ADC auth; no key file). Exact import paths verified against the installed release at build time.

## Files

| File | Change |
|---|---|
| `backend/pyproject.toml` | add `google-adk` (pinned) |
| `backend/app/core/config.py` (new) | tiny env reader: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` (default `global`), `CIVICTRACE_MODEL` (default `gemini-3.7-flash`); `require_vertex_config()` fails fast with a plain message |
| `backend/app/tools/artifact_tools.py` (new) | `ArtifactPageReader.read_pages(artifact_id, first_page, last_page)` → ≤10 pages of text via existing `LazyPdfPages` (`app/services/artifact_text.py`); bound to exactly one vaulted artifact path; any other id → typed refusal string. Exposed to ADK as a plain function tool. |
| `backend/app/agents/factory.py` | replace the pseudocode `GoogleAdkStructuredRunner` with the real one: instruction = `build_instruction(role)`; `output_schema=definition.output_model`; tools = the page-reader function only; parse → `output_model.model_validate`; malformed JSON → **one** logged retry then typed `AgentOutputError`; per-call structured log (model, prompt_version, schema_version, trace_id, artifact_id, latency_ms, input/output tokens, tool_calls — never page text) via an injected `UsageLog` |
| `backend/app/agents/routing_runner.py` (new) | `RoleRoutingRunner({"document_evidence": adk_runner}, default=fake_runner)` |
| `backend/app/agents/usage_log.py` (new) | append JSONL rows; `usage.jsonl` written next to `--out` ledger; totals helper for the eval report |
| `backend/app/services/replay.py` + `scripts/replay_corpus.py` | `--runner {fake,adk}` (default fake); adk path builds config + page-reader payload hints (`required_anchors` from the manifest, already parsed in `app/schemas/corpus.py`) |
| `backend/app/agents/document_evidence.py` | payload for the runner becomes a small `DocumentEvidenceTask` (artifact_id, title, canonical_url, page_count, media_type, hint pages) instead of the raw `Artifact` — fake runner keys on `artifact_id`, unchanged |
| `backend/tests/unit/test_adk_runner.py` (new) | with a stubbed ADK runtime: schema-valid parse; malformed → one retry → `AgentOutputError`; tool refuses foreign artifact id and >10 pages; usage row shape; routing runner sends roles to the right place |
| `backend/tests/evaluations/test_document_evidence_grounding.py` (new) | `@pytest.mark.live`, skipped unless `CIVICTRACE_LIVE=1`: per fixture artifact — passes `validate_extraction`, ≥1 item per `required_anchors` page, `$700,000` (plan) and `$2,345,000` (amendment) in accepted excerpts, annual-report blank-status `UNKNOWN` or recorded miss; writes `docs/evaluations/runs/<date>-document-evidence.md` with pass/fail + cost |
| `.env.example`, `backend/README.md`, `docs/evaluations/README.md` | `--runner adk` usage, `CIVICTRACE_LIVE=1`, cost note |

## What does not change

The extraction validators, ledger writes, delta/review flow, API, UI, and every existing test (whole suite stays green with no credentials). No new cloud resources; calls ride the existing dev project + ADC + $10 budget.

## Risks / honest notes

- ADK version drift: docs sampled today; exact imports checked against the installed wheel before writing code. If `output_schema`+tools misbehaves on 3.7-flash, fallback is instruction-embedded JSON schema + response parse (same seam, noted in the issue).
- pypdf text extraction is imperfect on scanned tables; the eval's job is to tell us, not to hide it. A miss goes in the eval report as a known miss.
- Cost: 3 artifacts × (≤10 pages text + schema) on Flash ≈ cents; usage.jsonl proves it.

## Verification (from the issue)

1. `uv run python scripts/replay_corpus.py … --runner adk --out /tmp/ledger-adk.json` — statuses + per-artifact token/latency lines pasted.
2. `CIVICTRACE_LIVE=1 uv run pytest tests/evaluations -q` + generated eval report pasted.
3. One real rejection (if the model anchors wrong → `EXTRACTION_REJECTED` with reason) pasted; if the model never errs, tamper one hint page to prove the gate on a live call.
4. Total cost from `usage.jsonl` pasted (expect cents).
5. Full suite without credentials: green. ruff + mypy clean.
6. Diff-question for Tarik before close: given the tool surface (one page-reader on one artifact), what would you try to make the agent do that it shouldn't?

**PM lens:** we are buying *proof under fire* — the gates were only ever tested against tampered fixtures; now they face a real model. We trade a small model bill and one new dependency. The PM question: "when the model fails the eval, who decides whether to fix the prompt or record the miss?" (Answer: Tarik, via the eval report; the prompt is versioned.)
