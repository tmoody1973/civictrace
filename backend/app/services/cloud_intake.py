"""Cloud wiring for case intake (MOO-719).

API side: `CreateCaseEnqueuer` turns an approval into exactly one named Cloud Task.
Worker side: `CloudCaseCreator` runs the whole gated chain from durable state —
fetch → hash-lock → vault → manifest record → replay pipeline, one event at a time,
and writes the bundle's final status. Deterministic refusals end the task (no retry);
transient failures raise so Cloud Tasks retries within the queue's bounded caps.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime

from app.agents.usage_log import UsageLog
from app.domain.enums import JobStatus
from app.policies.source_policy import SourcePolicy
from app.repositories.intake import FirestoreIntakeStore
from app.schemas.corpus import ManifestArtifact
from app.schemas.intake import BundleStatus
from app.services.case_intake import CaseIntakeError, CaseIntakeService
from app.services.cloud import CloudConfig, build_cloud_workflow_for_manifest
from app.services.gcs_artifact_vault import store_gcs_bytes

logger = logging.getLogger("civictrace.intake")

CREATE_CASE_PATH = "/tasks/create-case"
OK_STATUSES = frozenset({JobStatus.SUCCEEDED, JobStatus.NO_ACTION})


class CreateCaseEnqueuer:
    """One named task per bundle; Tasks dedupes re-approvals by name."""

    def __init__(self, config: CloudConfig | None = None) -> None:
        import os

        from google.cloud import tasks_v2

        config = config or CloudConfig.from_env()
        self._client = tasks_v2.CloudTasksClient()
        self._queue_path = self._client.queue_path(
            config.project, config.region, config.tasks_queue
        )
        self._worker_url = config.worker_url.rstrip("/")
        self._invoker_email = os.environ.get("CIVICTRACE_WORKER_SA", "")

    def __call__(self, bundle_id: str) -> None:
        from google.api_core.exceptions import AlreadyExists
        from google.cloud import tasks_v2

        task = tasks_v2.Task(
            name=f"{self._queue_path}/tasks/create-{bundle_id}",
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{self._worker_url}{CREATE_CASE_PATH}",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"bundle_id": bundle_id}).encode("utf-8"),
                oidc_token=tasks_v2.OidcToken(service_account_email=self._invoker_email),
            ),
        )
        try:
            self._client.create_task(parent=self._queue_path, task=task)
        except AlreadyExists:
            logger.info("create-case task for %s already queued", bundle_id)


class CloudCaseCreator:
    def __init__(self, config: CloudConfig | None = None) -> None:
        self._config = config or CloudConfig.from_env()

    async def run(self, bundle_id: str) -> dict[str, str]:
        from google.cloud import firestore  # noqa: I001
        from google.cloud import storage  # type: ignore[attr-defined]

        config = self._config
        store = FirestoreIntakeStore(firestore.Client(project=config.project))
        bundle = store.get_bundle(bundle_id)
        selection = store.get_selection(bundle_id)
        if bundle is None or selection is None:
            return {"status": "REFUSED", "reason": "bundle or selection missing"}
        if bundle.status is BundleStatus.CASE_CREATED:
            return {"status": "DUPLICATE_SUPPRESSED", "case_id": bundle.case_id or ""}
        if bundle.status not in (BundleStatus.APPROVED, BundleStatus.CREATING, BundleStatus.FAILED):
            return {"status": "REFUSED", "reason": f"bundle is {bundle.status}"}
        store.set_status(bundle_id, BundleStatus.CREATING)

        source_policy = SourcePolicy.from_yaml(config.allowlist_path)
        storage_client = storage.Client(project=config.project)
        try:
            service = CaseIntakeService(
                source_policy=source_policy,
                store_bytes=_vault_writer(config, storage_client),
                save_manifest=store.save_manifest,
                clock=lambda: datetime.now(UTC),
                load_vaulted_pdf=_vault_reader(config, storage_client),
            )
            manifest, events = service.create_case(bundle, selection)
        except CaseIntakeError as exc:
            store.set_status(bundle_id, BundleStatus.FAILED, reason=str(exc))
            return {"status": "REFUSED", "reason": str(exc)}

        workflow, _, usage_log = build_cloud_workflow_for_manifest(config, manifest)
        for index, event in enumerate(events):
            result = await workflow.run(event, trace_id=f"intake-{bundle_id}-{index}")
            logger.info(
                "intake case %s event %s → %s", manifest.case_id, event.artifact_id, result.status
            )
            if result.status not in OK_STATUSES:
                reason = f"{event.artifact_id}: {result.status} — {result.reason}"
                store.set_status(bundle_id, BundleStatus.FAILED, reason=reason)
                _log_usage(usage_log)
                return {"status": "FAILED", "reason": reason}
        _log_usage(usage_log)
        store.set_status(bundle_id, BundleStatus.CASE_CREATED, case_id=manifest.case_id)
        return {"status": "CASE_CREATED", "case_id": manifest.case_id}


def _vault_writer(
    config: CloudConfig, storage_client: object
) -> Callable[[ManifestArtifact, bytes], str]:
    def store_bytes(entry: ManifestArtifact, payload: bytes) -> str:
        return store_gcs_bytes(storage_client, config.vault_bucket, entry, payload)  # type: ignore[arg-type]

    return store_bytes


def _vault_reader(config: CloudConfig, storage_client: object) -> Callable[[str], bytes | None]:
    """Retry support (MOO-726): an already-vaulted Word→PDF conversion is adopted, never
    re-converted, so the hash-lock stays stable across Cloud Tasks retries."""

    def load_vaulted_pdf(object_name: str) -> bytes | None:
        blob = storage_client.bucket(config.vault_bucket).blob(object_name)  # type: ignore[attr-defined]
        if not blob.exists():
            return None
        return bytes(blob.download_as_bytes())

    return load_vaulted_pdf


def _log_usage(usage_log: UsageLog | None) -> None:
    """Same model_usage lines as the ingest path, so cost stays visible per call."""
    if usage_log is None:
        return
    for record in usage_log.records:
        logger.info(
            "model_usage %s",
            json.dumps({**asdict(record), "estimated_usd": round(record.estimated_usd(), 6)}),
        )
