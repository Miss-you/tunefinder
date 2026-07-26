# How tunefinder works — from a link to a song title

> One question in one sentence: **how does pasting `https://youtube.com/shorts/xxxx` end up telling you "this is *Mori No Chiisana Restaurant* by Aoi Teshima"?**

The answer is a 4-stage pipeline. This doc walks each stage, then zooms in on the algorithm at the heart of it: **audio fingerprinting**.

---

## 1. The 30-second overview

```
   ┌────────────┐   ┌─────────────┐   ┌───────────────────┐   ┌──────────────┐
   │  1. URL /  │→  │ 2. Download │→  │ 3. Fingerprint &  │→  │ 4. Return    │
   │     File   │   │  + extract  │   │    match (cloud)  │   │  metadata    │
   └────────────┘   │   audio     │   └───────────────────┘   └──────────────┘
                    └─────────────┘
```

| Stage | What happens | Who does it in this repo |
| --- | --- | --- |
| 1. Input | User submits a URL or uploads a file | `cli.py` / `web/server.py` |
| 2. Fetch audio | Download the video, strip video, keep audio, transcode to mp3 | `downloader.py` (yt-dlp + ffmpeg) |
| 3. Recognize | Generate an audio fingerprint from the mp3, send to Shazam's cloud, get a match | `recognizer.py` (Shazamio) |
| 4. Present | Normalize the response into a `RecognitionResult`, show title / artist / links | `pipeline.py` + `web/static/app.js` |

---

## 2. Stage 1 — Input

Two entry points, one code path:

- **CLI**: `tunefinder recognize --url <link>` or `--file <path>` → [cli.py](../src/tunefinder/cli.py) → `pipeline.recognize_from_url` / `recognize_from_file`.
- **Web**: `POST /api/recognize/url` (JSON) or `POST /api/recognize/file` (multipart) → [server.py](../src/tunefinder/web/server.py) → same `pipeline` functions, wrapped in `asyncio.to_thread` so the FastAPI event loop isn't blocked.

They both converge on `pipeline.recognize_from_url()` / `recognize_from_file()`, so the rest of the doc treats them as one path.

## 3. Stage 2 — Download & extract audio

`recognize_from_url()` calls `download_audio()` in [downloader.py](../src/tunefinder/downloader.py), which shells out to `yt-dlp`:

```
yt-dlp -x --audio-format mp3 --audio-quality 0 \
       -o <out_dir>/yt_%(id)s.%(ext)s <url>
```

- `-x` = extract audio only (no video track kept)
- `--audio-format mp3` = ask ffmpeg (invoked by yt-dlp) to transcode to mp3
- `--audio-quality 0` = best available quality

We parse `yt-dlp`'s stdout for `Destination:` or `has already been downloaded` to find the final file path (see `_find_result_file`), with a mtime-based fallback. The result is a plain local `mp3`.

> Why mp3? Shazam's algorithm doesn't care about the container — but mp3 keeps the file small and is universally decodable by Shazamio's underlying `pydub` + ffmpeg loader.

For file-mode requests we skip this stage entirely.

## 4. Stage 3 — Fingerprint & match (the interesting part)

This is where "audio → song title" happens. tunefinder delegates the algorithm to **Shazamio**, but the underlying idea is the [Shazam 2003 paper](https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf). Here's what happens inside that black box:

### 4.1 Turn audio into a picture

Take the mp3, decode to raw PCM (mono, ~8 kHz is enough), then run a **Short-Time Fourier Transform (STFT)**: chop the waveform into overlapping ~40 ms windows, and compute a spectrum for each. The result is a 2-D image called a **spectrogram** — time on X, frequency on Y, brightness = energy.

```
                        frequency
                            ▲
                            │
                    peaks   │ • . •     •  .   •
                            │ .   • .  •  •
   audio waveform  ───────► │ • •   • .    •  •      ─── time ──►
                            │  .  •  .  •    •
                            │_____________________________________
```

Music has clear peaks (notes, harmonics). Noise doesn't — it's diffuse. That's what we exploit next.

### 4.2 Keep only the peaks — this is what makes it noise-proof

We throw away 99% of the spectrogram and keep only **local energy peaks**: points that are louder than every neighbor within some frequency-time neighborhood.

Peaks survive:
- MP3 compression (peaks are the loudest parts, compression touches them last)
- Café background noise (noise adds diffuse energy, not new peaks)
- EQ tweaks (peaks shift a bit but stay peaks)
- Cropped clips (any long-enough window still has enough peaks)

This is why Shazam works from a 5-second phone recording in a noisy bar.

### 4.3 Turn peaks into hashes

