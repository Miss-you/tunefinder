# Contributing to tunefinder

Thanks for your interest! This is a small, opinionated project — we prefer a few well-scoped PRs over sweeping refactors.

## Before you open a PR

1. Fork & clone.
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -e ".[dev]"`
4. Run the fast checks:
   ```bash
   ruff check .
   ruff format --check .
   pytest -q
   ```
5. If your change is user-visible (new CLI flag, new API field, backend behavior change), update:
   - [README.md](README.md)
   - [CHANGELOG.md](CHANGELOG.md) (add an entry under `[Unreleased]`)

## Scope guidance

- **Great fits**: new recognition backends, better error messages, docs, CI fixes, better tests, bug fixes.
- **Please discuss first (open an issue)**: renaming public APIs, adding paid API dependencies, changing the CLI surface.
- **Out of scope**: bundling proprietary datasets, redistributing copyrighted audio.

## Code style

Everything is enforced by `ruff` — see [pyproject.toml](pyproject.toml). Beyond that, please follow the conventions in [AGENTS.md](AGENTS.md).

## Tests

- Must be **offline**. No network, no `yt-dlp` subprocess, no real Shazam calls.
- Cover the happy path *and* one failure branch when adding a new module.

## Reporting bugs / suggesting features

Use the [Issue templates](.github/ISSUE_TEMPLATE). For security concerns, don't file a public issue — email the maintainer instead.

## Licensing

By contributing you agree that your contributions are licensed under the MIT License (same as the project).
