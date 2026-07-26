"""Download audio from a URL (YouTube, Bilibili, etc.) via yt-dlp."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


class DownloadError(RuntimeError):
    pass


def download_audio(url: str, out_dir: Path, prefer_mp3: bool = True) -> Path:
    """Download best audio from `url` into `out_dir`, return final audio file path.

    Uses `yt-dlp` binary if present, else the `yt_dlp` Python module as fallback.
    Requires `ffmpeg` to be installed for mp3 conversion.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    template = str(out_dir / "yt_%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-quality", "0",
        "-o", template,
        url,
    ]
    if prefer_mp3:
        cmd[2:2] = ["--audio-format", "mp3"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise DownloadError("yt-dlp binary not found. Install with `pip install yt-dlp` or `brew install yt-dlp`.") from e

    if proc.returncode != 0:
        raise DownloadError(f"yt-dlp failed: {proc.stderr[-500:]}")

    # Parse the actual output path from yt-dlp stdout
    audio_file = _find_result_file(proc.stdout, out_dir)
    if audio_file is None:
        # Fallback: pick the newest mp3/m4a in out_dir
        candidates = sorted(
            [p for p in out_dir.iterdir() if p.suffix.lower() in {".mp3", ".m4a", ".webm", ".opus", ".wav"}],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise DownloadError("Download succeeded but no audio file found.")
        audio_file = candidates[0]
    return audio_file


def _find_result_file(stdout: str, out_dir: Path) -> Optional[Path]:
    # yt-dlp prints lines like:
    # [ExtractAudio] Destination: /path/to/yt_XXX.mp3
    # [download] /path/to/yt_XXX.mp3 has already been downloaded
    for line in stdout.splitlines():
        for marker in ("Destination:", "has already been downloaded"):
            if marker in line:
                # Take last path-looking token
                parts = line.split(marker)
                if marker == "Destination:":
                    candidate = parts[-1].strip()
                else:
                    # "[download] /path has already been downloaded"
                    candidate = parts[0].split("]")[-1].strip()
                p = Path(candidate)
                if p.exists():
                    return p
    return None
