"""`runapi init`: scaffold a new project."""

import os
import secrets
from pathlib import Path

import typer

from ... import __version__
from .._app import app, console
from .._templates import render

_PACKAGES = ["routes", "schemas", "repositories", "services"]
DB_CHOICES = ("none", "sqlite", "postgres")
_DATABASE_URLS = {
    "sqlite": "sqlite+aiosqlite:///./app.db",
    "postgres": "postgresql+asyncpg://app:app@localhost:5432/app",
}


def _scaffold_database(project_path: Path, db: str) -> None:
    """Add models, a session object, migrations and (for PostgreSQL) a compose file."""
    from .db import write_migrations_scaffold

    (project_path / "models").mkdir()
    (project_path / "models" / "__init__.py").write_text(
        render("db/models_init.py"), encoding="utf-8"
    )
    (project_path / "models" / "item.py").write_text(render("db/models_item.py"), encoding="utf-8")
    (project_path / "db.py").write_text(render("db/db.py"), encoding="utf-8")
    (project_path / "main.py").write_text(render("db/main.py"), encoding="utf-8")
    (project_path / "routes" / "api" / "items.py").write_text(
        render("db/route_items.py"), encoding="utf-8"
    )
    write_migrations_scaffold(project_path)

    env_path = project_path / ".env"
    env_path.write_text(
        env_path.read_text(encoding="utf-8") + f"\n# Database\nDATABASE_URL={_DATABASE_URLS[db]}\n",
        encoding="utf-8",
    )
    version = __version__.split("+")[0].split(".dev")[0]
    (project_path / "requirements.txt").write_text(f"runapi[{db}]>={version}\n", encoding="utf-8")
    if db == "postgres":
        (project_path / "docker-compose.yml").write_text(
            render("db/docker-compose.yml"), encoding="utf-8"
        )
    (project_path / ".env.example").write_text(
        f"SECRET_KEY=change-me\nDATABASE_URL={_DATABASE_URLS[db]}\n", encoding="utf-8"
    )


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
    docker: bool = typer.Option(False, "--docker", help="Also generate a Dockerfile"),
    db: str = typer.Option(
        "none", "--db", help="Database to set up: none, sqlite or postgres", show_default=True
    ),
):
    """Initialize a new RunApi project."""
    project_path = Path(name)

    if db not in DB_CHOICES:
        console.print(f"[red]❌ --db must be one of: {', '.join(DB_CHOICES)}")
        raise typer.Exit(code=1)

    if project_path.exists():
        console.print(f"[red]❌ Directory '{name}' already exists")
        raise typer.Exit(code=1)

    console.print(f"🚀 [bold blue]Creating RunApi project: {name}[/bold blue]")

    project_path.mkdir()
    for package in _PACKAGES:
        (project_path / package).mkdir()
        (project_path / package / "__init__.py").touch()
    (project_path / "static").mkdir()
    (project_path / "uploads").mkdir()

    routes_api = project_path / "routes" / "api"
    routes_api.mkdir()
    (routes_api / "__init__.py").touch()

    files = {
        "main.py": "project/main.py",
        "routes/api/hello.py": "project/route_hello.py",
        "routes/index.py": "project/route_index.py",
        ".env": "project/env",
        ".gitignore": "project/gitignore",
        "README.md": "project/README.md",
    }
    for target, template_name in files.items():
        content = render(template_name, project_name=name, secret_key=secrets.token_hex(32))
        (project_path / target).write_text(content, encoding="utf-8")

    if db != "none":
        _scaffold_database(project_path, db)

    if docker:
        requirements = project_path / "requirements.txt"
        if not requirements.exists():
            version = __version__.split("+")[0].split(".dev")[0]
            requirements.write_text(f"runapi>={version}\n", encoding="utf-8")
        (project_path / "Dockerfile").write_text(render("project/Dockerfile"), encoding="utf-8")
        (project_path / ".dockerignore").write_text(
            render("project/dockerignore"), encoding="utf-8"
        )

    console.print("✅ [green]Project created successfully!")
    console.print("\n📁 Project structure:")
    for root, _dirs, filenames in os.walk(project_path):
        level = root.replace(str(project_path), "").count(os.sep)
        console.print(f"{' ' * 2 * level}{os.path.basename(root)}/")
        for filename in filenames:
            console.print(f"{' ' * 2 * (level + 1)}{filename}")

    console.print("\n🚀 To get started:")
    console.print(f"   cd {name}")
    if db != "none":
        console.print(f"   pip install -r requirements.txt   # installs runapi[{db}]")
        if db == "postgres":
            console.print("   docker compose up -d db            # start PostgreSQL")
        console.print("   runapi db migrate -m 'create items'")
        console.print("   runapi db upgrade")
    console.print("   runapi dev")
