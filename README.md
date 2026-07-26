# tunefinder — Universal Music Recognition Tool

A drop-in music recognition tool powered by [Shazamio](https://github.com/shazamio/ShazamIO) (a free, reverse-engineered Shazam API), with:

1. **URL mode** — paste a YouTube / Bilibili / etc. link, we download → extract audio → recognize
2. **File mode** — feed any local audio file (mp3 / m4a / wav / ogg / webm / mp4 …)
3. Two frontends: a **CLI** and a **FastAPI-based Web UI** (plain HTML / JS, no framework)

## ✨ First recognition demo

Input: `https://www.youtube.com/shorts/r05JFAAWAZ8`

| Field  | Value                                                                 |
| ------ | --------------------------------------------------------------------- |
| Title  | Mori No Chiisana Restaurant (森のちいさなレストラン)                  |
| Artist | Aoi Teshima (手嶌葵)                                                  |
| Genre  | J-Pop                                                                 |
| ISRC   | JPVI02301273                                                          |
| Shazam | <https://www.shazam.com/track/660662889/mori-no-chiisana-restaurant>  |

---

## 🛠️ System requirements

- Python 3.10+
- `ffmpeg` (audio decode / transcode)
- `yt-dlp` (installed as a Python dep, or system-wide)
- Optional: `fpcalc` (Chromaprint) — only needed for the AcoustID backend

macOS one-liner:

```bash
brew install ffmpeg chromaprint
```

## 🚀 Quick start

```bash
# 1. Create a virtualenv and install
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Recognize via CLI
tunefinder recognize --url "https://www.youtube.com/shorts/r05JFAAWAZ8"
tunefinder recognize --file samples/yt_r05JFAAWAZ8.mp3

# 3. Launch the Web UI (default http://127.0.0.1:8000)
tunefinder serve
```

Open <http://127.0.0.1:8000> in your browser to use the UI.

## 🧠 Industry survey of music-recognition tech

See [docs/tech-survey.md](docs/tech-survey.md) for a full comparison of Shazam / ACRCloud / AudD / Chromaprint / Dejavu / NeuralFP across accuracy, latency, cost and use cases.

## 📁 Project layout

```
tunefinder/
├── pyproject.toml
├── requirements.txt
├── README.md
├── docs/
│   └── tech-survey.md         # Industry survey
├── src/tunefinder/
│   ├── __init__.py
│   ├── config.py              # Config (download dir, backend, …)
│   ├── downloader.py          # yt-dlp + ffmpeg audio extraction
│   ├── recognizer.py          # Recognizer abstraction + Shazamio impl
│   ├── pipeline.py            # URL / file → result orchestration
│   ├── cli.py                 # click CLI entry point
│   └── web/
│       ├── server.py          # FastAPI app
│       └── static/
│           ├── index.html
│           ├── app.js
│           └── style.css
├── samples/                   # Sample audio files
└── scripts/quick_recognize.py # Original one-off validation script
```

## 🔌 Pluggable recognition backend

Switch backends via env var (only `shazamio` is implemented today; `acoustid` and `dejavu` are stubs for future work):

```bash
export TUNEFINDER_BACKEND=shazamio      # default
export TUNEFINDER_DOWNLOAD_DIR=./downloads
```

## 📝 License

MIT
