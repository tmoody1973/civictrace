"""Load the reviewed replay-corpus manifest from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.corpus import CorpusManifest


def load_corpus_manifest(path: Path) -> CorpusManifest:
    return CorpusManifest.model_validate(yaml.safe_load(path.read_text()))
