"""`runapi dev` and `runapi start`."""

import os
from pathlib import Path

import typer
import uvicorn
from rich.panel import Panel
from rich.table import Table

from ...config import load_config
from .._app import app, console


@app.command()
def dev(
    host: str = typer.Option(None, "--host", "-h", help="Host to bind"),
    port: int = typer.Option(None, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(None, "--reload/--no-reload", help="Enable auto-reload"),
    config_file: str = typer.Option(".env", "--config", "-c", help="Configuration file"),
    log_level: str = typer.Option(None, "--log-level", "-l", help="Log level"),
):
    """Run the RunApi development server."""
    console.print(Panel.fit("🚀 [bold blue]RunApi Development Server[/bold blue]", style="blue"))

    # Load configuration
    config = load_config(config_file)

    # Override config with CLI arguments if provided
    if host:
        config.host = host
    if port:
        config.port = port
    if reload is not None:
        config.reload = reload
    if log_level:
        config.log_level = log_level

    # Check if main.py exists
    main_path = Path("main.py")
    if not main_path.exists():
        console.print("[red]❌ Error: main.py not found in current directory")
        console.print(
            "[yellow]💡 Tip: Run 'runapi init' to create a new project or 'runapi generate main' to create main.py"
        )
        raise typer.Exit(code=1)

    # Display server info
    table = Table(show_header=False, box=None)
    table.add_row("🌐 Server:", f"http://{config.host}:{config.port}")
    table.add_row("🔄 Reload:", "✅ Enabled" if config.reload else "❌ Disabled")
    table.add_row("📝 Log Level:", config.log_level.upper())
    table.add_row("⚙️  Config:", config_file if Path(config_file).exists() else "Default")
    console.print(table)

    # Check for routes directory
    if Path("routes").exists():
        console.print("📁 Routes directory detected")
    else:
        console.print("[yellow]⚠️  No routes directory found")

    # Check for schemas directory
    if Path("schemas").exists():
        console.print("📦 Schemas directory detected")
    else:
        console.print("[dim]📦 No schemas directory (optional)")

    console.print()

    try:
        # Ensure we're in the correct working directory
        import os
        import sys

        current_dir = os.getcwd()

        # Add current directory to Python path if not already there
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        # Verify main.py can be imported before starting server
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("main", "main.py")
            if spec is None or spec.loader is None:
                raise ImportError("Cannot load main.py")
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            console.print("✅ [green]main.py loaded successfully")
        except Exception as e:
            console.print(f"[red]❌ Error importing main.py: {e}")
            console.print(
                "[yellow]💡 Make sure main.py exists and runapi is installed in this environment"
            )
            raise typer.Exit(code=1) from e

        # Run uvicorn with the FastAPI app
        uvicorn.run(
            "main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            log_level=config.log_level.lower(),
            reload_dirs=[current_dir] if config.reload else None,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Server stopped")
    except Exception as e:
        console.print(f"[red]❌ Server error: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def start(
    host: str = typer.Option(None, "--host", "-h", help="Host to bind"),
    port: int = typer.Option(None, "--port", "-p", help="Port to bind"),
    workers: int = typer.Option(None, "--workers", "-w", help="Number of worker processes"),
    config_file: str = typer.Option(".env", "--config", "-c", help="Configuration file"),
    log_level: str = typer.Option(None, "--log-level", "-l", help="Log level"),
):
    """Run the RunApi server in production mode."""
    console.print(Panel.fit("🚀 [bold green]RunApi Production Server[/bold green]", style="green"))

    # `start` is production mode; worker processes inherit this through the environment
    os.environ.setdefault("ENVIRONMENT", "production")

    # Load configuration
    config = load_config(config_file)

    problems = config.validate_settings()
    for warning in problems["warnings"]:
        console.print(f"[yellow]⚠️  {warning}[/yellow]")
    if problems["errors"] and config.is_production():
        for error in problems["errors"]:
            console.print(f"[red]❌ {error}[/red]")
        console.print("[red]Refusing to start with an unsafe production configuration.[/red]")
        raise typer.Exit(code=1)

    # Override config with CLI arguments
    if host:
        config.host = host
    if port:
        config.port = port
    if log_level:
        config.log_level = log_level

    # Determine workers
    # If not specified in CLI, check env/config, else default to 1 (or cpu_count in real prod)
    # RunApiConfig doesn't have 'workers' yet, adding it logic here or just defaulting
    final_workers = workers or int(os.getenv("WORKERS", "1"))

    # Check if main.py exists
    if not Path("main.py").exists():
        console.print("[red]❌ Error: main.py not found")
        raise typer.Exit(code=1)

    # Display server info
    table = Table(show_header=False, box=None)
    table.add_row("🌐 Server:", f"http://{config.host}:{config.port}")
    table.add_row("⚙️  Mode:", "Production (No Reload)")
    table.add_row("👷 Workers:", str(final_workers))
    table.add_row("📝 Log Level:", config.log_level.upper())
    console.print(table)
    console.print()

    try:
        # Puts current dir in path
        import sys

        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())

        uvicorn.run(
            "main:app",
            host=config.host,
            port=config.port,
            workers=final_workers,
            reload=False,
            log_level=config.log_level.lower(),
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Server stopped")
    except Exception as e:
        console.print(f"[red]❌ Server error: {e}")
        raise typer.Exit(code=1) from e
