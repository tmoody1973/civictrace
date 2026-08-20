"""Cloud service assembly (Slice 5.3, MOO-709): env config + the Firestore/GCS workflow.

Everything here only wires existing seams together — the same workflow, policy gates,
agents, and fixtures the local replay uses, with cloud storage and a durable job repo.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.orchestration.idempotency import SourceJobKeys
from app.orchestration.routes import CityRouteRegistry
from app.orchestration.workflow import CityDocumentWorkflow
from app.policies.policy_service import CivicTracePolicyService
from app.policies.source_policy import SourcePolicy
from app.repositories.firestore_cases import FirestoreLedger
from app.repositories.firestore_jobs import FirestoreJobRepository
from app.schemas.corpus import CorpusManifest
from app.services.agents_service import build_agents_service
from app.services.bigquery_corpus import BigQueryCorpusPrefilter
from app.services.corpus import load_corpus_manifest
from app.services.gcs_artifact_vault import GcsArtifactVault
from app.services.uri_bytes import GcsUriResolver

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent


@dataclass(frozen=True)
class CloudConfig:
    project: str
    region: str
    vault_bucket: str
    packets_bucket: str
    tasks_queue: str
    worker_url: str
    runner_kind: str
    bq_prefilter: bool
    bq_dataset: str
    manifest_path: Path
    allowlist_path: Path
    extraction_path: Path
    fixture_root: Path

    @classmethod
    def from_env(cls) -> CloudConfig:
        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        return cls(
            project=project,
            region=os.environ.get("CIVICTRACE_REGION", "us-central1"),
            vault_bucket=os.environ.get(
                "CIVICTRACE_VAULT_BUCKET", f"{project}-civictrace-vault"
            ),
            packets_bucket=os.environ.get(
                "CIVICTRACE_PACKETS_BUCKET", f"{project}-civictrace-packets"
            ),
            tasks_queue=os.environ.get("CIVICTRACE_TASKS_QUEUE", "civictrace-ingest"),
            worker_url=os.environ.get("CIVICTRACE_WORKER_URL", ""),
            runner_kind=os.environ.get("CIVICTRACE_RUNNER", "fake"),
            bq_prefilter=os.environ.get("CIVICTRACE_BQ_PREFILTER") == "1",
            bq_dataset=os.environ.get("CIVICTRACE_BQ_DATASET", "civictrace_dev"),
            manifest_path=_REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml",
            allowlist_path=_REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml",
            extraction_path=_BACKEND_ROOT
            / "tests"
            / "fixtures"
            / "milwaukee-city-promise-ledger-demo-v1"
            / "fixture_extraction.json",
            fixture_root=_REPO_ROOT,
        )


def build_cloud_ledger(
    config: CloudConfig,
    manifest: CorpusManifest,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FirestoreLedger:
    from google.cloud import firestore

    return FirestoreLedger(
        client=firestore.Client(project=config.project),
        case_id=manifest.case_id,
        case_topic=manifest.case_topic,
        original_artifact_ids=frozenset(
            entry.artifact_id for entry in manifest.artifacts if entry.role == "original_commitment"
        ),
        clock=clock,
    )


def build_corpus_prefilter(config: CloudConfig) -> BigQueryCorpusPrefilter | None:
    """The BQ bounded-evidence prefilter; None keeps local/fake mode on the manifest file."""
    if not config.bq_prefilter:
        return None
    from google.cloud import bigquery

    return BigQueryCorpusPrefilter(
        client=bigquery.Client(project=config.project),
        project=config.project,
        dataset=config.bq_dataset,
    )


def build_cloud_workflow(
    config: CloudConfig,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    prefilter: BigQueryCorpusPrefilter | None = None,
) -> tuple[CityDocumentWorkflow, FirestoreLedger, CorpusManifest]:
    from google.cloud import firestore  # noqa: I001
    from google.cloud import storage  # type: ignore[attr-defined]

    manifest = load_corpus_manifest(config.manifest_path)
    ledger = build_cloud_ledger(config, manifest, clock=clock)
    storage_client = storage.Client(project=config.project)
    workflow = CityDocumentWorkflow(
        artifacts=GcsArtifactVault(
            manifest=manifest,
            fixture_root=config.fixture_root,
            storage_client=storage_client,
            bucket_name=config.vault_bucket,
        ),
        jobs=FirestoreJobRepository(firestore.Client(project=config.project)),
        cases=ledger,
        policy=CivicTracePolicyService(
            source_policy=SourcePolicy.from_yaml(config.allowlist_path),
            uri_resolver=GcsUriResolver(storage_client),
        ),
        agents=build_agents_service(
            manifest,
            extraction_path=config.extraction_path,
            fixture_root=config.fixture_root,
            runner_kind=config.runner_kind,
            hint_pages=prefilter.hint_pages() if prefilter is not None else None,
        )[0],
        routes=CityRouteRegistry(),
        idempotency=SourceJobKeys(),
    )
    return workflow, ledger, manifest
