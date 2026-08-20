#!/usr/bin/env python3
"""Publish the reviewed corpus source events to Pub/Sub for the cloud replay (MOO-710).

Dry-run by default: prints every payload and publishes NOTHING. Sends the 4 manifest
events plus the reviewed duplicate only with an explicit --publish (a write to the
cloud project — get a human go first). Publishing is ORDERED: each event waits for
its workflow job to reach a terminal Firestore status before the next is sent, so
the cloud replay is the same deterministic re-enactment as the local one.

Usage (from backend/):
  uv run python scripts/publish_source_events.py ../docs/sources/corpus-manifest.yaml \
      --project civictrace-dev-tm            # dry run
  ... --publish                              # actually send
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.enums import JobStatus  # noqa: E402
from app.orchestration.idempotency import SourceJobKeys  # noqa: E402
from app.orchestration.workflow import CityDocumentWorkflow  # noqa: E402
from app.schemas.source import SourceEvent  # noqa: E402
from app.services.corpus import load_corpus_manifest  # noqa: E402

TOPIC = "civictrace-source-events"
TERMINAL_STATUSES = {
    JobStatus.SUCCEEDED,
    JobStatus.FAILED,
    JobStatus.DUPLICATE_SUPPRESSED,
    JobStatus.NOT_PUBLISHED,
    JobStatus.NO_ACTION,
    JobStatus.EXTRACTION_REJECTED,
}
WAIT_SECONDS = 240


def corpus_events(manifest_path: Path) -> list[SourceEvent]:
    manifest = load_corpus_manifest(manifest_path)
    artifact_ids = [entry.artifact_id for entry in manifest.artifacts]
    artifact_ids.append(manifest.duplicate_event_fixture.artifact_id)
    return [manifest.source_event(artifact_id) for artifact_id in artifact_ids]


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    events = corpus_events(args.manifest)
    for index, event in enumerate(events):
        mode = "PUBLISH" if args.publish else "DRY-RUN"
        print(f"[{mode} {index + 1}/{len(events)}] {event.source_event_id}")
        print(f"  {event.model_dump_json()}")
    if not args.publish:
        print("\nNothing sent. Re-run with --publish after an explicit human go.")
        return 0

    from google.cloud import firestore, pubsub_v1

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(args.project, TOPIC)
    jobs = firestore.Client(project=args.project).collection("jobs")
    for event in events:
        job_key = SourceJobKeys().source_job_key(
            event, workflow_version=CityDocumentWorkflow.WORKFLOW_VERSION
        )
        already_terminal = _job_status(jobs, job_key) in TERMINAL_STATUSES
        message_id = publisher.publish(
            topic_path, event.model_dump_json().encode("utf-8")
        ).result()
        print(f"published {event.source_event_id} → message {message_id}")
        if already_terminal:
            # The reviewed duplicate: its job is already terminal, so the worker's
            # second run is suppressed by the job repo — nothing new to wait for.
            print(f"  job {job_key[:24]}… already terminal; duplicate suppression expected")
            continue
        status = _wait_terminal(jobs, job_key)
        print(f"  job {job_key[:24]}… → {status}")
        if status not in {JobStatus.SUCCEEDED, JobStatus.NOT_PUBLISHED}:
            print("stopping: the replay is ordered — later events wait for a clean run")
            return 1
    return 0


def _job_status(jobs: Any, job_key: str) -> JobStatus | None:
    snapshot = jobs.document(job_key).get()
    if not snapshot.exists:
        return None
    return JobStatus(snapshot.to_dict()["status"])


def _wait_terminal(jobs: Any, job_key: str) -> JobStatus | None:
    """An ordered replay: block until this event's workflow run finishes."""
    import time

    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        status = _job_status(jobs, job_key)
        if status in TERMINAL_STATUSES:
            return status
        time.sleep(5)
    return None


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--publish", action="store_true", help="actually send (default is dry-run)"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
