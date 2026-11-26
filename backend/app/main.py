"""FastAPI application entry point.

Run from the backend/ folder:  uvicorn app.main:app --reload
"""
import logging
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.routes import chat, documents
from app.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="PDF Chatbot (RAG)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


api = APIRouter(prefix="/api")


@api.get("/health")
def health():
    return {"status": "ok", "llm_configured": bool(settings.groq_api_key)}


api.include_router(documents.router)
api.include_router(chat.router)
app.include_router(api)

# Serve the built React app (frontend/dist) if it exists, so one server runs everything.
frontend_dist: Path = BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
