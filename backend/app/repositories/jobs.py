"""Job state keyed by idempotency key. In-memory implementation for Slice 1.

# ponytail: Firestore implementation + retry caps/dead-letter in Slice 2.
"""

from __future__ import annotations

from app.domain.enums import JobStatus
from app.domain.errors import DuplicateJobError
from app.orchestration.workflow import WorkflowContext

TERMINAL = frozenset({JobStatus.SUCCEEDED})
IN_FLIGHT = frozenset({JobStatus.STARTED})


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._status: dict[str, JobStatus] = {}

    def status(self, job_key: str) -> JobStatus | None:
        return self._status.get(job_key)

    async def exists_terminal(self, job_key: str) -> bool:
        return self._status.get(job_key) in TERMINAL

    async def start(self, job_key: str, *, context: WorkflowContext) -> None:
        current = self._status.get(job_key)
        if current in TERMINAL or current in IN_FLIGHT:
            raise DuplicateJobError(f"job {job_key} is already {current}")
        self._status[job_key] = JobStatus.STARTED

    async def succeed(self, job_key: str, *, context: WorkflowContext) -> None:
        self._status[job_key] = JobStatus.SUCCEEDED

    async def fail(self, job_key: str, *, error_code: str, context: WorkflowContext) -> None:
        self._status[job_key] = JobStatus.FAILED
