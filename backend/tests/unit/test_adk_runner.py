"""MOO-691 boundaries, provable without a network: schema gate, retry cap, tool fence, usage rows."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from app.agents.document_evidence import DOCUMENT_EVIDENCE_DEFINITION
from app.agents.factory import AgentDefinition, AgentOutputError, GoogleAdkStructuredRunner
from app.agents.routing_runner import RoleRoutingRunner
from app.agents.usage_log import UsageLog
from app.schemas.evidence import DocumentEvidenceTask
from app.tools.artifact_tools import ArtifactPageReader
from tests.conftest import FIXTURE_DIR

PLAN_PDF = FIXTURE_DIR / "records" / "tid121-project-plan-2024.pdf"
TASK = DocumentEvidenceTask(artifact_id="tid121-project-plan-2024", hint_pages=[2, 5, 6])

GOOD_EXTRACTION = {
    "artifact_id": "tid121-project-plan-2024",
    "agent_name": "civictrace-document_evidence",
    "agent_version": "test",
    "evidence": [],
}


def _reader(_: str) -> ArtifactPageReader:
    return ArtifactPageReader(artifact_id="tid121-project-plan-2024", pdf_path=PLAN_PDF)


def _stub(responses: list[str]) -> Any:
    async def run_agent(**_: Any) -> tuple[str, dict[str, int]]:
        return responses.pop(0), {"input_tokens": 100, "output_tokens": 20}

    return run_agent


def _runner(responses: list[str], usage: UsageLog) -> GoogleAdkStructuredRunner:
    return GoogleAdkStructuredRunner(
        model="gemini-test", page_reader_factory=_reader, usage_log=usage, run_agent=_stub(responses)
    )


def test_valid_output_parses_and_logs_one_usage_row() -> None:
    import json

    usage = UsageLog()
    runner = _runner([json.dumps(GOOD_EXTRACTION)], usage)
    result = asyncio.run(runner.run(DOCUMENT_EVIDENCE_DEFINITION, TASK, trace_id="t1"))
    assert result.artifact_id == "tid121-project-plan-2024"
    assert len(usage.records) == 1
    row = usage.records[0]
    assert (row.model, row.artifact_id, row.retried) == ("gemini-test", TASK.artifact_id, False)
    assert row.input_tokens == 100 and row.output_tokens == 20
    assert row.estimated_usd() > 0


def test_markdown_fenced_output_is_accepted() -> None:
    import json

    runner = _runner(["```json\n" + json.dumps(GOOD_EXTRACTION) + "\n```"], UsageLog())
    result = asyncio.run(runner.run(DOCUMENT_EVIDENCE_DEFINITION, TASK, trace_id="t2"))
    assert result.artifact_id == TASK.artifact_id


def test_malformed_output_gets_exactly_one_retry_then_typed_error() -> None:
    usage = UsageLog()
    runner = _runner(["not json", "still not json", "never reached"], usage)
    with pytest.raises(AgentOutputError):
        asyncio.run(runner.run(DOCUMENT_EVIDENCE_DEFINITION, TASK, trace_id="t3"))
    assert len(usage.records) == 2  # first try + one retry, both logged
    assert [row.retried for row in usage.records] == [False, True]


def test_page_reader_refuses_foreign_artifact_and_wide_ranges() -> None:
    reader = ArtifactPageReader(artifact_id="tid121-project-plan-2024", pdf_path=PLAN_PDF)
    assert "REFUSED" in reader.read_pages("some-other-artifact", 1, 2)
    assert "REFUSED" in reader.read_pages("tid121-project-plan-2024", 1, 11)
    assert "REFUSED" in reader.read_pages("tid121-project-plan-2024", 0, 2)
    assert "REFUSED" in reader.read_pages("tid121-project-plan-2024", 999, 999)
    page5 = reader.read_pages("tid121-project-plan-2024", 5, 5)
    assert "$700,000" in page5 and "page 5" in page5
    assert reader.calls == 5


def test_routing_runner_sends_roles_to_the_right_runner() -> None:
    class Echo(BaseModel):
        artifact_id: str = "x"

    calls: list[str] = []

    class Recorder:
        def __init__(self, tag: str) -> None:
            self._tag = tag

        async def run(self, definition: AgentDefinition, payload: BaseModel, *, trace_id: str) -> BaseModel:
            calls.append(f"{self._tag}:{definition.role}")
            return payload

    routing = RoleRoutingRunner(
        {"document_evidence": Recorder("adk")}, default=Recorder("fake")
    )
    doc = AgentDefinition(name="d", role="document_evidence", model="m", output_model=Echo, tools=())
    delta = AgentDefinition(name="e", role="delta_investigator", model="m", output_model=Echo, tools=())
    asyncio.run(routing.run(doc, Echo(), trace_id="t"))
    asyncio.run(routing.run(delta, Echo(), trace_id="t"))
    assert calls == ["adk:document_evidence", "fake:delta_investigator"]


def test_usage_log_writes_jsonl(tmp_path: Path) -> None:
    import json

    usage = UsageLog()
    runner = _runner([json.dumps(GOOD_EXTRACTION)], usage)
    asyncio.run(runner.run(DOCUMENT_EVIDENCE_DEFINITION, TASK, trace_id="t4"))
    out = tmp_path / "usage.jsonl"
    usage.write_jsonl(out)
    row = json.loads(out.read_text().splitlines()[0])
    assert set(row) >= {"model", "trace_id", "artifact_id", "latency_ms", "input_tokens", "output_tokens", "tool_calls", "estimated_usd"}
