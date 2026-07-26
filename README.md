# tunefinder — Universal Music Recognition Tool

Recognize the song playing in any audio, from a **URL** or a **local file**, in a
single command. Powered by [Shazamio](https://github.com/shazamio/ShazamIO)
(a free, reverse-engineered Shazam API).

```
YouTube / Bilibili URL  ┐
                        ├──► tunefinder ──► "Mori No Chiisana Restaurant — 手嶌葵"
Local mp3 / m4a / wav   ┘
```

---

## (a) What it is and what problem it solves

**What it is.** A small, self-hosted Python tool with three interchangeable
frontends over the same recognition core:

- **Python API** — `tunefinder.recognize_from_url(...)` / `recognize_from_file(...)`
- **CLI** — `tunefinder recognize --url ...` / `tunefinder recognize --file ...`
- **Web UI** — a plain HTML/JS page served by FastAPI, no framework, no build

**Problem it solves.** You have a video, a clip, or a piece of audio, and you
want to know **which song is playing** without:

- installing a mobile app,
- signing up for a paid API (AudD / ACRCloud),
- or handing your audio to a third-party website.

`tunefinder` handles the whole pipeline offline-ish: it downloads the audio
locally, extracts a compact fingerprint, and asks Shazam's public matcher
directly. The heavy work (download, transcode, fingerprint, match) happens on
**your machine**; the only network calls are to the source video and to
Shazam.

**First recognition demo** — input `https://www.youtube.com/shorts/r05JFAAWAZ8`:

| Field  | Value                                                                 |
| ------ | --------------------------------------------------------------------- |
| Title  | Mori No Chiisana Restaurant (森のちいさなレストラン)                  |
| Artist | Aoi Teshima (手嶌葵)                                                  |
| Genre  | J-Pop                                                                 |
| ISRC   | JPVI02301273                                                          |
| Shazam | <https://www.shazam.com/track/660662889/mori-no-chiisana-restaurant>  |

---

## (b) How it works — the end-to-end flow

Given either a URL or a local file, tunefinder runs a **4-stage pipeline**:

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ 1. Download  │──►│ 2. Fingerprint│──►│ 3. Match     │──►│ 4. Normalize │
 │  + extract   │   │  (spectrogram│   │  (Shazam     │   │  → stable    │
 │  audio       │   │  peaks →     │   │  public API) │   │  result      │
 │  (yt-dlp +   │   │  ~10k hashes)│   │              │   │  dataclass)  │
 │  ffmpeg)     │   │              │   │              │   │              │
 └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

1. **Download & extract audio.** For a URL, [downloader.py](src/tunefinder/downloader.py)
   shells out to `yt-dlp` to grab the best audio track and pipes it through
   `ffmpeg` to produce a clean `mp3`. For a local file this step is skipped.
2. **Fingerprint.** [recognizer.py](src/tunefinder/recognizer.py) hands the audio
   to Shazamio, which computes a spectrogram, keeps only local energy peaks
   (this is what makes the fingerprint noise-proof), and pairs neighboring
   peaks into a stream of compact `(f₁, f₂, Δt)` hashes — roughly 10k of them
   for a few-second clip.
3. **Match.** Those hashes get POSTed to Shazam's public matcher. The server
   intersects them with its ~20M-song index and, crucially, checks that the
   matching hashes **line up in time** (a histogram of `db_offset − query_offset`
   should peak sharply). That temporal alignment is why one true match beats
   thousands of coincidental hits.
4. **Normalize.** The deeply-nested Shazam JSON is flattened into a stable
   `RecognitionResult` dataclass (title / artist / album / ISRC / links), so
   CLI, Web UI, and any future backend share one contract — see
   [pipeline.py](src/tunefinder/pipeline.py).

End-to-end latency in practice: **~3–8 s**, dominated by the download and one
Shazam round-trip.

📖 Full deep-dive with the fingerprint math and failure modes:
[docs/how-it-works.md](docs/how-it-works.md).

