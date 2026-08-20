#!/usr/bin/env python3
"""Load the reviewed corpus manifest rows into BigQuery `corpus_artifacts` (MOO-710).

Batch load (free tier), WRITE_TRUNCATE so a re-run replaces the rows — the manifest
file stays the single reviewed source; this table is its queryable copy.

Usage (from backend/, after `terraform apply` created the dataset):
  uv run python scripts/load_corpus_bigquery.py ../docs/sources/corpus-manifest.yaml \
      --project civictrace-dev-tm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.corpus import ManifestArtifact  # noqa: E402
from app.services.bigquery_corpus import CORPUS_TABLE  # noqa: E402
from app.services.corpus import load_corpus_manifest  # noqa: E402


def manifest_rows(entries: list[ManifestArtifact]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": entry.artifact_id,
            "source_id": entry.source_id,
            "role": entry.role,
            "canonical_url": entry.canonical_url,
            "hint_pages": [anchor.page for anchor in entry.required_anchors],
            "content_hash": entry.content_hash,
        }
        for entry in entries
    ]


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    from google.cloud import bigquery

    manifest = load_corpus_manifest(args.manifest)
    rows = manifest_rows(list(manifest.artifacts))
    client = bigquery.Client(project=args.project)
    table_id = f"{args.project}.{args.dataset}.{CORPUS_TABLE}"
    # Explicit schema, identical to Terraform's: without it the load autodetects and
    # relaxes REQUIRED→NULLABLE, Terraform sees drift, and the next apply REPLACES
    # the table (data loss — happened once on 2026-08-20).
    schema = [
        bigquery.SchemaField("artifact_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("canonical_url", "STRING"),
        bigquery.SchemaField("hint_pages", "INTEGER", mode="REPEATED"),
        bigquery.SchemaField("content_hash", "STRING"),
    ]
    job = client.load_table_from_json(
        rows,
        table_id,
        job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    loaded = client.get_table(table_id).num_rows
    print(f"{table_id}: {loaded} rows loaded from {manifest.corpus_id}")
    return 0 if loaded == len(rows) else 1


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--dataset", default="civictrace_dev")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
