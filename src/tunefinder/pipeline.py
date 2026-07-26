"""High-level orchestration: URL/file → RecognitionResult."""

from __future__ import annotations

from pathlib import Path

from .config import get_settings
from .downloader import download_audio
from .recognizer import RecognitionResult, recognize_sync


def recognize_from_url(url: str) -> RecognitionResult:
    settings = get_settings()
    audio = download_audio(url, settings.download_dir, prefer_mp3=True)
    return recognize_sync(audio, backend=settings.backend)


def recognize_from_file(path: str | Path) -> RecognitionResult:
    settings = get_settings()
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(p)
    return recognize_sync(p, backend=settings.backend)
