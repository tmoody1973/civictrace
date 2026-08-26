"""Word → PDF conversion at intake (MOO-726). LibreOffice headless, injected runner.

Milwaukee publishes some official attachments (fiscal notes, hearing notices) as Word
files. The page-anchor trust chain needs fixed pages, so intake converts Word bytes to
PDF and vaults BOTH: the canonical original stays the provenance root; the clearly
labeled conversion is what the extraction pipeline reads.
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

SOFFICE_TIMEOUT_SECONDS = 120
PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"
# Every legacy Microsoft Office file (.doc, .xls, .ppt) shares this container magic,
# so OLE2 alone cannot prove "Word document" — the URL extension breaks the tie.
OLE2_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_MEDIA_TYPE = "application/msword"


class ConversionError(Exception):
    """The Word file could not become a PDF; the reason is user-showable."""


def classify_attachment(payload: bytes, url: str) -> str:
    """'pdf' | 'word' | 'unsupported', decided from the actual bytes, never the URL alone."""
    if payload.startswith(PDF_MAGIC):
        return "pdf"
    if payload.startswith(ZIP_MAGIC) and _zip_holds_word_document(payload):
        return "word"
    if payload.startswith(OLE2_MAGIC) and _url_path(url).endswith(".doc"):
        return "word"
    return "unsupported"


def word_media_type(payload: bytes) -> str:
    return DOCX_MEDIA_TYPE if payload.startswith(ZIP_MAGIC) else DOC_MEDIA_TYPE


def word_suffix(payload: bytes) -> str:
    return ".docx" if payload.startswith(ZIP_MAGIC) else ".doc"


def convert_word_to_pdf(
    payload: bytes,
    *,
    run: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> bytes:
    """Run LibreOffice headless over the exact fetched bytes; return the PDF bytes."""
    with tempfile.TemporaryDirectory(prefix="civictrace-convert-") as workdir:
        source = Path(workdir) / f"original{word_suffix(payload)}"
        source.write_bytes(payload)
        command = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            workdir,
            str(source),
        ]
        try:
            result = run(command, capture_output=True, timeout=SOFFICE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(
                "converting the Word document to PDF took too long and was stopped"
            ) from exc
        except FileNotFoundError as exc:
            raise ConversionError(
                "the PDF converter (LibreOffice) is not installed on this server"
            ) from exc
        produced = source.with_suffix(".pdf")
        if result.returncode != 0 or not produced.exists():
            raise ConversionError(
                "the Word document could not be converted to PDF; the file may be "
                "damaged or use features the converter does not support"
            )
        converted = produced.read_bytes()
        if not converted.startswith(PDF_MAGIC):
            raise ConversionError("the converter produced something that is not a PDF")
        return converted


def _zip_holds_word_document(payload: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            return any(name.startswith("word/") for name in archive.namelist())
    except zipfile.BadZipFile:
        return False


def _url_path(url: str) -> str:
    return url.lower().split("?", 1)[0]
