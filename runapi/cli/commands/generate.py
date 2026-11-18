"""`runapi generate`: boilerplate generators (route, schema, repository, service, crud, ...)."""

from pathlib import Path
from typing import List

import typer

from .._app import app, console
from .._templates import class_name_for, render

GENERATORS = "route, schema, repository, service, crud, main, middleware"


@app.command()
def generate(
    item: str = typer.Argument(
        ...,
        help="What to generate (route, schema, repository, service, crud, main, middleware)",
    ),
    name: str = typer.Argument(..., help="Name of the item"),
    path: str = typer.Option("", "--path", "-p", help="Path for the item"),
):
    """Generate boilerplate code."""
    if item == "route":
        _generate_route(name, path)
    elif item == "schema":
        _generate_schema(name, path)
    elif item == "repository":
        _generate_repository(name, path)
    elif item == "service":
        _generate_service(name, path)
    elif item == "crud":
        _generate_crud(name)
    elif item == "main":
        _generate_main()
    elif item == "middleware":
        _generate_middleware(name)
    else:
        console.print(f"[red]❌ Unknown generator: {item}")
        console.print(f"Available generators: {GENERATORS}")
        raise typer.Exit(code=1)


def _scaffold(directory: str, label: str, name: str, path: str, template: str) -> Path:
    """Create ``<directory>/<path>/<name>.py`` from a template. Refuses to overwrite."""
    base = Path(directory)
    base.mkdir(exist_ok=True)
    (base / "__init__.py").touch()

    if path:
        base = base / path
        base.mkdir(parents=True, exist_ok=True)
        (base / "__init__.py").touch()

    file_path = base / f"{name}.py"
    if file_path.exists():
        console.print(f"[red]❌ {label} already exists: {file_path}")
        raise typer.Exit(code=1)

    file_path.write_text(
        render(template, name=name, class_name=class_name_for(name)), encoding="utf-8"
    )
    console.print(f"✅ [green]{label} created: {file_path}")
    return file_path


def _generate_route(name: str, path: str):
    file_path = _scaffold("routes", "Route", name, path, "generate/route.py")
    route_url = "/" + str(file_path.relative_to("routes")).replace("\\", "/").replace(".py", "")
    if route_url.endswith("/index"):
        route_url = route_url[:-6] or "/"
    console.print(f"🌐 URL: {route_url}")


def _generate_schema(name: str, path: str):
    _scaffold("schemas", "Schema", name, path, "generate/schema.py")
    cls = class_name_for(name)
    console.print(f"📦 Classes: {cls}Base, {cls}Create, {cls}Update, {cls}Response, {cls}List")


def _generate_repository(name: str, path: str):
    _scaffold("repositories", "Repository", name, path, "generate/repository.py")
    console.print(f"📦 Class: {class_name_for(name)}Repository")


def _generate_service(name: str, path: str):
    _scaffold("services", "Service", name, path, "generate/service.py")
    console.print(f"📦 Class: {class_name_for(name)}Service")


def _generate_middleware(name: str):
    base = Path("middleware")
    base.mkdir(exist_ok=True)
    (base / "__init__.py").touch()
    file_path = base / f"{name}.py"
    if file_path.exists():
        console.print(f"[red]❌ Middleware already exists: {file_path}")
        raise typer.Exit(code=1)
    file_path.write_text(
        render("generate/middleware.py", name=name, class_name=class_name_for(name)),
        encoding="utf-8",
    )
    console.print(f"✅ [green]Middleware created: {file_path}")


def _generate_main():
    main_path = Path("main.py")
    if main_path.exists() and not typer.confirm("main.py already exists. Overwrite?"):
        raise typer.Exit()
    main_path.write_text(render("generate/main.py"), encoding="utf-8")
    console.print("✅ [green]main.py created successfully!")


def _generate_crud(name: str):
    """Generate schema + repository + service + REST routes for a resource."""
    if not name.replace("_", "").replace("-", "").isalnum():
        console.print("[red]❌ Name may only contain letters, numbers, '-' and '_'")
        raise typer.Exit(code=1)
    name = name.replace("-", "_")
    cls = class_name_for(name)

    targets: List[Path] = [
        Path("schemas") / f"{name}.py",
        Path("repositories") / f"{name}.py",
        Path("services") / f"{name}.py",
        Path("routes") / name / "index.py",
        Path("routes") / name / "[id].py",
    ]
    existing = [str(p) for p in targets if p.exists()]
    if existing:
        console.print(f"[red]❌ Refusing to overwrite: {', '.join(existing)}")
        raise typer.Exit(code=1)

    _generate_schema(name, "")
    _generate_repository(name, "")
    _generate_service(name, "")

    context = {"name": name, "class_name": cls}
    # A shared service instance: regular imports are cached, so every route sees the same one
    with open(Path("services") / f"{name}.py", "a", encoding="utf-8") as f:
        f.write(render("generate/crud_service_footer.py", **context))

    route_dir = Path("routes") / name
    route_dir.mkdir(parents=True, exist_ok=True)
    (route_dir / "__init__.py").touch()
    (route_dir / "index.py").write_text(
        render("generate/crud_index.py", **context), encoding="utf-8"
    )
    (route_dir / "[id].py").write_text(render("generate/crud_item.py", **context), encoding="utf-8")

    console.print(f"✅ [green]CRUD resource '{name}' created")
    console.print(f"🌐 Routes: GET/POST /{name}   GET/PUT/DELETE /{name}/{{id}}")
    console.print("   (data is stored in memory; swap the repository for a database in production)")
