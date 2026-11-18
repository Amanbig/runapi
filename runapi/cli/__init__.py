"""The ``runapi`` command-line interface.

Layout:
    _app.py        shared Typer ``app`` and ``console``
    _templates.py  renderer for the files the CLI generates
    commands/      one module per group of commands (importing registers them)
    templates/     the generated files themselves, as plain ``*.tmpl`` files
"""

import typer

from .. import __version__
from . import commands  # noqa: F401
from ._app import app, console
from .commands import db, generate, inspect, project, server  # noqa: F401  (registers commands)


def _version_callback(value: bool):
    if value:
        typer.echo(f"runapi {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the runapi version and exit.",
    ),
):
    """RunApi - Next.js-inspired Python Backend Framework."""


def main():
    """Main entry point for CLI."""
    from ..errors import ConfigurationError

    try:
        app()
    except ConfigurationError as exc:
        console.print(f"[red]❌ {exc}[/red]")
        raise SystemExit(1) from None


__all__ = ["app", "console", "main"]


if __name__ == "__main__":
    main()
