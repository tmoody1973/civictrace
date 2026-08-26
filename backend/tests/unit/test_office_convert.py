"""MOO-726: Word detection by bytes and the LibreOffice conversion contract."""

from __future__ import annotations

import io
import subprocess
import zipfile
from pathlib import Path

import pytest

from app.services.office_convert import (
    ConversionError,
    classify_attachment,
    convert_word_to_pdf,
    word_media_type,
)

DOC_URL = "https://milwaukee.legistar1.com/milwaukee/attachments/notice.doc"
XLS_URL = "https://milwaukee.legistar1.com/milwaukee/attachments/budget.xls"
OLE2 = bytes.fromhex("D0CF11E0A1B11AE1") + b"rest-of-legacy-office-container"


def _docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


def test_pdf_bytes_classify_as_pdf() -> None:
    assert classify_attachment(b"%PDF-1.7 payload", DOC_URL) == "pdf"


def test_docx_bytes_classify_as_word_regardless_of_url() -> None:
    assert classify_attachment(_docx_bytes(), "https://example.gov/mislabeled.pdf") == "word"


def test_legacy_doc_needs_the_doc_extension_to_break_the_ole2_tie() -> None:
    assert classify_attachment(OLE2, DOC_URL) == "word"
    assert classify_attachment(OLE2, XLS_URL) == "unsupported"


def test_html_and_plain_zip_are_unsupported() -> None:
    assert classify_attachment(b"<html>error page</html>", DOC_URL) == "unsupported"
    plain_zip = io.BytesIO()
    with zipfile.ZipFile(plain_zip, "w") as archive:
        archive.writestr("data.csv", "a,b")
    assert classify_attachment(plain_zip.getvalue(), DOC_URL) == "unsupported"


def test_word_media_type_tracks_the_container() -> None:
    assert word_media_type(_docx_bytes()).endswith("wordprocessingml.document")
    assert word_media_type(OLE2) == "application/msword"


def _fake_run(pdf_bytes: bytes | None, returncode: int = 0):
    """Stand-in for subprocess.run: writes the 'converted' PDF next to the source."""

    def run(command, **kwargs):
        assert command[0] == "soffice" and "--headless" in command
        source = Path(command[-1])
        if pdf_bytes is not None:
            source.with_suffix(".pdf").write_bytes(pdf_bytes)
        return subprocess.CompletedProcess(command, returncode, b"", b"")

    return run


def test_convert_returns_the_produced_pdf_bytes() -> None:
    assert convert_word_to_pdf(_docx_bytes(), run=_fake_run(b"%PDF-1.7 converted")) == (
        b"%PDF-1.7 converted"
    )


def test_convert_refuses_when_soffice_fails() -> None:
    with pytest.raises(ConversionError, match="could not be converted"):
        convert_word_to_pdf(_docx_bytes(), run=_fake_run(None, returncode=1))


def test_convert_refuses_when_no_output_appears() -> None:
    with pytest.raises(ConversionError, match="could not be converted"):
        convert_word_to_pdf(_docx_bytes(), run=_fake_run(None, returncode=0))


def test_convert_refuses_non_pdf_output() -> None:
    with pytest.raises(ConversionError, match="not a PDF"):
        convert_word_to_pdf(_docx_bytes(), run=_fake_run(b"<html>oops</html>"))


def test_convert_refuses_when_libreoffice_is_missing() -> None:
    def run(command, **kwargs):
        raise FileNotFoundError("soffice")

    with pytest.raises(ConversionError, match="not installed"):
        convert_word_to_pdf(_docx_bytes(), run=run)
