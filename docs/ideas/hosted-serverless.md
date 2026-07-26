# Idea — Hosted tunefinder with a lightweight, private-by-default backend

> Status: **idea / not implemented**. This doc captures the design thinking so we
> can pick it up later. Today `tunefinder` runs locally only; nothing here has
> been built yet.

## 1. Why write this down

While playing with tunefinder locally, a natural follow-up came up:

> "Can I host this as a tool without paying for a server or worrying about
> abuse? Ideally everything runs in the user's browser; if not, at least keep
> the server dumb and cheap."

We explored three flavors — pure frontend, browser + tiny proxy, and a
"private-by-default" hosted backend — and landed on the third as the right
first step. This doc records **why**, so future-me doesn't re-litigate the
same tradeoffs.

## 2. What we considered

### Option A — Pure static frontend

- Frontend does: file upload / mic capture → ffmpeg.wasm → shazamio-core WASM
  fingerprint → **directly** call AudD or Shazam.
- Server cost: **zero** (GitHub Pages).
- Fatal limits:
  - **No URL mode.** YouTube / Bilibili audio streams set CORS headers that
    forbid third-party pages from `fetch`-ing them. Only browser extensions
    (with `host_permissions`) can bypass this. A plain webpage cannot.
  - **Shazam's public endpoint doesn't return CORS headers.** Confirmed by the
    upstream `node-shazam-api` README: browser usage requires a userscript to
    override CORS.
  - AudD does support browser CORS but its catalog is weaker on J-Pop and
    Chinese indie, and requires per-user API keys.

### Option B — Browser fingerprint + Cloudflare Worker CORS proxy

- Frontend does the fingerprinting (shazamio-core compiled to WASM already
  exists as [`Inrixia/shazamio-core`](https://github.com/Inrixia/shazamio-core)).
- Worker is <100 lines, forwards the tiny signature blob to Shazam and adds
  CORS headers back.
- Server cost: essentially zero (CF Worker free tier = 100k req/day, CPU
  <10ms/req, payload <1KB).
- Still no URL mode (see A). Anyone with the page URL could burn your Worker
  budget if you don't add auth on top.

### Option C — Keep the current Python backend, but private and sleepy

- Reuse everything we already built: [downloader.py](../../src/tunefinder/downloader.py),
  [recognizer.py](../../src/tunefinder/recognizer.py), [pipeline.py](../../src/tunefinder/pipeline.py),
  [web/server.py](../../src/tunefinder/web/server.py).
- Deploy to a "scale-to-zero" host (Fly.io / Railway free tier) — container
  sleeps when idle, wakes on request in ~3–5 s.
- Put an access gate in front so it's **not a public service**.

## 3. Why Option C wins _once we accept a scope constraint_

The moment we say **"I don't need this to be open to the world; it's for me and
a few friends, used infrequently"** — every downside of A/B disappears:

| Concern that killed A/B | Under C, when it's private + low-frequency |
| --- | --- |
| YouTube audio has CORS | Server has yt-dlp; no browser involved for downloads |
| Shazam API blocks browsers | Server calls Shazamio directly (already works) |
| Server bandwidth/CPU cost | Sleeps 95%+ of the day; free tier is enormous relative to a few daily requests |
| Getting flooded / abused | Access list blocks it entirely |

So the constraint _is_ the design.

## 4. Reference architecture (for the day we build it)

```
You (or an invited friend)
    │
    ▼   https://tunefinder.<your-domain>/
Cloudflare Access  (free for up to 50 users)
    │   Only lets through emails on your allowlist
    ▼
Fly.io / Railway container (free tier, scale-to-zero)
    ├─ Idle: 0 CPU, 0 memory, container hibernated
    ├─ On request: cold-start ~3–5 s, run existing FastAPI
    └─ Auto-sleep after N minutes of no traffic
```

### Ballpark cost (personal use, ~5 recognitions/day)

| Line item | Free quota | Expected usage | % of quota |
| --- | --- | --- | --- |
| Fly.io shared-cpu-1x + 256MB | ~2340 CPU-h / month | ~2.5 CPU-h / month | 0.1% |
| Fly.io egress | 100 GB / month | ~500 MB / month | 0.5% |
| Cloudflare Access users | 50 users | 1–5 | trivial |
| Domain | not included | reuse existing | — |

Net expected monthly bill: **¥0**.

## 5. Three access-control tiers, cheapest first

### Tier 1 — URL token (30 lines of code)

Add a FastAPI dependency to [web/server.py](../../src/tunefinder/web/server.py):

```python
from fastapi import Header, HTTPException
import os, secrets


def require_token(x_api_key: str | None = Header(None)) -> None:
    expected = os.environ["TUNEFINDER_API_KEY"]
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401)
```

- Share `https://tunefinder.example.com/?k=xxx`; frontend puts `k` in a header.
- Rotate the token to revoke.
- Slots naturally into the existing `TUNEFINDER_` env-var scheme in
  [config.py](../../src/tunefinder/config.py).

### Tier 2 — Cloudflare Access (recommended, zero code)

- Wrap the Fly.io container with a Cloudflare Tunnel + Access policy.
- Users authenticate with Google / GitHub / one-time email code.
- Allowlist by email or org — revoke by removing a row in the dashboard.
- **Zero application-code change.** This is the highest leverage lego brick.

### Tier 3 — Fully private via Tailscale

- Deploy the FastAPI app to a home Mac Mini / Raspberry Pi.
- Only reachable inside your Tailscale tailnet.
- No public exposure at all. Highest privacy, lowest availability.

## 6. Two additional cheap wins to bake in later

### 6a. Result cache

Because usage is low-frequency, the _same_ URLs will be re-recognized (rewatching
a short, sharing with a friend). A 30-line SQLite k/v in [pipeline.py](../../src/tunefinder/pipeline.py):

```
key   = sha256(normalized_url)  or  sha256(first-30s-PCM)
value = RecognitionResult JSON
```

Second hit → ~100 ms return, no yt-dlp, no Shazam call. This cuts almost all
recurring cost.

### 6b. Rate limit

Even behind Access, add `slowapi` (3 req/min/IP) to protect against fat-finger
loops and accidental infinite refreshes. Ten lines.

## 7. Minimal path to ship (when we come back to this)

1. Add a `Dockerfile` + `fly.toml`; existing [pyproject.toml](../../pyproject.toml)
   already declares all runtime deps.
2. Add SQLite result cache in [pipeline.py](../../src/tunefinder/pipeline.py).
3. Add `slowapi` middleware in [web/server.py](../../src/tunefinder/web/server.py).
4. Put a Cloudflare Tunnel + Access policy in front. No app code change.
5. Optional: add `TUNEFINDER_API_KEY` in [config.py](../../src/tunefinder/config.py)
   as a second layer of defence for CLI/API automation.

Rough estimate: ~2 hours end-to-end, most of it clicking around Cloudflare
and Fly.io dashboards.

## 8. Explicit non-goals of this idea

- Not building a public / open recognition service.
- Not building a browser extension or Tauri desktop app (would unblock URL
  mode client-side, but is a much bigger scope).
- Not swapping the backend away from Shazamio — the whole point is to reuse
  today's working pipeline.
- Not adding user accounts, teams, billing, or any SaaS scaffolding.
