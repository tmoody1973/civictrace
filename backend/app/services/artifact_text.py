"""Page-text access for stored artifacts, used only to check that quoted words exist on the page."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from pathlib import Path
from typing import overload

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)

_IGNORED = re.compile(r"[\s$]+")


def normalise_for_match(text: str) -> str:
    """Compare words and digits in order; ignore whitespace and currency symbols.

    Different PDF text extractors place table '$' signs differently; the words do not move.
    """
    return _IGNORED.sub("", text)


class LazyPdfPages(Sequence[str]):
    """Extracts a page only when asked for: a 164-page report costs 2 page reads, not 164."""

    def __init__(self, path: Path) -> None:
        self._reader = PdfReader(path)
        self._cache: dict[int, str] = {}

    def __len__(self) -> int:
        return len(self._reader.pages)

    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...
    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if index < 0:
            index += len(self)
        if index not in self._cache:
            self._cache[index] = self._reader.pages[index].extract_text() or ""
        return self._cache[index]


def read_page_texts(storage_uri: str, media_type: str | None) -> Sequence[str] | None:
    path = Path(storage_uri.removeprefix("file://"))
    if media_type == "application/pdf":
        return LazyPdfPages(path)
    if media_type == "text/html":
        return [path.read_text(errors="replace")]
    return None
