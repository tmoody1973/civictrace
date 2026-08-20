"""Build the bounded agent service for any runtime (local replay or cloud worker).

Fixtures stay the default runner everywhere; `runner_kind="adk"` routes only the
Document Evidence role to the real Gemini Flash runner (MOO-691's seam, unchanged).
"""

from __future__ import annotations

from pathlib import Path

from app.agents.document_evidence import DocumentEvidenceAgentService
from app.agents.factory import GoogleAdkStructuredRunner, StructuredAgentRunner
from app.agents.fake_runner import FakeAgentRunner
from app.agents.routing_runner import RoleRoutingRunner
from app.agents.usage_log import UsageLog
from app.core.config import apply_vertex_env, require_vertex_config
from app.schemas.corpus import CorpusManifest
from app.tools.artifact_tools import ArtifactPageReader


def build_agents_service(
    manifest: CorpusManifest,
    *,
    extraction_path: Path,
    fixture_root: Path,
    runner_kind: str = "fake",
    delta_path: Path | None = None,
    review_path: Path | None = None,
    inquiry_path: Path | None = None,
) -> tuple[DocumentEvidenceAgentService, UsageLog | None]:
    fake_runner = _fake_runner(
        extraction_path, delta_path=delta_path, review_path=review_path, inquiry_path=inquiry_path
    )
    runner, usage_log = _runner(manifest, fixture_root, runner_kind, fake_runner)
    hint_pages = {
        entry.artifact_id: [anchor.page for anchor in entry.required_anchors]
        for entry in manifest.artifacts
    }
    service = DocumentEvidenceAgentService(
        runner, case_id=manifest.case_id, hint_pages=hint_pages
    )
    return service, usage_log


def _fake_runner(
    extraction_path: Path,
    *,
    delta_path: Path | None,
    review_path: Path | None,
    inquiry_path: Path | None,
) -> FakeAgentRunner:
    delta = delta_path or extraction_path.with_name("fixture_delta.json")
    review = review_path or extraction_path.with_name("fixture_review.json")
    inquiry = inquiry_path or extraction_path.with_name("fixture_inquiry.json")
    return FakeAgentRunner.from_paths(
        extraction_path=extraction_path,
        delta_path=delta if delta.exists() else None,
        review_path=review if review.exists() else None,
        inquiry_path=inquiry if inquiry.exists() else None,
    )


def _runner(
    manifest: CorpusManifest,
    fixture_root: Path,
    runner_kind: str,
    fake_runner: FakeAgentRunner,
) -> tuple[StructuredAgentRunner, UsageLog | None]:
    if runner_kind == "fake":
        return fake_runner, None
    if runner_kind != "adk":
        raise ValueError(f"unknown runner kind {runner_kind!r}; use 'fake' or 'adk'")
    config = require_vertex_config()
    apply_vertex_env(config)
    usage_log = UsageLog()
    fixture_dir = fixture_root / manifest.fixture_dir

    def page_reader_for(artifact_id: str) -> ArtifactPageReader:
        entry = manifest.entry(artifact_id)
        if entry.local_path is None:
            raise ValueError(f"{artifact_id}: no vaulted file to read")
        return ArtifactPageReader(artifact_id=artifact_id, pdf_path=fixture_dir / entry.local_path)

    adk_runner = GoogleAdkStructuredRunner(
        model=config.model,
        page_reader_factory=page_reader_for,
        usage_log=usage_log,
    )
    # Real model for document evidence only; delta/reviewer/planner stay on fixtures.
    return RoleRoutingRunner({"document_evidence": adk_runner}, default=fake_runner), usage_log
