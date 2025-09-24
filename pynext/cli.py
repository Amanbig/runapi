# pynextapi/cli.py
import typer
import uvicorn
from rich.console import Console
from pathlib import Path

app = typer.Typer(name="pynextapi")
console = Console()

@app.command()
def dev(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
):
    """Run the PyNext development server."""
    console.print("[bold blue]🚀 Starting PyNextAPI development server...")
    
    # Check if main.py exists
    main_path = Path("main.py")
    if not main_path.exists():
        console.print("[red]Error: main.py not found in current directory")
        raise typer.Exit(code=1)
    
    # Run uvicorn with the FastAPI app
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )

if __name__ == "__main__":
    app()