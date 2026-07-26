"""Unit tests for tunefinder.downloader._find_result_file.

Uses tmp_path to fabricate the output files that yt-dlp *would* have written,
so we can assert the stdout-parsing logic without invoking the yt-dlp binary.
"""

from __future__ import annotations

from pathlib import Path

from tunefinder.downloader import _find_result_file


def test_find_result_file_from_destination(tmp_path: Path) -> None:
    audio = tmp_path / "yt_ABC.mp3"
    audio.write_bytes(b"fake-mp3-bytes")

    stdout = (
        "[youtube] ABC: Downloading webpage\n"
        f"[ExtractAudio] Destination: {audio}\n"
        "Deleting original file.\n"
    )
    assert _find_result_file(stdout, tmp_path) == audio


def test_find_result_file_from_already_downloaded(tmp_path: Path) -> None:
    audio = tmp_path / "yt_DEF.mp3"
    audio.write_bytes(b"fake-mp3-bytes")

    stdout = f"[download] {audio} has already been downloaded\n"
    assert _find_result_file(stdout, tmp_path) == audio


def test_find_result_file_missing_returns_none(tmp_path: Path) -> None:
    stdout = "[youtube] fetching metadata\nnothing useful here\n"
    assert _find_result_file(stdout, tmp_path) is None


def test_find_result_file_path_not_on_disk_returns_none(tmp_path: Path) -> None:
    # Path parsed successfully but the file doesn't exist -> we don't return a bogus path.
    stdout = f"[ExtractAudio] Destination: {tmp_path / 'not_there.mp3'}\n"
    assert _find_result_file(stdout, tmp_path) is None
