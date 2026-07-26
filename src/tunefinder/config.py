"""Runtime configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOWNLOAD_DIR = PROJECT_ROOT / "downloads"


@dataclass(frozen=True)
class Settings:
    backend: str = os.getenv("TUNEFINDER_BACKEND", "shazamio")
    download_dir: Path = Path(os.getenv("TUNEFINDER_DOWNLOAD_DIR", str(DEFAULT_DOWNLOAD_DIR)))
    # For long audio, we only fingerprint the first N seconds by default
    max_seconds: int = int(os.getenv("TUNEFINDER_MAX_SECONDS", "60"))


def get_settings() -> Settings:
    s = Settings()
    s.download_dir.mkdir(parents=True, exist_ok=True)
    return s
