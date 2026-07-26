"""CLI entry point."""
from __future__ import annotations

import json
import sys

import click

from . import pipeline


@click.group()
def cli() -> None:
    """tunefinder: recognize music from a URL or a local audio file."""


@cli.command()
@click.option("--url", "url", help="Video/audio URL (YouTube, Bilibili, ...)")
@click.option("--file", "file", type=click.Path(exists=True, dir_okay=False), help="Local audio file")
def recognize(url: str | None, file: str | None) -> None:
    """Recognize the music in the given URL or local file."""
    if not url and not file:
        raise click.UsageError("Provide either --url or --file")
    if url and file:
        raise click.UsageError("Use only one of --url / --file")

    result = pipeline.recognize_from_url(url) if url else pipeline.recognize_from_file(file)
    payload = result.to_dict()
    if result.matched:
        click.echo(f"🎵 {payload['title']} — {payload['artist']}")
        click.echo(f"   Genre : {payload['genre']}")
        click.echo(f"   Album : {payload['album']}")
        click.echo(f"   ISRC  : {payload['isrc']}")
        click.echo(f"   Shazam: {payload['shazam_url']}")
    else:
        click.echo("❌ No match.", err=True)
        sys.exit(2)
    click.echo("\n--- JSON ---")
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
@click.option("--reload/--no-reload", default=False)
def serve(host: str, port: int, reload: bool) -> None:
    """Start the web UI + JSON API."""
    import uvicorn

    uvicorn.run("tunefinder.web.server:app", host=host, port=port, reload=reload)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
