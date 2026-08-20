"""Firestore-backed job state (Slice 5.3, MOO-709): idempotency that survives scale-to-zero.

One document per job key in `jobs/{job_key}`. A retried Cloud Task sees the terminal
document and becomes a no-op; a crashed STARTED job is retried by Tasks (finite attempts)
and `start()` allows re-entry from FAILED/STARTED so the retry can run.
"""

from __future__ import annotations

from google.cloud import firestore

from app.domain.enums import JobStatus
from app.orchestration.workflow import WorkflowContext

JOBS_COLLECTION = "jobs"
TERMINAL = frozenset({JobStatus.SUCCEEDED})


class FirestoreJobRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._jobs = client.collection(JOBS_COLLECTION)

    async def exists_terminal(self, job_key: str) -> bool:
        snapshot = self._jobs.document(job_key).get()
        return snapshot.exists and snapshot.get("status") in TERMINAL

    async def start(self, job_key: str, *, context: WorkflowContext) -> None:
        # Unlike the in-memory repo, STARTED does not block: a Cloud Task retry after a
        # crash must be able to re-enter. Ledger append dedupe keeps re-entry harmless.
        self._jobs.document(job_key).set(
            {"status": JobStatus.STARTED, "trace_id": context.trace_id}, merge=True
        )

    async def succeed(self, job_key: str, *, context: WorkflowContext) -> None:
        self._jobs.document(job_key).set(
            {"status": JobStatus.SUCCEEDED, "trace_id": context.trace_id}, merge=True
        )

    async def fail(self, job_key: str, *, error_code: str, context: WorkflowContext) -> None:
        self._jobs.document(job_key).set(
            {"status": JobStatus.FAILED, "error_code": error_code, "trace_id": context.trace_id},
            merge=True,
        )
