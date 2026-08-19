"""Google ADK integration outline for CivicTrace.

Verify exact imports, model identifiers, schema parameters, and runner calls against the
installed ADK release before implementing. Keep ADK-specific code confined to this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from app.agents.prompts import PROMPT_VERSION, build_instruction

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


class GoogleAdkStructuredRunner:
    """Pseudocode adapter for current Google ADK APIs.

    Required production properties:
    - Vertex AI / Cloud Run service-identity authentication;
    - Gemini Flash default model;
    - global policy plus role-specific instruction from `build_instruction`;
    - strict Pydantic/JSON output schema;
    - only the definition's read-only tools;
    - trace/model/prompt-version metadata sent to observability;
    - parsed output returned for deterministic validation.
    """

    def __init__(self, *, adk_runtime: Any, observability: Any) -> None:
        self._adk_runtime = adk_runtime
        self._observability = observability

    async def run(
        self,
        definition: AgentDefinition,
        payload: BaseModel,
        *,
        trace_id: str,
    ) -> BaseModel:
        instruction = build_instruction(definition.role)

        # PSEUDOCODE — adapt to installed google-adk release:
        # adk_agent = Agent(
        #     name=definition.name,
        #     model=definition.model,
        #     instruction=instruction,
        #     tools=list(definition.tools),
        #     output_schema=definition.output_model.model_json_schema(),
        # )
        # raw_result = await self._adk_runtime.run(
        #     agent=adk_agent,
        #     input=payload.model_dump(mode="json"),
        #     trace_id=trace_id,
        # )
        # result = definition.output_model.model_validate_json(raw_result.text)

        raise NotImplementedError(
            "Implement against the installed Google ADK release. Do not bypass the "
            "typed output parse, read-only tool boundary, or observability hook."
        )
