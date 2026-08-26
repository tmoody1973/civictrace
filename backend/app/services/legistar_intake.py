"""Legistar Web API intake lookups (MOO-719). Read-only, allowlisted, injected transport.

Gotchas inherited from Gavel's shipped client (docs/research/gavel-learnings.md §2):
Milwaukee needs no API key; matter titles can be terse; every list endpoint caps at
1,000 rows. One file-number lookup fetches at most two small JSON pages.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

from app.schemas.intake import CandidateAttachment, CandidateBundle, MatterSearchResult

LEGISTAR_BASE = "https://webapi.legistar.com/v1/milwaukee"
FETCH_TIMEOUT_SECONDS = 30
USER_AGENT = "CivicTrace/0.1 (public-records research; read-only)"
FILE_NUMBER_PATTERN = re.compile(r"^\d{6}$")

# Words too common in matter titles to narrow anything; dropped before searching.
SEARCH_STOPWORDS = frozenset(
    "the a an of and or for to in on at by with from relating regarding resolution "
    "ordinance substitute city milwaukee file".split()
)
MAX_SEARCH_WORDS = 5
SEARCH_RESULT_LIMIT = 20


class IntakeLookupError(Exception):
    """The official record could not be retrieved or does not list this file."""


def _default_get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:  # noqa: S310
        return json.loads(response.read())


class LegistarIntakeClient:
    """File number → what the official Legistar record lists for that matter."""

    def __init__(self, *, get_json: Callable[[str], Any] = _default_get_json) -> None:
        self._get_json = get_json

    def candidate_bundle(
        self, file_number: str, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)
    ) -> CandidateBundle:
        file_number = file_number.strip()
        if not FILE_NUMBER_PATTERN.match(file_number):
            raise IntakeLookupError(
                f"{file_number!r} is not a Milwaukee Legistar file number (six digits, e.g. 260433)"
            )
        matter = self._matter_by_file(file_number)
        matter_id = int(matter["MatterId"])
        attachments = self._attachments(matter_id)
        retrieved_at = now()
        return CandidateBundle(
            bundle_id=f"bundle-{file_number}-{retrieved_at.strftime('%Y%m%d%H%M%S')}",
            legistar_file=file_number,
            matter_id=matter_id,
            title=_title(matter),
            matter_type=matter.get("MatterTypeName"),
            matter_status=matter.get("MatterStatusName"),
            intro_date=_date(matter.get("MatterIntroDate")),
            matter_url=f"{LEGISTAR_BASE}/matters/{matter_id}",
            attachments=attachments,
            retrieved_at=retrieved_at,
        )

    def search_matters(self, query: str) -> list[MatterSearchResult]:
        """Plain words → matters from the official record, newest first (MOO-749).

        This is word search over official titles (Legistar's substringof is
        case-insensitive in practice — probed live 2026-08-26), not meaning search.
        A six-digit query is treated as a file number directly.
        """
        query = query.strip()
        if FILE_NUMBER_PATTERN.match(query):
            rows = self._get_json(
                f"{LEGISTAR_BASE}/matters?$filter="
                + urllib.parse.quote(f"MatterFile eq '{query}'")
            )
            return [_search_result(row) for row in rows if isinstance(rows, list)]
        words = _search_words(query)
        if not words:
            raise IntakeLookupError(
                "give me a word or two to search for — a project name, a place, a program "
                "(for example: Amani homeownership) — or a six-digit file number"
            )
        per_word = [
            f"(substringof('{word}',MatterTitle) or substringof('{word}',MatterName))"
            for word in words
        ]
        filter_query = urllib.parse.quote(" and ".join(per_word))
        rows = self._get_json(
            f"{LEGISTAR_BASE}/matters?$filter={filter_query}"
            f"&$orderby=MatterIntroDate desc&$top={SEARCH_RESULT_LIMIT}".replace(" ", "%20")
        )
        return [_search_result(row) for row in rows] if isinstance(rows, list) else []

    def _matter_by_file(self, file_number: str) -> dict[str, Any]:
        query = urllib.parse.quote(f"MatterFile eq '{file_number}'")
        rows = self._get_json(f"{LEGISTAR_BASE}/matters?$filter={query}")
        if not isinstance(rows, list) or not rows:
            raise IntakeLookupError(
                f"the official Legistar record lists no matter with file number {file_number}"
            )
        return dict(rows[0])

    def _attachments(self, matter_id: int) -> list[CandidateAttachment]:
        rows = self._get_json(f"{LEGISTAR_BASE}/matters/{matter_id}/attachments")
        items = []
        for row in rows if isinstance(rows, list) else []:
            url = row.get("MatterAttachmentHyperlink") or ""
            if not url.startswith("https://"):
                continue  # never offer a non-HTTPS or empty link as candidate evidence
            items.append(
                CandidateAttachment(
                    attachment_id=int(row["MatterAttachmentId"]),
                    name=row.get("MatterAttachmentName")
                    or f"Attachment {row['MatterAttachmentId']}",
                    url=url,
                )
            )
        return items


def _search_words(query: str) -> list[str]:
    words = []
    for raw in re.findall(r"[A-Za-z0-9]+", query):
        word = raw.strip()
        if len(word) < 3 or word.lower() in SEARCH_STOPWORDS:
            continue
        words.append(word.replace("'", "''"))
        if len(words) == MAX_SEARCH_WORDS:
            break
    return words


def _search_result(row: dict[str, Any]) -> MatterSearchResult:
    return MatterSearchResult(
        legistar_file=str(row.get("MatterFile") or ""),
        matter_id=int(row["MatterId"]),
        title=_title(row),
        matter_type=row.get("MatterTypeName"),
        matter_status=row.get("MatterStatusName"),
        intro_date=_date(row.get("MatterIntroDate")),
    )


def _title(matter: dict[str, Any]) -> str:
    # Matter titles can be terse ("File 230045"); prefer the fuller of Title/Name.
    title = matter.get("MatterTitle") or ""
    name = matter.get("MatterName") or ""
    return max((title, name), key=len) or f"File {matter.get('MatterFile', '?')}"


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None
