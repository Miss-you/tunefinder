# AGENTS.md — Working on `tunefinder`

This file is the SOP for any AI coding agent (Claude, Codex, Trae, Cursor, …) or human contributor working in this repository.

## 1. What this project is

`tunefinder` recognizes what song is playing in a piece of audio. Input is either:
- a **URL** (YouTube / Bilibili / …) — we download & extract audio, or
- a **local audio file** (`mp3` / `m4a` / `wav` / `webm` / …).

The recognition backend is **Shazamio** (reverse-engineered free Shazam API). Interfaces exposed:
- Python API — `tunefinder.recognize_from_url`, `tunefinder.recognize_from_file`
- CLI — `tunefinder recognize --url|--file …`, `tunefinder serve`
- Web UI + JSON API — FastAPI app in [src/tunefinder/web/server.py](src/tunefinder/web/server.py)

## 2. Repository layout

```
src/tunefinder/
  config.py          Env-driven Settings (TUNEFINDER_*)
  downloader.py      yt-dlp subprocess wrapper; audio download + extraction
  recognizer.py      Recognizer ABC + ShazamioRecognizer; RecognitionResult dataclass
  pipeline.py        URL/file → RecognitionResult orchestration
  cli.py             click CLI (recognize / serve)
  web/
    server.py        FastAPI app: /, /api/health, /api/recognize/url, /api/recognize/file
    static/          plain HTML/CSS/JS frontend, no build step

docs/                tech-survey.md, how-it-works.md
tests/               pytest suite; must be offline & fast (< 5s total)
scripts/             one-off validation scripts
.github/workflows/   CI
```

## 3. Development loop

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Fast feedback:
ruff check . && ruff format --check .
pytest -q

# Manual smoke:
tunefinder recognize --file samples/yt_r05JFAAWAZ8.mp3
tunefinder serve --port 8000
```

## 4. Conventions

- **Python ≥ 3.10**; prefer PEP 604 unions (`str | None`) and `from __future__ import annotations`.
- **Lint & format**: `ruff` is the source of truth. Rules & line length live in [pyproject.toml](pyproject.toml).
- **Public API stability**: everything in `tunefinder/__init__.py` is public. Don't break it without bumping version + updating CHANGELOG.
- **Env variables**: prefix is `TUNEFINDER_` (see [config.py](src/tunefinder/config.py)). Never invent a new prefix.
- **No secrets in code**. Ever. There are no API keys in this project today — keep it that way.
- **Comments**: default is *no* comments unless the code is genuinely non-obvious (e.g. yt-dlp stdout parsing). Prefer clearer code and dataclass field names over prose.

## 5. Test rules

- Tests must be **hermetic**: no network, no `yt-dlp` subprocess, no `Shazam().recognize(...)`. If you need Shazam-shaped data, hand-craft a payload (see [test_recognizer_parse.py](tests/test_recognizer_parse.py)).
- Adding a new module? Add a matching `tests/test_<module>.py`. Aim for the happy path + at least one error branch.
- CI runs on Python 3.10 / 3.11 / 3.12 (Ubuntu). Don't rely on macOS-only tools.

## 6. Backends

Only `shazamio` is implemented. `acoustid` / `dejavu` are documented aspirations; if you add one:
1. Implement `Recognizer` in [recognizer.py](src/tunefinder/recognizer.py) and wire it into `get_recognizer()`.
2. Return the same `RecognitionResult` dataclass so `pipeline` / CLI / Web don't change.
3. Add a section to [docs/tech-survey.md](docs/tech-survey.md) explaining tradeoffs.

## 7. When you finish a change

- [ ] `ruff check .` clean
- [ ] `ruff format --check .` clean
- [ ] `pytest -q` green
- [ ] README / docs updated if user-visible behavior changed
- [ ] No new files created "just in case" — this repo prefers editing over spawning docs

## 8. Non-goals

- Not aiming to be a hosted service.
- Not implementing our own fingerprint algorithm — that's what backends are for.
- Not depending on any paid API by default.
