"""The shared Typer app and console used by every command module."""

import typer
from rich.console import Console

app = typer.Typer(name="runapi", help="RunApi - Next.js-inspired Python Backend Framework")
console = Console()