Peaks alone aren't a searchable fingerprint. Instead, we pick an **anchor peak** and pair it with several nearby peaks in a "target zone". Each pair becomes a compact hash:

```
hash = (freq_anchor, freq_target, Δt)   → 32-bit integer
value stored in DB = (song_id, absolute_time_of_anchor_in_song)
```

A 3-minute song produces ~10,000 such hashes. Shazam's index maps `hash → list of (song_id, offset)`.

### 4.4 The clever matching trick

To decide *which* song a query clip matches, we don't just count hash hits — we look for **temporal alignment**:

1. For every query hash that appears in the DB, compute `Δ = db_offset − query_offset`.
2. Group the Δ values by song. Take a histogram.
3. The correct song has a huge **peak in its histogram**: because if the clip is really a snippet of that song at time T, then every hit for that song produces roughly the same Δ ≈ T.
4. Wrong songs give scattered Δ values (background hits) — no peak.

This is what makes Shazam robust: even if 90% of your query's hashes collide with random songs by chance, only the *correct* song has them all lining up in time.

### 4.5 Where Shazamio comes in

`ShazamioRecognizer.recognize()` in [recognizer.py](../src/tunefinder/recognizer.py) essentially does:

```python
from shazamio import Shazam

raw = await Shazam().recognize(str(audio_path))
```

Shazamio locally fingerprints a few seconds of audio (using the algorithm above) and POSTs the hashes to Shazam's public recognition endpoint. Shazam runs the histogram matching against its ~20M-song index and returns a JSON blob containing the top track.

> This is a **reverse-engineered public API**, not an officially licensed SDK. It's excellent for personal use / prototypes and can be rate-limited or broken at any time. See [docs/tech-survey.md](tech-survey.md) for licensed alternatives (ACRCloud, AudD, self-hosted Dejavu).

## 5. Stage 4 — Normalize & present

Shazam's JSON is deeply nested and inconsistent (hub.actions[…], sections[…].metadata[…] etc.). We flatten it in `_parse_shazam()` into a stable dataclass:

```python
@dataclass
class RecognitionResult:
    matched: bool
    title: str | None
    artist: str | None
    album: str | None
    genre: str | None
    isrc: str | None  # global standard recording code
    shazam_url: str | None  # canonical Shazam link
    cover_url: str | None  # album art (HQ preferred)
    preview_url: str | None  # 30s streaming preview
    apple_music_url: str | None  # deep link if available
    raw: dict  # kept compact (only matches/location/timestamp)
```

Everything downstream (CLI print, Web JSON response, static frontend rendering) only depends on `RecognitionResult`, which is why **swapping backends later doesn't ripple through the codebase**.

## 6. Full request timeline (URL mode)

```
User            CLI / API          Downloader         Shazamio             Shazam cloud
 │                 │                    │                 │                     │
 │──URL──────────► │                    │                 │                     │
 │                 │──yt-dlp -x─────────►                 │                     │
 │                 │                    │──mp3 file──────►│                     │
 │                 │                    │                 │──fingerprint POST──►│
 │                 │                    │                 │◄──top track JSON────│
 │                 │◄─RecognitionResult─│─────────────────│                     │
 │◄─JSON/render────│                    │                 │                     │
```

End-to-end latency in practice: **3-8 seconds**, dominated by download (varies with source) and Shazam's cloud round-trip. Recognition itself is ~1 second once audio is on disk.

## 7. Failure modes to know about

| Failure | Where it happens | What we do |
| --- | --- | --- |
| `yt-dlp` binary missing | Stage 2 | Raise `DownloadError` with install hint |
| Video has no audio / geo-blocked | Stage 2 | `yt-dlp` non-zero exit → last 500 chars of stderr surfaced |
| Audio too short / too noisy | Stage 3 | Shazam returns empty `track` → `RecognitionResult(matched=False)` |
| Shazam rate-limits Shazamio | Stage 3 | Exception surfaces to CLI / API `500` — retry later or switch backend |
| Instrumental / very obscure song | Stage 3 | Just won't match — expected behavior of any commercial fingerprint DB |

## 8. Design choices, in one line each

- **Backend is pluggable** because the whole industry has 6+ options with wildly different tradeoffs (see [docs/tech-survey.md](tech-survey.md)) — locking in Shazam would age poorly.
- **Sync `pipeline` wrapped in `asyncio.to_thread`** in FastAPI because `yt-dlp` is a blocking subprocess anyway; not worth making the whole stack async for one call.
- **Static frontend, no build step** because this is a demo tool; adding React/Vite would multiply the setup cost with zero UX gain.
- **`RecognitionResult` dataclass, not a raw dict** because it makes the contract with the frontend explicit and testable (see [tests/test_recognizer_parse.py](../tests/test_recognizer_parse.py)).
