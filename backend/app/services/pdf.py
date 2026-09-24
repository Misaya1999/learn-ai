import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(ValueError):
    pass


class NoExtractableTextError(PDFExtractionError):
    pass


def normalize_extracted_text(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        normalized = re.sub(r"[\t\f\v ]+", " ", line).strip()
        lines.append(normalized)
    normalized_text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized_text).strip()


def extract_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PDFExtractionError("Encrypted PDFs are not supported")
        pages = [normalize_extracted_text(page.extract_text() or "") for page in reader.pages]
    except (OSError, PdfReadError, ValueError) as exc:
        if isinstance(exc, PDFExtractionError):
            raise
        raise PDFExtractionError("Unable to extract text from PDF") from exc

    text = "\n\n".join(page for page in pages if page).strip()
    if not text:
        raise NoExtractableTextError("PDF contains no extractable text")
    return text
