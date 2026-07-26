"""FastAPI application: JSON API + static frontend."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..pipeline import recognize_from_file, recognize_from_url


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="tunefinder", version="0.1.0")


class RecognizeUrlBody(BaseModel):
    url: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/recognize/url")
async def api_recognize_url(body: RecognizeUrlBody) -> dict:
    if not body.url.strip():
        raise HTTPException(status_code=400, detail="url is required")
    try:
        # pipeline is sync (subprocess + asyncio.run inside). Run in threadpool.
        result = await asyncio.to_thread(recognize_from_url, body.url.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return result.to_dict()


@app.post("/api/recognize/file")
async def api_recognize_file(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "audio.mp3").suffix or ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        result = await asyncio.to_thread(recognize_from_file, tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
    return result.to_dict()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
