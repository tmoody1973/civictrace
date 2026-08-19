"""Only allowlisted official sources may be retrieved. Everything else fails closed."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.errors import SourcePolicyError
from app.policies.source_policy import SourcePolicy
from app.schemas.source import SourceEvent
from tests.conftest import ALLOWLIST_PATH

LEGISTAR_PDF = "https://milwaukee.legistar1.com/milwaukee/attachments/5fe0f830.pdf"


@pytest.fixture(scope="module")
def policy() -> SourcePolicy:
    return SourcePolicy.from_yaml(ALLOWLIST_PATH)


def _event(**overrides: object) -> SourceEvent:
    base = {
        "source_event_id": "evt-1",
        "source_id": "milwaukee_legistar",
        "jurisdiction": "milwaukee_city",
        "artifact_id": "tid121-project-plan-2024",
        "external_id": "240382/attachment/223678",
        "canonical_url": LEGISTAR_PDF,
        "media_type": "application/pdf",
        "content_hash": "sha256:7097a1ba",
        "observed_at": datetime(2026, 8, 19, tzinfo=UTC),
    }
    return SourceEvent.model_validate({**base, **overrides})


def test_allowlisted_legistar_pdf_passes(policy: SourcePolicy) -> None:
    policy.assert_source_event_allowed(_event())


def test_attachment_host_legistar1_is_allowlisted(policy: SourcePolicy) -> None:
    assert "milwaukee.legistar1.com" in policy.domains_for("milwaukee_legistar")


def test_unknown_domain_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="domain"):
        policy.assert_source_event_allowed(
            _event(canonical_url="https://evil.example.com/milwaukee/attachments/x.pdf")
        )


def test_plain_http_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="scheme"):
        policy.assert_source_event_allowed(
            _event(canonical_url=LEGISTAR_PDF.replace("https", "http"))
        )


def test_disallowed_content_type_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="content type"):
        policy.assert_source_event_allowed(_event(media_type="application/msword"))


def test_unknown_source_id_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="source_id"):
        policy.assert_source_event_allowed(_event(source_id="mps_board"))


def test_lookalike_domain_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="domain"):
        policy.assert_source_event_allowed(
            _event(canonical_url="https://milwaukee.legistar1.com.evil.example/x.pdf")
        )


def test_expected_but_absent_record_without_url_passes_for_enrolled_source(
    policy: SourcePolicy,
) -> None:
    policy.assert_source_event_allowed(
        _event(
            artifact_id="tid-annual-report-2025",
            external_id="expected:annual-tid-report-2025",
            canonical_url=None,
            media_type=None,
            content_hash=None,
        )
    )


def test_userinfo_trick_is_rejected(policy: SourcePolicy) -> None:
    # "host@" is userinfo; the real host is the part after "@".
    with pytest.raises(SourcePolicyError, match="domain"):
        policy.assert_source_event_allowed(
            _event(canonical_url="https://milwaukee.legistar1.com@evil.example/x.pdf")
        )


def test_subdomain_of_allowlisted_host_is_rejected(policy: SourcePolicy) -> None:
    with pytest.raises(SourcePolicyError, match="domain"):
        policy.assert_source_event_allowed(
            _event(canonical_url="https://cdn.milwaukee.legistar1.com/x.pdf")
        )


def test_uppercase_host_is_normalised_and_allowed(policy: SourcePolicy) -> None:
    policy.assert_source_event_allowed(
        _event(canonical_url="https://MILWAUKEE.LEGISTAR1.COM/milwaukee/attachments/x.pdf")
    )
