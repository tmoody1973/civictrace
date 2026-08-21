"""MOO-720: the candidate-versus-confirmed gate (required demo behavior #5) and the
deterministic entity registry. A model may propose CONFIRMED; only code lets it stand."""

from __future__ import annotations

from app.domain.enums import (
    AnchorType,
    EvidenceObjectType,
    EvidenceStatus,
    LinkStatus,
)
from app.schemas.evidence import (
    DocumentExtraction,
    EntityCandidate,
    EntityLink,
    EntityLinkBatch,
    Evidence,
    EvidenceAnchor,
)
from app.services.corpus import load_corpus_manifest
from app.services.entity_registry import entity_candidates_from_manifests
from app.services.validator import sanitize_entity_links
from tests.conftest import MANIFEST_PATH


def _evidence(evidence_id: str, text: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        artifact_id="art-1",
        object_type=EvidenceObjectType.CLAIM,
        verbatim_excerpt=text,
        neutral_statement="The record states this.",
        anchors=[
            EvidenceAnchor(artifact_id="art-1", anchor_type=AnchorType.PAGE, anchor_value="1")
        ],
        status=EvidenceStatus.SUPPORTED,
    )


def _extraction(*evidence: Evidence) -> DocumentExtraction:
    return DocumentExtraction(
        artifact_id="art-1", agent_name="test", agent_version="test", evidence=list(evidence)
    )


CANDIDATE_CASE = EntityCandidate(
    entity_id="case-tid121",
    kind="case",
    name="TID 121 (Bronzeville Arts & Tech Hub)",
    identifiers=["240382", "Tax Incremental District No. 121", "TID 121"],
)


def _link(status: LinkStatus, evidence_id: str = "ev-1") -> EntityLink:
    return EntityLink(
        evidence_id=evidence_id,
        entity_id="case-tid121",
        link_status=status,
        rationale="agent rationale",
    )


class TestCandidateVersusConfirmedGate:
    def test_confirmed_with_exact_identifier_in_evidence_stands(self) -> None:
        extraction = _extraction(_evidence("ev-1", "amending Tax Incremental District No. 121"))
        batch = sanitize_entity_links(
            EntityLinkBatch(links=[_link(LinkStatus.CONFIRMED)]), extraction, [CANDIDATE_CASE]
        )
        assert batch.links[0].link_status is LinkStatus.CONFIRMED

    def test_confirmed_without_identifier_is_demoted_to_candidate(self) -> None:
        extraction = _extraction(_evidence("ev-1", "a mixed-use arts project in Bronzeville"))
        batch = sanitize_entity_links(
            EntityLinkBatch(links=[_link(LinkStatus.CONFIRMED)]), extraction, [CANDIDATE_CASE]
        )
        assert batch.links[0].link_status is LinkStatus.CANDIDATE
        assert "demoted" in batch.links[0].rationale

    def test_candidate_is_never_promoted(self) -> None:
        extraction = _extraction(_evidence("ev-1", "amending Tax Incremental District No. 121"))
        batch = sanitize_entity_links(
            EntityLinkBatch(links=[_link(LinkStatus.CANDIDATE)]), extraction, [CANDIDATE_CASE]
        )
        assert batch.links[0].link_status is LinkStatus.CANDIDATE

    def test_invented_evidence_or_entity_ids_are_dropped(self) -> None:
        extraction = _extraction(_evidence("ev-1", "any text"))
        invented_evidence = _link(LinkStatus.CONFIRMED, evidence_id="ev-999")
        invented_entity = EntityLink(
            evidence_id="ev-1", entity_id="case-made-up",
            link_status=LinkStatus.CONFIRMED, rationale="x",
        )
        batch = sanitize_entity_links(
            EntityLinkBatch(links=[invented_evidence, invented_entity]),
            extraction,
            [CANDIDATE_CASE],
        )
        assert batch.links == []


def test_registry_candidates_carry_exact_identifiers_from_the_manifest() -> None:
    manifest = load_corpus_manifest(MANIFEST_PATH)
    [candidate] = entity_candidates_from_manifests([manifest])
    assert candidate.entity_id == manifest.case_id
    assert "240382" in candidate.identifiers  # the project plan's Legistar file
    assert "Tax Incremental District No. 121" in candidate.identifiers
    assert candidate.kind == "case"
