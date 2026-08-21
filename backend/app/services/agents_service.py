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
from app.schemas.evidence import MediaEvidenceTask
from app.schemas.transcript import TranscriptArtifact
from app.tools.artifact_tools import ArtifactPageReader
from app.tools.transcript_tools import TranscriptSpanReader


def build_agents_service(
    manifest: CorpusManifest,
    *,
    extraction_path: Path,
    fixture_root: Path,
    runner_kind: str = "fake",
    delta_path: Path | None = None,
    review_path: Path | None = None,
    inquiry_path: Path | None = None,
    media_path: Path | None = None,
    hint_pages: dict[str, list[int]] | None = None,
) -> tuple[DocumentEvidenceAgentService, UsageLog | None]:
    fixture_dir = fixture_root / manifest.fixture_dir
    fake_runner = _fake_runner(
        extraction_path,
        delta_path=delta_path,
        review_path=review_path,
        inquiry_path=inquiry_path,
        media_path=media_path,
    )
    runner, usage_log = _runner(manifest, fixture_dir, runner_kind, fake_runner)
    # Cloud mode passes hint_pages from the BigQuery prefilter (MOO-710); the
    # manifest anchors stay the source everywhere else.
    if hint_pages is None:
        hint_pages = {
            entry.artifact_id: [anchor.page for anchor in entry.required_anchors]
            for entry in manifest.artifacts
        }
    service = DocumentEvidenceAgentService(
        runner,
        case_id=manifest.case_id,
        hint_pages=hint_pages,
        media_task_for=lambda artifact_id: _media_task(manifest, fixture_dir, artifact_id),
    )
    return service, usage_log


def load_media_transcript(
    manifest: CorpusManifest, fixture_dir: Path, artifact_id: str
) -> TranscriptArtifact:
    """The committed diarized transcript for one reviewed media artifact."""
    entry = manifest.media_entry(artifact_id)
    if entry.transcript_path is None:
        raise ValueError(f"{artifact_id}: media entry has no committed transcript")
    return TranscriptArtifact.model_validate_json(
        (fixture_dir / entry.transcript_path).read_text()
    )


def _media_task(
    manifest: CorpusManifest, fixture_dir: Path, artifact_id: str
) -> MediaEvidenceTask:
    entry = manifest.media_entry(artifact_id)
    transcript = load_media_transcript(manifest, fixture_dir, artifact_id)
    return MediaEvidenceTask(
        artifact_id=artifact_id,
        transcript_id=transcript.transcript_id,
        title=entry.title,
        canonical_url=entry.canonical_url,
        segment_start_seconds=transcript.segment_start_seconds,
        segment_end_seconds=transcript.segment_end_seconds,
        duration_ms=transcript.duration_seconds() * 1000,
        speaker_labels=sorted({segment.speaker_label for segment in transcript.segments}),
        focus_basis=entry.focus_segment.basis if entry.focus_segment else None,
    )


def _fake_runner(
    extraction_path: Path,
    *,
    delta_path: Path | None,
    review_path: Path | None,
    inquiry_path: Path | None,
    media_path: Path | None,
) -> FakeAgentRunner:
    delta = delta_path or extraction_path.with_name("fixture_delta.json")
    review = review_path or extraction_path.with_name("fixture_review.json")
    inquiry = inquiry_path or extraction_path.with_name("fixture_inquiry.json")
    media = media_path or extraction_path.with_name("fixture_media_extraction.json")
    return FakeAgentRunner.from_paths(
        extraction_path=extraction_path,
        delta_path=delta if delta.exists() else None,
        review_path=review if review.exists() else None,
        inquiry_path=inquiry if inquiry.exists() else None,
        media_path=media if media.exists() else None,
    )


def _runner(
    manifest: CorpusManifest,
    fixture_dir: Path,
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

    def page_reader_for(artifact_id: str) -> ArtifactPageReader:
        entry = manifest.entry(artifact_id)
        if entry.local_path is None:
            raise ValueError(f"{artifact_id}: no vaulted file to read")
        return ArtifactPageReader(artifact_id=artifact_id, pdf_path=fixture_dir / entry.local_path)

    def transcript_reader_for(artifact_id: str) -> TranscriptSpanReader:
        return TranscriptSpanReader(
            artifact_id=artifact_id,
            transcript=load_media_transcript(manifest, fixture_dir, artifact_id),
        )

    adk_runner = GoogleAdkStructuredRunner(
        model=config.model,
        page_reader_factory=page_reader_for,
        transcript_reader_factory=transcript_reader_for,
        usage_log=usage_log,
    )
    # The full agent chain runs on the live model: extraction reads real pages or transcript
    # spans, and the investigator/reviewer/planner reason over validated evidence. Fixtures
    # remain only as the no-credentials default (runner_kind="fake") for local dev and CI.
    live_roles: dict[str, StructuredAgentRunner] = {
        "document_evidence": adk_runner,
        "media_evidence": adk_runner,
        "delta_investigator": adk_runner,
        "quality_reviewer": adk_runner,
        "inquiry_planner": adk_runner,
    }
    return RoleRoutingRunner(live_roles, default=fake_runner), usage_log
