"""Cloud wiring for the source watcher (MOO-721).

Worker side: `CloudWatchRunner` runs one bounded check over every known case recipe —
a few read-only Legistar API calls per case, hits into the case ledger, watermarks into
Firestore. API side: `WatchRunEnqueuer` turns the studio's "check now" button into
exactly one named Cloud Task per minute (name-deduped), so a double-click never doubles
the API calls.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.repositories.watch import FirestoreWatchStore
from app.services.cloud import CloudConfig, _known_manifests, build_cloud_ledger
from app.services.corpus import load_corpus_manifest
from app.services.source_watcher import SourceWatcher

logger = logging.getLogger("civictrace.watcher")

WATCH_TASK_PATH = "/tasks/watch"


class CloudWatchRunner:
    def __init__(self, config: CloudConfig | None = None) -> None:
        self._config = config or CloudConfig.from_env()

    async def run(self) -> dict[str, int]:
        from google.cloud import firestore

        config = self._config
        yaml_manifest = load_corpus_manifest(config.manifest_path)
        manifests = _known_manifests(config, yaml_manifest)
        watcher = SourceWatcher(
            get_json=_default_get_json,
            state_store=FirestoreWatchStore(firestore.Client(project=config.project)),
            clock=lambda: datetime.now(UTC),
        )
        totals = {"cases": 0, "checked": 0, "skipped": 0, "hits": 0}
        for manifest in manifests:
            ledger = build_cloud_ledger(config, manifest)
            summary = watcher.check_case(manifest, ledger)
            totals["cases"] += 1
            for field in ("checked", "skipped", "hits"):
                totals[field] += summary[field]
            logger.info("watch %s → %s", manifest.case_id, json.dumps(summary))
        logger.info("watch run complete: %s", json.dumps(totals))
        return totals


class WatchRunEnqueuer:
    """One named watch task per minute; Tasks name-dedupe absorbs double-clicks."""

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

    def __call__(self) -> str:
        from google.api_core.exceptions import AlreadyExists
        from google.cloud import tasks_v2

        minute = datetime.now(UTC).strftime("%Y%m%d%H%M")
        task_name = f"{self._queue_path}/tasks/watch-run-{minute}"
        task = tasks_v2.Task(
            name=task_name,
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{self._worker_url}{WATCH_TASK_PATH}",
                headers={"Content-Type": "application/json"},
                body=b"{}",
                oidc_token=tasks_v2.OidcToken(service_account_email=self._invoker_email),
            ),
        )
        try:
            self._client.create_task(parent=self._queue_path, task=task)
        except AlreadyExists:
            logger.info("watch run already queued this minute")
        return f"watch-run-{minute}"


def _default_get_json(url: str) -> object:
    from app.services.legistar_intake import _default_get_json as get

    return get(url)
