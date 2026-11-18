"""`runapi init`: scaffold a new project."""

import os
import secrets
from pathlib import Path

import typer

from ... import __version__
from .._app import app, console
from .._templates import render

_PACKAGES = ["routes", "schemas", "repositories", "services"]


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
    docker: bool = typer.Option(False, "--docker", help="Also generate a Dockerfile"),
):
    """Initialize a new RunApi project."""
    project_path = Path(name)

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
    console.print("   runapi dev")
