"""Grounding eval (MOO-691): does the real Document Evidence agent survive our gates,
and does it find what a human found?

Live-only: real Gemini Flash calls, cents of cost. Run:
    CIVICTRACE_LIVE=1 uv run pytest tests/evaluations -q
Writes docs/evaluations/runs/<date>-document-evidence.md (pass/fail per criterion + cost).
The reviewed human baseline is fixture_extraction.json; the manifest's required_anchors
pages are where a human said the load-bearing facts live.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.agents.document_evidence import DOCUMENT_EVIDENCE_DEFINITION
from app.agents.factory import GoogleAdkStructuredRunner
from app.agents.usage_log import UsageLog
from app.core.config import apply_vertex_env, require_vertex_config
from app.schemas.corpus import CorpusManifest
from app.schemas.evidence import DocumentEvidenceTask, DocumentExtraction
from app.services.artifact_text import LazyPdfPages
from app.services.corpus import load_corpus_manifest
from app.services.validator import validate_extraction
from app.tools.artifact_tools import ArtifactPageReader
from tests.conftest import MANIFEST_PATH, REPO_ROOT

pytestmark = pytest.mark.live

RUNS_DIR = REPO_ROOT / "docs" / "evaluations" / "runs"
MUST_QUOTE = {
    "tid121-project-plan-2024": "$700,000",
    "tid121-amendment-1-2026": "$2,345,000",
}
BLANK_STATUS_ARTIFACT = "tid-annual-report-2024"

if not os.environ.get("CIVICTRACE_LIVE"):
    pytest.skip("set CIVICTRACE_LIVE=1 to run real-model evals", allow_module_level=True)


@pytest.fixture(scope="module")
def manifest() -> CorpusManifest:
    return load_corpus_manifest(MANIFEST_PATH)


@pytest.fixture(scope="module")
def live_results(manifest: CorpusManifest) -> dict:
    """One real extraction per available artifact; shared across criteria to pay once."""
    config = require_vertex_config()
    apply_vertex_env(config)
    usage = UsageLog()
    fixture_dir = REPO_ROOT / manifest.fixture_dir
    results: dict[str, dict] = {}
    for entry in manifest.artifacts:
        if entry.local_path is None:
            continue
        pdf_path = fixture_dir / entry.local_path
        runner = GoogleAdkStructuredRunner(
            model=config.model,
            page_reader_factory=lambda _aid, p=pdf_path, a=entry.artifact_id: ArtifactPageReader(
                artifact_id=a, pdf_path=p
            ),
            usage_log=usage,
        )
        task = DocumentEvidenceTask(
            artifact_id=entry.artifact_id,
            title=entry.title,
            canonical_url=entry.canonical_url,
            media_type=entry.media_type,
            page_count=entry.page_count,
            hint_pages=[anchor.page for anchor in entry.required_anchors],
        )
        extraction = asyncio.run(
            runner.run(DOCUMENT_EVIDENCE_DEFINITION, task, trace_id=f"eval-{entry.artifact_id}")
        )
        artifact = _as_artifact(manifest, entry.artifact_id, pdf_path)
        pages = LazyPdfPages(pdf_path)
        validation = validate_extraction(
            DocumentExtraction.model_validate(extraction.model_dump()), artifact, pages
        )
        results[entry.artifact_id] = {
            "extraction": extraction,
            "validation": validation,
            "required_pages": [anchor.page for anchor in entry.required_anchors],
        }
    report = _write_report(results, usage, config.model)
    results["_report_path"] = report
    return results


def _as_artifact(manifest: CorpusManifest, artifact_id: str, pdf_path: Path):
    from app.domain.enums import ArtifactAvailability
    from app.schemas.source import Artifact
    from app.services.artifact_vault import HASH_PREFIX, sha256_hex

    entry = manifest.entry(artifact_id)
    return Artifact(
        artifact_id=entry.artifact_id,
        source_id=entry.source_id,
        canonical_url=entry.canonical_url,
        external_id=entry.external_id,
        title=entry.title,
        media_type=entry.media_type,
        content_hash=HASH_PREFIX + sha256_hex(pdf_path.read_bytes()),
        byte_length=pdf_path.stat().st_size,
        page_count=entry.page_count,
        storage_uri=pdf_path.resolve().as_uri(),
        retrieved_at=entry.retrieved_at,
        availability=ArtifactAvailability.AVAILABLE,
    )


def test_every_artifact_passes_the_extraction_gates(live_results: dict) -> None:
    failures = {
        artifact_id: list(result["validation"].reasons)
        for artifact_id, result in live_results.items()
        if not artifact_id.startswith("_") and result["validation"].reasons
    }
    assert failures == {}, f"validator refused live output: {failures}"


def test_required_anchor_pages_are_covered(live_results: dict) -> None:
    missing: dict[str, list[int]] = {}
    for artifact_id, result in live_results.items():
        if artifact_id.startswith("_"):
            continue
        anchored_pages = {
            int(anchor.anchor_value)
            for item in result["extraction"].evidence
            for anchor in item.anchors
            if anchor.anchor_value.isdigit()
        }
        gap = [page for page in result["required_pages"] if page not in anchored_pages]
        if gap:
            missing[artifact_id] = gap
    assert missing == {}, f"required_anchors pages with no evidence item: {missing}"


@pytest.mark.parametrize(("artifact_id", "needle"), sorted(MUST_QUOTE.items()))
def test_load_bearing_dollar_figures_are_quoted(
    live_results: dict, artifact_id: str, needle: str
) -> None:
    excerpts = " ".join(
        item.verbatim_excerpt for item in live_results[artifact_id]["extraction"].evidence
    )
    assert needle in excerpts, f"{artifact_id}: {needle!r} not in any verbatim excerpt"


def test_blank_completion_status_is_unknown_or_recorded_miss(live_results: dict) -> None:
    from app.domain.enums import EvidenceStatus

    extraction = live_results[BLANK_STATUS_ARTIFACT]["extraction"]
    has_unknown = any(item.status is EvidenceStatus.UNKNOWN for item in extraction.evidence)
    if not has_unknown:
        readme = (REPO_ROOT / "docs" / "evaluations" / "README.md").read_text()
        assert "completion status" in readme.lower(), (
            "no UNKNOWN item for the blank Completion Status and no recorded miss in "
            "docs/evaluations/README.md — record one or fix the prompt"
        )


def _write_report(results: dict, usage: UsageLog, model: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# Document Evidence grounding eval — {date}",
        "",
        f"Model `{model}` · prompt `{DOCUMENT_EVIDENCE_DEFINITION.prompt_version}` · "
        f"estimated cost **${usage.total_estimated_usd():.4f}** "
        f"({sum(r.input_tokens for r in usage.records)} in / "
        f"{sum(r.output_tokens for r in usage.records)} out tokens)",
        "",
        "| artifact | evidence items | validator | required pages covered | must-quote |",
        "|---|---|---|---|---|",
    ]
    for artifact_id, result in sorted(results.items()):
        if artifact_id.startswith("_"):
            continue
        extraction, validation = result["extraction"], result["validation"]
        anchored = {
            int(a.anchor_value)
            for item in extraction.evidence
            for a in item.anchors
            if a.anchor_value.isdigit()
        }
        covered = all(page in anchored for page in result["required_pages"])
        needle = MUST_QUOTE.get(artifact_id)
        quoted = (
            "n/a"
            if needle is None
            else ("✅" if any(needle in i.verbatim_excerpt for i in extraction.evidence) else "❌")
        )
        gate = "✅ pass" if not validation.reasons else "❌ " + "; ".join(validation.reasons)[:80]
        gaps = [p for p in result["required_pages"] if p not in anchored]
        pages = "✅" if covered else f"❌ missing {gaps}"
        lines.append(
            f"| {artifact_id} | {len(extraction.evidence)} | {gate} | {pages} | {quoted} |"
        )
    lines += ["", "Raw usage rows:", "```json"]
    lines += [
        json.dumps(
            {
                "artifact_id": r.artifact_id,
                "in": r.input_tokens,
                "out": r.output_tokens,
                "ms": r.latency_ms,
                "usd": round(r.estimated_usd(), 5),
            }
        )
        for r in usage.records
    ]
    lines += ["```", ""]
    path = RUNS_DIR / f"{date}-document-evidence.md"
    path.write_text("\n".join(lines))
    return path
