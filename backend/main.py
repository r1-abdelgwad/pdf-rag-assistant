"""Start the whole app (API + web interface) from the project root:

    python -m backend.main
"""
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))  # lets `app.*` imports work from any folder

import uvicorn  # noqa: E402

from app.config import settings  # noqa: E402

logger = logging.getLogger("backend")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not (BACKEND_DIR.parent / "frontend" / "dist").exists():
        logger.warning("Web interface not built. Run once:  cd frontend && npm install && npm run build")
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY is not set. Add it to backend/.env")

    logger.info("Open http://%s:%s   (API docs: /docs)", settings.host, settings.port)
    uvicorn.run(
        "app.main:app",
        app_dir=str(BACKEND_DIR),
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=[str(BACKEND_DIR / "app")],
    )


if __name__ == "__main__":
    main()
