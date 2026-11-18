"""Read-only commands: routes, schemas, info, doctor."""

import sys
from pathlib import Path

import typer
from rich.markup import escape
from rich.table import Table

from ... import __version__
from ...config import load_config
from ...routing import discover_routes
from .._app import app, console


@app.command()
def routes():
    """List all available routes in the project."""
    routes_path = Path("routes")
    if not routes_path.exists():
        console.print("[red]❌ No routes directory found")
        raise typer.Exit(code=1)

    console.print("📋 [bold blue]Available Routes[/bold blue]\n")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Method")
    table.add_column("Path")
    table.add_column("File")

    for route in discover_routes(routes_path):
        route_file = route.file
        relative_path = route_file.relative_to(routes_path)
        url_path = route.full_path

        # Read file to detect HTTP methods
        try:
            content = route_file.read_text()
            import ast

            try:
                tree = ast.parse(content)
                methods = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name in [
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                            "head",
                            "options",
                        ]:
                            methods.append(node.name.upper())
                        elif node.name == "websocket":
                            methods.append("WS")

                # Deduplicate and sort
                methods = sorted(set(methods))
                methods_str = ", ".join(methods) if methods else "No methods found"
                table.add_row(methods_str, escape(url_path), escape(str(relative_path)))
            except SyntaxError:
                table.add_row("Error", url_path, "Syntax Error in file")

        except Exception as e:
            table.add_row("Error", url_path, f"Error reading file: {e}")

    console.print(table)


@app.command()
def schemas():
    """List all available schemas in the project."""
    schemas_path = Path("schemas")
    if not schemas_path.exists():
        console.print("[yellow]⚠️  No schemas directory found")
        console.print("[dim]💡 Tip: Run 'runapi generate schema user' to create your first schema")
        raise typer.Exit(code=0)

    console.print("📋 [bold blue]Available Schemas[/bold blue]\n")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("File")
    table.add_column("Classes")
    table.add_column("Module Path")

    schema_count = 0
    for schema_file in schemas_path.rglob("*.py"):
        if schema_file.name == "__init__.py":
            continue

        relative_path = schema_file.relative_to(schemas_path)
        module_path = "schemas." + str(relative_path).replace("\\", ".").replace("/", ".").replace(
            ".py", ""
        )

        # Read file to detect Pydantic model classes
        try:
            content = schema_file.read_text()
            import ast

            try:
                tree = ast.parse(content)
                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it's likely a Pydantic model (inherits from something)
                        if node.bases:
                            classes.append(node.name)

                classes_str = ", ".join(classes) if classes else "No classes found"
                table.add_row(str(relative_path), classes_str, module_path)
                schema_count += 1
            except SyntaxError:
                table.add_row(str(relative_path), "[red]Syntax Error", module_path)

        except Exception as e:
            table.add_row(str(relative_path), f"[red]Error: {e}", module_path)

    if schema_count > 0:
        console.print(table)
        console.print(f"\n[dim]Total: {schema_count} schema file(s)")
    else:
        console.print("[yellow]No schema files found in schemas/ directory")
        console.print("[dim]💡 Tip: Run 'runapi generate schema user' to create a schema")


@app.command()
def doctor():
    """Check the environment and project for common problems."""

    problems = 0

    def check(ok: bool, label: str, hint: str = ""):
        nonlocal problems
        if ok:
            console.print(f"✅ {label}")
        else:
            problems += 1
            console.print(f"❌ {label}" + (f" - [yellow]{hint}[/yellow]" if hint else ""))

    check(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "requires Python 3.10+")
    check(True, f"runapi {__version__}")
    check(Path("main.py").exists(), "main.py found", "run from your project root")
    check(Path("routes").is_dir(), "routes/ directory found", "create a routes/ directory")
    config = load_config()
    result = config.validate_settings()
    for error in result["errors"]:
        check(False, "Configuration", error)
    for warning in result["warnings"]:
        console.print(f"⚠️  {warning}")
    if not result["errors"]:
        check(True, f"Configuration ({config.environment})")

    if problems:
        console.print(f"\n[red]{problems} problem(s) found[/red]")
        raise typer.Exit(code=1)
    console.print("\n[green]All checks passed[/green]")


@app.command()
def info():
    """Show project information and configuration."""
    console.print("ℹ️  [bold blue]RunApi Project Information[/bold blue]\n")

    # Load config
    config = load_config()

    # Project info
    info_table = Table(show_header=False, box=None)
    info_table.add_row("📁 Project Directory:", str(Path.cwd()))
    info_table.add_row("🐍 RunApi Version:", __version__)

    # Check main.py
    if Path("main.py").exists():
        info_table.add_row("📄 Entry Point:", "main.py ✅")
    else:
        info_table.add_row("📄 Entry Point:", "main.py ❌")

    # Check routes
    routes_path = Path("routes")
    if routes_path.exists():
        route_count = len([f for f in routes_path.rglob("*.py") if f.name != "__init__.py"])
        info_table.add_row("🛣️  Routes:", f"{route_count} files")
    else:
        info_table.add_row("🛣️  Routes:", "No routes directory")

    # Check schemas
    schemas_path = Path("schemas")
    if schemas_path.exists():
        schema_count = len([f for f in schemas_path.rglob("*.py") if f.name != "__init__.py"])
        info_table.add_row("📦 Schemas:", f"{schema_count} files")
    else:
        info_table.add_row("📦 Schemas:", "No schemas directory")

    console.print(info_table)
    console.print()

    # Configuration
    config_table = Table(show_header=True, header_style="bold blue", title="Configuration")
    config_table.add_column("Setting")
    config_table.add_column("Value")

    config_table.add_row("Debug", "✅ Enabled" if config.debug else "❌ Disabled")
    config_table.add_row("Host", config.host)
    config_table.add_row("Port", str(config.port))
    config_table.add_row("CORS Origins", ", ".join(config.cors_origins))
    config_table.add_row(
        "Rate Limiting", "✅ Enabled" if config.rate_limit_enabled else "❌ Disabled"
    )
    config_table.add_row("Log Level", config.log_level)

    console.print(config_table)
