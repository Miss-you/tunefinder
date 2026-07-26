"""Smoke tests for the FastAPI app: only the network-free routes.

We assert the app boots, /api/health returns 200, and the static index page mounts.
Recognition endpoints are *not* exercised (they hit yt-dlp / Shazam).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tunefinder.web.server import app


def test_health_ok() -> None:
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_index_page_served() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "tunefinder" in resp.text.lower()


def test_recognize_url_rejects_empty_body() -> None:
    client = TestClient(app)
    resp = client.post("/api/recognize/url", json={"url": "   "})
    assert resp.status_code == 400
