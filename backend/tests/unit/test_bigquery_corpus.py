"""BigQuery corpus prefilter: fake client, no network (Slice 5.4, MOO-710)."""

from __future__ import annotations

from typing import Any

from app.services.bigquery_corpus import BigQueryCorpusPrefilter

_ROW = {
    "artifact_id": "tid121-project-plan-2024",
    "source_id": "milwaukee_legistar",
    "role": "original_commitment",
    "canonical_url": "https://example.test/plan.pdf",
    "hint_pages": [2, 5, 6],
    "content_hash": "sha256:abc",
}


class FakeQueryJob:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def result(self) -> list[dict[str, Any]]:
        return self._rows


class FakeBigQueryClient:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.queries: list[str] = []

    def query(self, query: str, job_config: Any = None) -> FakeQueryJob:
        self.queries.append(query)
        if "WHERE artifact_id" in query:
            wanted = job_config.query_parameters[0].value
            return FakeQueryJob([r for r in self._rows if r["artifact_id"] == wanted])
        return FakeQueryJob(self._rows)


def _prefilter(rows: list[dict[str, Any]]) -> tuple[BigQueryCorpusPrefilter, FakeBigQueryClient]:
    client = FakeBigQueryClient(rows)
    return (
        BigQueryCorpusPrefilter(client=client, project="proj", dataset="civictrace_dev"),
        client,
    )


def test_manifest_row_returns_typed_row_for_known_artifact() -> None:
    prefilter, client = _prefilter([_ROW])
    row = prefilter.manifest_row("tid121-project-plan-2024")
    assert row is not None
    assert row.role == "original_commitment"
    assert row.hint_pages == (2, 5, 6)
    assert "`proj.civictrace_dev.corpus_artifacts`" in client.queries[0]


def test_manifest_row_returns_none_for_unknown_artifact() -> None:
    prefilter, _ = _prefilter([_ROW])
    assert prefilter.manifest_row("not-in-corpus") is None


def test_hint_pages_maps_every_artifact() -> None:
    other = dict(_ROW, artifact_id="tid121-amendment-1-2026", hint_pages=[3])
    prefilter, _ = _prefilter([_ROW, other])
    assert prefilter.hint_pages() == {
        "tid121-project-plan-2024": [2, 5, 6],
        "tid121-amendment-1-2026": [3],
    }
