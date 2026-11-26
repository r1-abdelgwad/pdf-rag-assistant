"""Tests for the local sentence-transformers embedding service.

These tests require the model to be downloaded (happens automatically on first
run; subsequent runs use the local cache).  They do NOT need any API key.
"""
from app.services.embeddings import embed_documents, embed_query


def test_embed_query_returns_list_of_floats():
    result = embed_query("What is the leave policy?")
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(v, float) for v in result)


def test_embed_query_length_matches_embed_documents():
    doc_vector = embed_documents(["x"])[0]
    query_vector = embed_query("x")
    assert len(query_vector) == len(doc_vector)


def test_embed_documents_returns_one_vector_per_text():
    texts = ["first document", "second document", "third document"]
    vectors = embed_documents(texts)
    assert len(vectors) == len(texts)
    assert all(isinstance(v, list) for v in vectors)
    assert all(isinstance(f, float) for f in vectors[0])
