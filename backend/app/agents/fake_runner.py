"""Stand-in for the Document Evidence Agent: returns the reviewed fixture extraction, records calls.

No network, no model SDK. The workflow cannot tell the difference — that is the point.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.agents.factory import AgentDefinition


@dataclass(frozen=True)
class RunnerCall:
    agent_name: str
    artifact_id: str
    trace_id: str


class FakeAgentRunner:
    def __init__(self, fixture_payload: dict[str, Any]) -> None:
        self._by_artifact: dict[str, dict[str, Any]] = fixture_payload["extractions"]
        self.calls: list[RunnerCall] = []

    @classmethod
    def from_path(cls, path: Path) -> FakeAgentRunner:
        return cls(json.loads(path.read_text()))

    async def run(
        self, definition: AgentDefinition, payload: BaseModel, *, trace_id: str
    ) -> BaseModel:
        artifact_id = str(payload.model_dump()["artifact_id"])
        self.calls.append(RunnerCall(definition.name, artifact_id, trace_id))
        return definition.output_model.model_validate(self._by_artifact[artifact_id])
