"""PDF text extraction and chunking."""
import io
import re

from pypdf import PdfReader

from app.models import Chunk


class PDFError(Exception):
    """The PDF cannot be used (corrupted, encrypted, or has no text)."""


def extract_pages(data: bytes) -> list[tuple[int, str]]:
    """Return [(page_number, text)] for every page that contains text."""
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PDFError("This PDF is password-protected.")
        pages = [(i, page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]
    except PDFError:
        raise
    except Exception as exc:
        raise PDFError("Could not read this PDF. The file may be corrupted.") from exc

    pages = [(number, text) for number, text in pages if text.strip()]
    if not pages:
        raise PDFError("No text found in this PDF. Scanned documents (images) are not supported.")
    return pages


def split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into chunks of roughly `size` characters, preferring paragraph
    and sentence boundaries. Neighbouring chunks share about `overlap` characters
    so that an answer split across a boundary is still retrievable."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    pieces: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        pieces.extend(_break_long(paragraph.strip(), size))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) + 1 > size:
            chunks.append(current)
            current = _tail(current, overlap)
        current = f"{current} {piece}".strip()
    if current:
        chunks.append(current)
    return chunks


def build_chunks(pages: list[tuple[int, str]], size: int, overlap: int) -> list[Chunk]:
    """Chunk each page separately so every chunk knows its page number."""
    return [
        Chunk(page=number, text=piece)
        for number, text in pages
        for piece in split_text(text, size, overlap)
    ]


def _break_long(text: str, size: int) -> list[str]:
    """Break a paragraph that is longer than `size` at sentence/word boundaries."""
    if not text:
        return []
    if len(text) <= size:
        return [text]
    pieces: list[str] = []
    for sentence in re.split(r"(?<=[.!?؟])\s+", text):
        while len(sentence) > size:
            cut = sentence.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            pieces.append(sentence[:cut])
            sentence = sentence[cut:].lstrip()
        if sentence:
            pieces.append(sentence)
    return pieces


def _tail(text: str, overlap: int) -> str:
    """Last `overlap` characters of text, starting at a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return "" if overlap <= 0 else text
    tail = text[-overlap:]
    first_space = tail.find(" ")
    return tail[first_space + 1:] if first_space != -1 else ""
