"""Endpoints to upload, list and delete the PDF knowledge base."""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.schemas import DocumentInfo
from app.services.pdf import PDFError, build_chunks, extract_pages
from app.services.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentInfo])
def list_documents(store: VectorStore = Depends(get_vector_store)):
    return store.list_documents()


@router.post("", response_model=DocumentInfo, status_code=201)
def upload_document(file: UploadFile = File(...), store: VectorStore = Depends(get_vector_store)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File is too large. The limit is {settings.max_upload_mb} MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "This file is not a valid PDF.")

    try:
        pages = extract_pages(data)
    except PDFError as exc:
        raise HTTPException(422, str(exc)) from exc

    chunks = build_chunks(pages, settings.chunk_size, settings.chunk_overlap)
    store.add_document(filename, chunks)
    logger.info("Indexed %s: %d pages, %d chunks", filename, len(pages), len(chunks))
    return DocumentInfo(filename=filename, pages=len(pages), chunks=len(chunks))


@router.delete("/{filename}", status_code=204)
def delete_document(filename: str, store: VectorStore = Depends(get_vector_store)):
    if not store.delete_document(filename):
        raise HTTPException(404, "Document not found.")
