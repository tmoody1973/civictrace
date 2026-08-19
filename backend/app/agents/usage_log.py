"""Per-model-call usage records. Structured, append-only, never raw page or prompt text."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Vertex list price per 1M tokens for Gemini Flash class models; order-of-magnitude cost
# estimate only — the bill is authoritative. # ponytail: constant, revisit if pricing shifts.
FLASH_USD_PER_1M_INPUT = 0.30
FLASH_USD_PER_1M_OUTPUT = 2.50


@dataclass(frozen=True)
class UsageRecord:
    model: str
    prompt_version: str
    schema_version: str
    trace_id: str
    artifact_id: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    tool_calls: int
    retried: bool

    def estimated_usd(self) -> float:
        return (
            self.input_tokens * FLASH_USD_PER_1M_INPUT
            + self.output_tokens * FLASH_USD_PER_1M_OUTPUT
        ) / 1_000_000


@dataclass
class UsageLog:
    records: list[UsageRecord] = field(default_factory=list)

    def add(self, record: UsageRecord) -> None:
        self.records.append(record)

    def total_estimated_usd(self) -> float:
        return sum(record.estimated_usd() for record in self.records)

    def write_jsonl(self, path: Path) -> None:
        lines = [
            json.dumps({**asdict(record), "estimated_usd": round(record.estimated_usd(), 6)})
            for record in self.records
        ]
        path.write_text("\n".join(lines) + ("\n" if lines else ""))
