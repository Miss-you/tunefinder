"""Recognition backends. Currently: Shazamio (default)."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class RecognitionResult:
    matched: bool
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    isrc: str | None = None
    shazam_url: str | None = None
    cover_url: str | None = None
    preview_url: str | None = None
    apple_music_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Keep raw compact
        d["raw"] = {k: v for k, v in self.raw.items() if k in {"matches", "location", "timestamp"}}
        return d


class Recognizer:
    async def recognize(self, audio_path: Path) -> RecognitionResult:
        raise NotImplementedError


class ShazamioRecognizer(Recognizer):
    """Uses shazamio (reverse-engineered free Shazam API)."""

    async def recognize(self, audio_path: Path) -> RecognitionResult:
        # Import lazily so users without shazamio installed can still see errors clearly
        from shazamio import Shazam

        shazam = Shazam()
        raw = await shazam.recognize(str(audio_path))
        return _parse_shazam(raw)


def _parse_shazam(raw: dict[str, Any]) -> RecognitionResult:
    track = (raw or {}).get("track") or {}
    if not track:
        return RecognitionResult(matched=False, raw=raw or {})

    hub_actions = ((track.get("hub") or {}).get("actions")) or []
    preview_url = next(
        (a.get("uri") for a in hub_actions if a.get("type") == "uri" and a.get("uri")),
        None,
    )
    apple_music_url = None
    for opt in (track.get("hub") or {}).get("options", []) or []:
        for act in opt.get("actions", []) or []:
            if act.get("type") == "applemusicopen" and act.get("uri"):
                apple_music_url = act["uri"]
                break

    images = track.get("images") or {}
    return RecognitionResult(
        matched=True,
        title=track.get("title"),
        artist=track.get("subtitle"),
        album=_find_section_meta(track, "Album"),
        genre=(track.get("genres") or {}).get("primary"),
        isrc=track.get("isrc"),
        shazam_url=track.get("url") or (track.get("share") or {}).get("href"),
        cover_url=images.get("coverarthq") or images.get("coverart") or images.get("background"),
        preview_url=preview_url,
        apple_music_url=apple_music_url,
        raw=raw,
    )


def _find_section_meta(track: dict[str, Any], name: str) -> str | None:
    for section in track.get("sections", []) or []:
        for m in section.get("metadata", []) or []:
            if m.get("title") == name:
                return m.get("text")
    return None


def get_recognizer(backend: str = "shazamio") -> Recognizer:
    if backend == "shazamio":
        return ShazamioRecognizer()
    raise ValueError(f"Unknown backend: {backend!r}")


def recognize_sync(audio_path: Path, backend: str = "shazamio") -> RecognitionResult:
    rec = get_recognizer(backend)
    return asyncio.run(rec.recognize(audio_path))
