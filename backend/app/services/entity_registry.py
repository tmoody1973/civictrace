"""Deterministic entity candidates from case recipes (MOO-720).

The matcher may only see things the system already knows: each case, named by its topic,
with the exact identifier strings a strong match must cite. Never model-generated,
never from the open web.
"""

from __future__ import annotations

import re

from app.schemas.corpus import CorpusManifest
from app.schemas.evidence import EntityCandidate

_TID_PATTERN = re.compile(r"Tax Incremental District No\.?\s*(\d+)|TID\s*(?:No\.?\s*)?(\d+)")
MAX_NAME_CHARS = 160


def entity_candidates_from_manifests(manifests: list[CorpusManifest]) -> list[EntityCandidate]:
    return [_candidate(manifest) for manifest in manifests]


def _candidate(manifest: CorpusManifest) -> EntityCandidate:
    identifiers: set[str] = {manifest.case_id}
    for entry in (*manifest.artifacts, *manifest.media_artifacts):
        if entry.legistar_file:
            identifiers.add(entry.legistar_file)
            identifiers.add(f"File {entry.legistar_file}")
        if entry.legistar_matter_id is not None:
            identifiers.add(str(entry.legistar_matter_id))
    for match in _TID_PATTERN.finditer(manifest.case_topic):
        number = match.group(1) or match.group(2)
        identifiers.add(f"Tax Incremental District No. {number}")
        identifiers.add(f"TID No. {number}")
        identifiers.add(f"TID {number}")
    return EntityCandidate(
        entity_id=manifest.case_id,
        kind="case",
        name=manifest.case_topic.strip()[:MAX_NAME_CHARS],
        identifiers=sorted(identifiers),
    )
