"""Live canonical-source retrieval (MOO-714): the vault fetches the official bytes.

Product rule #7: CivicTrace independently retrieves and preserves the canonical public
source artifact. The fetcher only touches allowlisted HTTPS domains and refuses any
response whose bytes do not match the reviewed manifest hash — a silently-changed
document never becomes evidence.
"""

from __future__ import annotations

import urllib.request
from collections.abc import Callable

from app.policies.source_policy import SourcePolicy
from app.schemas.corpus import ManifestArtifact
from app.services.artifact_vault import HASH_PREFIX, sha256_hex

FETCH_TIMEOUT_SECONDS = 60
USER_AGENT = "CivicTrace/0.1 (public-records research; read-only)"


class LiveFetchError(Exception):
    """The canonical source could not be retrieved as reviewed evidence."""


def _default_http_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:  # noqa: S310
        return bytes(response.read())


class LiveSourceFetcher:
    """Fetch one reviewed artifact's bytes from its canonical allowlisted URL."""

    def __init__(
        self,
        *,
        source_policy: SourcePolicy,
        http_get: Callable[[str], bytes] = _default_http_get,
    ) -> None:
        self._policy = source_policy
        self._http_get = http_get

    def fetch(self, entry: ManifestArtifact) -> bytes:
        if entry.canonical_url is None or entry.content_hash is None:
            raise LiveFetchError(f"{entry.artifact_id}: no canonical_url/hash to fetch against")
        self._assert_allowlisted(entry)
        payload = self._http_get(entry.canonical_url)
        if HASH_PREFIX + sha256_hex(payload) != entry.content_hash:
            raise LiveFetchError(
                f"{entry.artifact_id}: live bytes from {entry.canonical_url} do not match the "
                "reviewed manifest hash; refusing changed or tampered content"
            )
        return payload

    def _assert_allowlisted(self, entry: ManifestArtifact) -> None:
        from app.domain.errors import SourcePolicyError

        try:
            assert entry.canonical_url is not None
            self._policy.assert_url_allowed(entry.source_id, entry.canonical_url)
        except SourcePolicyError as exc:
            raise LiveFetchError(f"{entry.artifact_id}: {exc}") from exc
