import asyncio
import json
import sys
from pathlib import Path

from shazamio import Shazam


async def recognize(path: str) -> dict:
    shazam = Shazam()
    return await shazam.recognize(path)


def summarize(result: dict) -> dict:
    track = (result or {}).get("track") or {}
    if not track:
        return {"matched": False, "raw_matches": result.get("matches", [])}
    return {
        "matched": True,
        "title": track.get("title"),
        "artist": track.get("subtitle"),
        "shazam_url": track.get("url"),
        "genres": track.get("genres"),
        "isrc": track.get("isrc"),
        "sections_top": [s.get("type") for s in track.get("sections", [])][:3],
        "hub_actions": [
            {"name": a.get("name"), "type": a.get("type"), "uri": a.get("uri")}
            for a in (track.get("hub") or {}).get("actions", [])
        ],
    }


def main() -> None:
    audio = sys.argv[1] if len(sys.argv) > 1 else "samples/yt_r05JFAAWAZ8.mp3"
    audio_path = str(Path(audio).resolve())
    result = asyncio.run(recognize(audio_path))
    print("=== SUMMARY ===")
    print(json.dumps(summarize(result), ensure_ascii=False, indent=2))
    print("=== RAW (truncated) ===")
    print(json.dumps(result, ensure_ascii=False)[:1200])


if __name__ == "__main__":
    main()
