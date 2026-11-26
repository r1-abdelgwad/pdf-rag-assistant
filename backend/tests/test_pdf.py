import pytest

from app.services.pdf import PDFError, build_chunks, extract_pages, split_text


def test_short_text_is_one_chunk():
    assert split_text("Hello world.", size=100, overlap=20) == ["Hello world."]


def test_long_text_is_split_with_overlap():
    text = " ".join(f"Sentence number {i}." for i in range(60))
    chunks = split_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 + 40 for c in chunks)
    # neighbouring chunks share some words
    assert set(chunks[0].split()[-3:]) & set(chunks[1].split())


def test_single_word_longer_than_size_is_cut():
    chunks = split_text("x" * 250, size=100, overlap=0)
    assert [len(c) for c in chunks] == [100, 100, 50]


def test_empty_text_gives_no_chunks():
    assert split_text("  \n\n ", size=100, overlap=10) == []


def test_chunks_keep_their_page_number():
    chunks = build_chunks([(1, "First page."), (3, "Third page.")], size=100, overlap=10)
    assert [(c.page, c.text) for c in chunks] == [(1, "First page."), (3, "Third page.")]


def test_corrupted_pdf_is_rejected():
    with pytest.raises(PDFError):
        extract_pages(b"%PDF-1.4 this is not really a pdf")
