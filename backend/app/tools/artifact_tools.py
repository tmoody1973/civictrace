"""The Document Evidence Agent's only tool: read pages of ONE vaulted artifact.

The tool object is bound to a single artifact id and file path at construction time by
deterministic code. The model cannot name another artifact, a URL, or a path — a wrong id
gets a refusal string, never bytes. Reads are capped at MAX_PAGES_PER_CALL per call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.artifact_text import LazyPdfPages

MAX_PAGES_PER_CALL = 10


@dataclass
class ArtifactPageReader:
    """Read-only, single-artifact page reader. `name` satisfies the ReadOnlyTool protocol."""

    artifact_id: str
    pdf_path: Path
    name: str = "read_artifact_pages"
    calls: int = field(default=0)

    def __post_init__(self) -> None:
        self._pages = LazyPdfPages(self.pdf_path)

    @property
    def page_count(self) -> int:
        return len(self._pages)

    def read_pages(self, artifact_id: str, first_page: int, last_page: int) -> str:
        """Return the text of pages first_page..last_page (1-based, inclusive) of the artifact.

        Args:
            artifact_id: must be the artifact this task is about; any other id is refused.
            first_page: first 1-based page number to read.
            last_page: last 1-based page number to read; at most 10 pages per call.
        """
        self.calls += 1
        if artifact_id != self.artifact_id:
            return (
                f"REFUSED: this task may only read artifact {self.artifact_id!r}; "
                f"{artifact_id!r} is outside its boundary."
            )
        if first_page < 1 or last_page < first_page:
            return "REFUSED: pages are 1-based and last_page must be >= first_page."
        if last_page - first_page + 1 > MAX_PAGES_PER_CALL:
            return f"REFUSED: at most {MAX_PAGES_PER_CALL} pages per call; narrow the range."
        total = len(self._pages)
        if first_page > total:
            return f"REFUSED: the document has {total} pages; page {first_page} does not exist."
        last_page = min(last_page, total)
        chunks = [
            f"--- {self.artifact_id} page {number} ---\n{self._pages[number - 1]}"
            for number in range(first_page, last_page + 1)
        ]
        return "\n\n".join(chunks)
