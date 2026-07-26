# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `AGENTS.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`
- GitHub Actions CI (`.github/workflows/ci.yml`) running ruff + pytest on Python 3.10-3.12
- Ruff & pytest configuration in `pyproject.toml`
- Test suite under `tests/`: recognizer parsing, downloader stdout parsing, FastAPI smoke
- `docs/how-it-works.md` — end-to-end explainer of the URL → recognition pipeline
- Expanded `.gitignore` (IDE, OS, caches)
- Issue templates and pull request template

## [0.1.0] — 2026-07-26

### Added
- Initial release as `tunefinder` (renamed from earlier internal name).
- URL & file recognition modes via `tunefinder recognize`.
- FastAPI web UI at `tunefinder serve`.
- Shazamio backend; `RecognitionResult` dataclass with title / artist / album / genre / ISRC / Shazam URL / cover / preview / Apple Music.
- Industry survey document (`docs/tech-survey.md`).
