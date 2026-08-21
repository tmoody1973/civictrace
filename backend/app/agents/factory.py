"""Google ADK integration outline for CivicTrace.

Verify exact imports, model identifiers, schema parameters, and runner calls against the
installed ADK release before implementing. Keep ADK-specific code confined to this module.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.agents.prompts import PROMPT_VERSION, build_instruction
from app.agents.usage_log import UsageRecord

logger = logging.getLogger("civictrace.agents")

T = TypeVar("T", bound=BaseModel)


class ReadOnlyTool(Protocol):
    """Marker protocol for a bounded ADK tool.

    CivicTrace tools can read a supplied artifact window, a case bundle, a precomputed
    entity candidate list, or a correction set. They never write Firestore, send mail,
    browse the open web, or execute a shell command.
    """

    name: str


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    role: str
    model: str
    output_model: type[BaseModel]
    tools: tuple[ReadOnlyTool, ...]
    prompt_version: str = PROMPT_VERSION


class StructuredAgentRunner(Protocol):
    async def run(
        self,
        definition: AgentDefinition,
        payload: BaseModel,
        *,
        trace_id: str,
    ) -> BaseModel: ...


class CivicTraceAgentFactory:
    """Creates agent definitions; no business workflow or data mutation lives here."""

    # Latest GA Flash (2026-08-19). Gemini 3.x is served only from Vertex location "global".
    DEFAULT_MODEL = "gemini-3.7-flash"

    def __init__(
        self,
        *,
        artifact_reader: ReadOnlyTool,
        transcript_reader: ReadOnlyTool,
        case_bundle_reader: ReadOnlyTool,
        candidate_entity_reader: ReadOnlyTool,
        correction_reader: ReadOnlyTool,
    ) -> None:
        self._artifact_reader = artifact_reader
        self._transcript_reader = transcript_reader
        self._case_bundle_reader = case_bundle_reader
        self._candidate_entity_reader = candidate_entity_reader
        self._correction_reader = correction_reader

    def definition(self, role: str, output_model: type[T]) -> AgentDefinition:
        tools_by_role: dict[str, tuple[ReadOnlyTool, ...]] = {
            "orchestration_classifier": (self._artifact_reader,),
            "document_evidence": (self._artifact_reader, self._candidate_entity_reader),
            "media_evidence": (self._transcript_reader,),
            "entity_resolution": (self._candidate_entity_reader, self._correction_reader),
            "case_linker": (self._case_bundle_reader, self._correction_reader),
            "delta_investigator": (self._case_bundle_reader,),
            "quality_reviewer": (self._case_bundle_reader,),
            "inquiry_planner": (self._case_bundle_reader,),
            "brief_builder": (self._case_bundle_reader,),
        }
        return AgentDefinition(
            name=f"civictrace-{role}",
            role=role,
            model=self.DEFAULT_MODEL,
            output_model=output_model,
            tools=tools_by_role[role],
        )


class AgentOutputError(RuntimeError):
    """The model's final answer never became a schema-valid object (after one logged retry)."""