🧠 Industry survey of other music-recognition tech (ACRCloud / AudD / Chromaprint / Dejavu / NeuralFP):
[docs/tech-survey.md](docs/tech-survey.md).

💡 Design idea — running this as a lightweight private-by-default hosted tool
(future work, not built yet): [docs/ideas/hosted-serverless.md](docs/ideas/hosted-serverless.md).

---

## (c) How to run it locally

### 1. System prerequisites

- **Python 3.10+**
- **ffmpeg** — audio decoding / transcoding
- **yt-dlp** — installed as a Python dep automatically; a system binary works too
- Optional: **fpcalc** (Chromaprint) — only needed if you later wire up the
  AcoustID backend

macOS one-liner:

```bash
brew install ffmpeg chromaprint
```

Ubuntu / Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg libchromaprint-tools
```

### 2. Install

```bash
git clone https://github.com/<your-username>/tunefinder.git
cd tunefinder
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

For contributors:

```bash
pip install -e ".[dev]"
```

### 3. Run — pick any of the three frontends

**CLI (URL mode):**

```bash
tunefinder recognize --url "https://www.youtube.com/shorts/r05JFAAWAZ8"
```

**CLI (file mode):**

```bash
tunefinder recognize --file samples/yt_r05JFAAWAZ8.mp3
```

**Web UI (recommended for browsing):**

```bash
tunefinder serve                       # http://127.0.0.1:8000
tunefinder serve --host 0.0.0.0 --port 8080   # LAN-accessible
```

Then open <http://127.0.0.1:8000> in your browser and paste a URL or upload
an audio file.

**Python API:**

```python
import asyncio
from tunefinder import recognize_from_url

result = asyncio.run(recognize_from_url("https://www.youtube.com/shorts/r05JFAAWAZ8"))
print(result.title, result.artist)
```

### 4. Configuration

All settings are environment variables prefixed with `TUNEFINDER_` — see
[config.py](src/tunefinder/config.py):

```bash
export TUNEFINDER_BACKEND=shazamio        # default; only backend implemented today
export TUNEFINDER_DOWNLOAD_DIR=./downloads # where yt-dlp writes intermediates
```

### 5. Verify your setup

```bash
ruff check . && ruff format --check .
pytest -q
```

Tests are hermetic (no network, no Shazam calls) and should finish in under
5 seconds. If they pass, you're good.

---

## Project layout

```
tunefinder/
├── pyproject.toml
├── README.md
├── AGENTS.md                     # SOP for AI coding agents / contributors
├── docs/
│   ├── how-it-works.md           # Fingerprint + match deep-dive
│   ├── tech-survey.md            # Comparison of alternative backends
│   └── ideas/
│       └── hosted-serverless.md  # Design idea: private hosted variant
├── src/tunefinder/
│   ├── __init__.py
│   ├── config.py                 # TUNEFINDER_* env-driven settings
│   ├── downloader.py             # yt-dlp + ffmpeg audio extraction
│   ├── recognizer.py             # Recognizer ABC + Shazamio impl
│   ├── pipeline.py               # URL / file → RecognitionResult
│   ├── cli.py                    # click CLI entry point
│   └── web/
│       ├── server.py             # FastAPI app
│       └── static/               # index.html + app.js + style.css
├── samples/                      # Optional local audio for smoke tests
├── scripts/quick_recognize.py    # One-off validation script
└── tests/                        # pytest suite (offline, <5s)
```

## Pluggable recognition backend

The `Recognizer` interface in [recognizer.py](src/tunefinder/recognizer.py) is
intentionally minimal — one async method returning a `RecognitionResult`. To
plug in AcoustID / Dejavu / a self-hosted neural fingerprinter later, implement
the ABC, register it in `get_recognizer()`, and switch via
`TUNEFINDER_BACKEND=<name>`. CLI / Web / Python API don't need to change.

## License

MIT — see [LICENSE](LICENSE).
