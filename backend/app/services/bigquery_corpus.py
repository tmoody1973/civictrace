"""BigQuery bounded-evidence prefilter (Slice 5.4, MOO-710).

The reviewed corpus rows live in `<project>.<dataset>.corpus_artifacts`. When the
prefilter is enabled the worker asks BigQuery for each event's manifest row before
the workflow runs (no row → the event fails closed), and the agent page hints come
from the same table — the manifest file is no longer the prefilter source in cloud mode.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

CORPUS_TABLE = "corpus_artifacts"


@dataclass(frozen=True)
class CorpusRow:
    """One reviewed artifact's manifest row as stored in BigQuery."""

    artifact_id: str
    source_id: str
    role: str
    canonical_url: str | None
    hint_pages: tuple[int, ...]
    content_hash: str | None


class QueryJob(Protocol):
    def result(self) -> Iterable[Mapping[str, Any]]: ...


class BigQueryClient(Protocol):
    def query(self, query: str, job_config: Any = None) -> QueryJob: ...


class BigQueryCorpusPrefilter:
    def __init__(self, *, client: BigQueryClient, project: str, dataset: str) -> None:
        self._client = client
        self._table = f"`{project}.{dataset}.{CORPUS_TABLE}`"

    def manifest_row(self, artifact_id: str) -> CorpusRow | None:
        """Fetch one artifact's reviewed row; None means the event is not in the corpus."""
        from google.cloud import bigquery

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("artifact_id", "STRING", artifact_id)
            ]
        )
        rows = list(
            self._client.query(
                "SELECT artifact_id, source_id, role, canonical_url, hint_pages, content_hash"
                f" FROM {self._table} WHERE artifact_id = @artifact_id",
                job_config=job_config,
            ).result()
        )
        if not rows:
            return None
        return _to_corpus_row(rows[0])

    def hint_pages(self) -> dict[str, list[int]]:
        """All artifacts' bounded-evidence pages, for the agent service at build time."""
        rows = self._client.query(
            f"SELECT artifact_id, hint_pages FROM {self._table}"
        ).result()
        return {row["artifact_id"]: [int(p) for p in row["hint_pages"]] for row in rows}


def _to_corpus_row(row: Mapping[str, Any]) -> CorpusRow:
    return CorpusRow(
        artifact_id=row["artifact_id"],
        source_id=row["source_id"],
        role=row["role"],
        canonical_url=row["canonical_url"],
        hint_pages=tuple(int(page) for page in row["hint_pages"]),
        content_hash=row["content_hash"],
    )
