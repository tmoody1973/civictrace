"""Route each agent role to its runner: the real model where an issue has earned it,
the fixture fake everywhere else. MOO-691 routes only document_evidence to ADK."""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.factory import AgentDefinition, StructuredAgentRunner


class RoleRoutingRunner:
    def __init__(
        self,
        by_role: dict[str, StructuredAgentRunner],
        *,
        default: StructuredAgentRunner,
    ) -> None:
        self._by_role = dict(by_role)
        self._default = default

    async def run(
        self, definition: AgentDefinition, payload: BaseModel, *, trace_id: str
    ) -> BaseModel:
        runner = self._by_role.get(definition.role, self._default)
        return await runner.run(definition, payload, trace_id=trace_id)
