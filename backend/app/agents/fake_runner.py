"""Stand-in for every agent role: returns reviewed, hand-written fixtures and records each call.

No network, no model SDK. The workflow cannot tell the difference — that is the point.
Fixture lookup: role → key, where the key is the payload's `artifact_id` (document evidence)
or `trigger_artifact_id` (delta investigator on a CaseBundle).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.agents.factory import AgentDefinition

KEY_FIELDS = ("artifact_id", "trigger_artifact_id", "case_id")


@dataclass(frozen=True)
class RunnerCall:
    agent_name: str
    artifact_id: str
    trace_id: str


class FakeAgentRunner:
    def __init__(self, fixtures_by_role: dict[str, dict[str, dict[str, Any]]]) -> None:
        self._fixtures = fixtures_by_role
        self.calls: list[RunnerCall] = []

    @classmethod
    def from_payloads(
        cls,
        *,
        extraction: dict[str, Any],
        delta: dict[str, Any] | None = None,
        review: dict[str, Any] | None = None,
        inquiry: dict[str, Any] | None = None,
    ) -> FakeAgentRunner:
        fixtures = {"document_evidence": extraction["extractions"]}
        if delta is not None:
            fixtures["delta_investigator"] = delta["proposals"]
        if review is not None:
            fixtures["quality_reviewer"] = review["reviews"]
        if inquiry is not None:
            fixtures["inquiry_planner"] = inquiry["proposals"]
        return cls(fixtures)

    @classmethod
    def from_paths(
        cls,
        *,
        extraction_path: Path,
        delta_path: Path | None = None,
        review_path: Path | None = None,
        inquiry_path: Path | None = None,
    ) -> FakeAgentRunner:
        return cls.from_payloads(
            extraction=json.loads(extraction_path.read_text()),
            delta=json.loads(delta_path.read_text()) if delta_path else None,
            review=json.loads(review_path.read_text()) if review_path else None,
            inquiry=json.loads(inquiry_path.read_text()) if inquiry_path else None,
        )

    async def run(
        self, definition: AgentDefinition, payload: BaseModel, *, trace_id: str
    ) -> BaseModel:
        key = _fixture_key(payload)
        self.calls.append(RunnerCall(definition.name, key, trace_id))
        try:
            raw = self._fixtures[definition.role][key]
        except KeyError as exc:
            raise KeyError(f"no fixture for role {definition.role!r} key {key!r}") from exc
        return definition.output_model.model_validate(raw)


def _fixture_key(payload: BaseModel) -> str:
    data = payload.model_dump()
    for field in KEY_FIELDS:
        if data.get(field):
            return str(data[field])
    raise KeyError(f"payload {type(payload).__name__} has none of {KEY_FIELDS}")
