"""Naad Desk FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import calls, evaluation, findings, health, knowledge
from .config import ROOT, settings
from .db.database import SessionLocal, init_db
from .db.seed import seed
from .gateway.websocket import router as ws_router
from .gateway.websocket import set_retriever
from .logging_util import log
from .retrieval.hybrid import HybridRetriever
from .retrieval.ingestion import ingest_directory


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup_begin")
    init_db()
    db = SessionLocal()
    try:
        seed(db)
        stats = ingest_directory(db, ROOT / "knowledge", None)
        log.info("kb_indexed", extra={"chunks": stats.get("chunks"), "chars": stats.get("total_chars")})
        retriever = HybridRetriever()
        retriever.build_from_db(db)
        set_retriever(retriever)
        # Genuine findings from Phase 0 reconnaissance.
        import sys
        sys.path.insert(0, str(ROOT))
        from recon.findings_seed import seed_findings
        added = seed_findings(db)
        log.info("findings_seeded", extra={"added": added})
    finally:
        db.close()
    log.info("startup_complete", extra={"api_key_configured": settings.has_api_key})
    yield
    from .gateway.oogam_client import oogam
    await oogam.close()


app = FastAPI(title="Naad Desk", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for router in (health.router, calls.router, knowledge.router,
               evaluation.router, findings.router, ws_router):
    app.include_router(router)


@app.get("/api/config")
async def public_config():
    """Non-secret runtime flags the frontend needs."""
    return {
        "upstream_configured": settings.has_api_key,
        "voice": settings.voice,
        "language": settings.lang,
        "retrieval_backend": "deterministic_char_hash",
    }


@app.get("/api/healthz")
async def healthz():
    return {"ok": True}


# Serve the built frontend if present (Docker/local). On Vercel the frontend is
# a separate service and owns the catch-all route.
DIST = ROOT / "frontend" / "dist"
if DIST.exists() and not settings.is_vercel:
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        candidate = DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
