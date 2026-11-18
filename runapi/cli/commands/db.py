"""`runapi build` and the `runapi db` migration commands."""

import subprocess
import sys
from pathlib import Path

import typer

from .._app import app, console


@app.command()
def build(
    tag: str = typer.Option("runapi-app", "--tag", "-t", help="Docker image tag"),
    path: str = typer.Argument(".", help="Project directory"),
):
    """Build a Docker image for the project (requires Docker and a Dockerfile)."""
    project = Path(path)
    if not (project / "Dockerfile").exists():
        console.print("[red]❌ No Dockerfile found. Create one with: runapi init <name> --docker")
        raise typer.Exit(code=1)
    console.print(f"🐳 [bold blue]Building image {tag}[/bold blue]")
    try:
        result = subprocess.run(["docker", "build", "-t", tag, str(project)])
    except FileNotFoundError:
        console.print("[red]❌ Docker is not installed or not on PATH")
        raise typer.Exit(code=1) from None
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    console.print(f"✅ [green]Built {tag}[/green]  (run: docker run -p 8000:8000 {tag})")


db_app = typer.Typer(help="Database migrations (Alembic). Install with: pip install runapi\\[db]")
app.add_typer(db_app, name="db")


def _alembic(*args: str):
    try:
        import alembic  # noqa: F401
    except ImportError:
        console.print("[red]❌ Alembic is not installed. Run: pip install runapi\\[db]")
        raise typer.Exit(code=1) from None
    result = subprocess.run([sys.executable, "-m", "alembic", *args])
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@db_app.command("init")
def db_init(directory: str = typer.Option("migrations", help="Migrations directory")):
    """Initialise Alembic migrations (async-ready template)."""
    _alembic("init", "-t", "async", directory)


@db_app.command("migrate")
def db_migrate(message: str = typer.Option(..., "--message", "-m", help="Migration message")):
    """Autogenerate a new migration from model changes."""
    _alembic("revision", "--autogenerate", "-m", message)


@db_app.command("upgrade")
def db_upgrade(revision: str = typer.Argument("head")):
    """Apply migrations up to a revision (default: head)."""
    _alembic("upgrade", revision)


@db_app.command("downgrade")
def db_downgrade(revision: str = typer.Argument("-1")):
    """Revert migrations (default: one step)."""
    _alembic("downgrade", revision)
