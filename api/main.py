"""FastAPI app. Run: uvicorn api.main:app --reload  (serves the built React app from web/dist too)."""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from .db import DB  # noqa: E402
from .routes import exceptions, overview, payments, trace  # noqa: E402

app = FastAPI(title="YottaFlex ReconOps API", version="1.0.0",
              description="Reconciles payment instructions, processor events, settlement batches and bank statements.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.state.db = DB()
for r in (overview.router, exceptions.router, payments.router, trace.router):
    app.include_router(r)

DIST = ROOT / "web" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