class GoogleAdkStructuredRunner:
    """Runs one bounded ADK agent per call on Gemini Flash via Vertex AI (ADC, no key file).

    Boundary properties, enforced here and testable with a stubbed run function:
    - instruction = versioned `build_instruction(role)`;
    - `output_schema` = the definition's pydantic model (ADK adds set_model_response);
    - tools = ONLY the single-artifact page reader supplied by `page_reader_factory`;
    - malformed output → one logged retry → typed AgentOutputError;
    - every call appends a UsageRecord (never raw page/prompt text).
    """

    def __init__(
        self,
        *,
        model: str,
        page_reader_factory: Callable[[str], Any],
        usage_log: Any,
        transcript_reader_factory: Callable[[str], Any] | None = None,
        run_agent: Callable[..., Awaitable[tuple[str, dict[str, int]]]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._model = model
        self._page_reader_factory = page_reader_factory
        self._transcript_reader_factory = transcript_reader_factory
        self._usage_log = usage_log
        self._run_agent = run_agent or _run_adk_agent
        self._clock = clock

    async def run(
        self,
        definition: AgentDefinition,
        payload: BaseModel,
        *,
        trace_id: str,
    ) -> BaseModel:
        artifact_id = getattr(payload, "artifact_id", "") or getattr(
            payload, "trigger_artifact_id", ""
        )
        task_json = payload.model_dump_json()
        if definition.role == "document_evidence":
            # Only the extraction roles get a read tool; every other role reasons over the
            # already-validated evidence in its task payload — no tools, no browsing.
            reader = self._page_reader_factory(artifact_id)
            tools: list[Any] = [reader.read_pages]
            message = (
                f"Task input (JSON):\n{task_json}\n\n"
                "Read the artifact with your read_pages tool before extracting anything. "
                "hint_pages are suggestions from the corpus manifest, not answers. "
                "Read every hint page; when a hint page contains extractable content, anchor at "
                "least one evidence object to that exact page. If an official form field on a page "
                "you read is present but blank (for example a status field with no value), record "
                "that as an evidence object with status UNKNOWN quoting the field label."
            )
        elif definition.role == "media_evidence":
            if self._transcript_reader_factory is None:
                raise ValueError(f"{artifact_id}: media_evidence has no transcript reader")
            reader = self._transcript_reader_factory(artifact_id)
            tools = [reader.read_transcript_span]
            message = (
                f"Task input (JSON):\n{task_json}\n\n"
                "Read the transcript with your read_transcript_span tool before extracting "
                "anything; times are 0-based milliseconds within the transcribed segment and "
                f"the segment ends at {reader.duration_ms} ms. Copy anchor bounds exactly from "
                "the [start-end ms] markers of the lines you quote."
            )
        else:
            reader = None
            tools = []
            message = (
                f"Task input (JSON):\n{task_json}\n\n"
                "Use ONLY the evidence and fields in the task input above. "
                "Return ONLY the JSON output object required by your instructions."
            )
        last_error: Exception | None = None
        for attempt in (1, 2):  # exactly one retry on malformed output
            started = self._clock()
            text, usage = await self._run_agent(
                model=self._model,
                name=definition.name,
                instruction=build_instruction(definition.role),
                output_model=definition.output_model,
                tools=tools,
                message=message,
            )
            latency_ms = int((self._clock() - started) * 1000)
            self._usage_log.add(
                UsageRecord(
                    model=self._model,
                    prompt_version=definition.prompt_version,
                    schema_version=definition.output_model.__name__,
                    trace_id=trace_id,
                    artifact_id=artifact_id,
                    latency_ms=latency_ms,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    tool_calls=getattr(reader, "calls", 0) if reader is not None else 0,
                    retried=attempt == 2,
                )
            )
            try:
                return definition.output_model.model_validate_json(_strip_fences(text))
            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "agent output failed schema validation",
                    extra={"trace_id": trace_id, "artifact_id": artifact_id, "attempt": attempt},
                )
        raise AgentOutputError(
            f"{definition.name}: output for {artifact_id!r} failed "
            f"{definition.output_model.__name__} validation after retry"
        ) from last_error


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


async def _run_adk_agent(
    *,
    model: str,
    name: str,
    instruction: str,
    output_model: type[BaseModel],
    tools: list[Any],
    message: str,
) -> tuple[str, dict[str, int]]:
    """One ADK invocation → (final response text, token usage). Verified on google-adk 2.7.1."""
    from google.adk.agents import Agent  # noqa: PLC0415  (heavy import, adk path only)
    from google.adk.runners import InMemoryRunner  # noqa: PLC0415
    from google.genai import types  # noqa: PLC0415

    agent = Agent(
        name=name.replace("-", "_"),
        model=model,
        instruction=instruction,
        tools=tools,
        output_schema=output_model,
    )
    runner = InMemoryRunner(agent=agent, app_name="civictrace")
    session = await runner.session_service.create_session(app_name="civictrace", user_id="replay")
    text = ""
    usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
    async for event in runner.run_async(
        user_id="replay",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)]),
    ):
        metadata = getattr(event, "usage_metadata", None)
        if metadata is not None:
            usage["input_tokens"] += getattr(metadata, "prompt_token_count", 0) or 0
            usage["output_tokens"] += getattr(metadata, "candidates_token_count", 0) or 0
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(part.text or "" for part in event.content.parts)
    return text, usage
