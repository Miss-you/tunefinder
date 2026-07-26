"""Unit tests for tunefinder.recognizer._parse_shazam.

These tests use a hand-crafted response payload shaped like Shazamio's real output.
They do NOT hit the network and do NOT require ffmpeg / shazamio to work.
"""

from __future__ import annotations

from tunefinder.recognizer import _parse_shazam


def _fake_track_response() -> dict:
    return {
        "matches": [{"id": "660662889", "offset": 12.34}],
        "timestamp": 1699999999,
        "track": {
            "key": "660662889",
            "title": "Mori No Chiisana Restaurant",
            "subtitle": "Aoi Teshima",
            "url": "https://www.shazam.com/track/660662889/mori-no-chiisana-restaurant",
            "isrc": "JPVI02301273",
            "genres": {"primary": "J-Pop"},
            "images": {
                "coverart": "https://example.com/cover.jpg",
                "coverarthq": "https://example.com/cover_hq.jpg",
            },
            "hub": {
                "actions": [
                    {"name": "apple", "type": "applemusicplay", "id": "xyz"},
                    {"type": "uri", "uri": "https://example.com/preview.m4a"},
                ],
                "options": [
                    {
                        "actions": [
                            {"type": "applemusicopen", "uri": "https://music.apple.com/song/1"},
                        ]
                    }
                ],
            },
            "sections": [
                {
                    "type": "SONG",
                    "metadata": [
                        {"title": "Album", "text": "The Best of Aoi"},
                        {"title": "Label", "text": "Victor"},
                    ],
                }
            ],
        },
    }


def test_parse_shazam_success() -> None:
    result = _parse_shazam(_fake_track_response())

    assert result.matched is True
    assert result.title == "Mori No Chiisana Restaurant"
    assert result.artist == "Aoi Teshima"
    assert result.album == "The Best of Aoi"
    assert result.genre == "J-Pop"
    assert result.isrc == "JPVI02301273"
    assert result.shazam_url and "shazam.com" in result.shazam_url
    assert result.cover_url == "https://example.com/cover_hq.jpg"
    assert result.preview_url == "https://example.com/preview.m4a"
    assert result.apple_music_url == "https://music.apple.com/song/1"


def test_parse_shazam_no_match_empty_payload() -> None:
    result = _parse_shazam({})
    assert result.matched is False
    assert result.title is None
    assert result.artist is None


def test_parse_shazam_no_match_no_track() -> None:
    result = _parse_shazam({"matches": [], "timestamp": 0})
    assert result.matched is False


def test_to_dict_keeps_raw_compact() -> None:
    result = _parse_shazam(_fake_track_response())
    d = result.to_dict()

    # Bulky "track" details must not leak into d["raw"] to keep API payloads small.
    assert set(d["raw"].keys()) <= {"matches", "location", "timestamp"}
    assert d["matched"] is True
    assert d["title"] == "Mori No Chiisana Restaurant"
