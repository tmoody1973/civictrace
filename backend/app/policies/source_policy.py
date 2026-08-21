"""Source allowlist enforcement: adapters retrieve only what source-allowlist.yaml permits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from app.domain.errors import SourcePolicyError
from app.schemas.source import SourceEvent

REQUIRED_SCHEME = "https"


@dataclass(frozen=True)
class SourceRule:
    source_id: str
    domains: frozenset[str]
    content_types: frozenset[str]


class SourcePolicy:
    def __init__(self, rules: dict[str, SourceRule]) -> None:
        self._rules = rules

    @classmethod
    def from_yaml(cls, path: Path) -> SourcePolicy:
        document = yaml.safe_load(path.read_text())
        rules = {
            source["id"]: SourceRule(
                source_id=source["id"],
                domains=frozenset(source["domains"]),
                content_types=frozenset(source["allowed_content_types"]),
            )
            for jurisdiction in document["jurisdictions"].values()
            for source in jurisdiction["sources"]
        }
        return cls(rules)

    def domains_for(self, source_id: str) -> frozenset[str]:
        return self._rule(source_id).domains

    def assert_url_allowed(self, source_id: str, url: str) -> None:
        """Raise SourcePolicyError unless url is HTTPS on an allowlisted domain for source_id."""
        _assert_url_allowed(self._rule(source_id), url)

    def assert_source_event_allowed(self, event: SourceEvent) -> None:
        rule = self._rule(event.source_id)
        if event.canonical_url is not None:
            _assert_url_allowed(rule, event.canonical_url)
        if event.media_type is not None and event.media_type not in rule.content_types:
            raise SourcePolicyError(
                f"content type {event.media_type} is not allowlisted for {rule.source_id}"
            )

    def _rule(self, source_id: str) -> SourceRule:
        try:
            return self._rules[source_id]
        except KeyError as exc:
            raise SourcePolicyError(f"source_id {source_id} is not enrolled") from exc


def _assert_url_allowed(rule: SourceRule, url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != REQUIRED_SCHEME:
        raise SourcePolicyError(f"scheme {parts.scheme!r} is not allowed; use {REQUIRED_SCHEME}")
    if parts.hostname not in rule.domains:
        raise SourcePolicyError(
            f"domain {parts.hostname!r} is not allowlisted for {rule.source_id}"
        )
