# pynextapi/cli.py
import typer
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
import os
import shutil
from typing import Optional

from .config import load_config, PyNextConfig
from .core import create_pynext_app

app = typer.Typer(name="pynext", help="PyNext - Next.js-inspired Python Backend Framework")
console = Console()


@app.command()
def dev(
    host: str = typer.Option(None, "--host", "-h", help="Host to bind"),
    port: int = typer.Option(None, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(None, "--reload/--no-reload", help="Enable auto-reload"),
    config_file: str = typer.Option(".env", "--config", "-c", help="Configuration file"),
    log_level: str = typer.Option(None, "--log-level", "-l", help="Log level"),
):
    """Run the PyNext development server."""
    console.print(Panel.fit("🚀 [bold blue]PyNext Development Server[/bold blue]", style="blue"))
    
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
        console.print("[yellow]💡 Tip: Run 'pynext init' to create a new project or 'pynext generate main' to create main.py")
        raise typer.Exit(code=1)
    
    # Display server info
    table = Table(show_header=False, box=None)
    table.add_row("🌐 Server:", f"http://{config.host}:{config.port}")
    table.add_row("🔄 Reload:", "✅ Enabled" if config.reload else "❌ Disabled")
    table.add_row("📝 Log Level:", config.log_level.upper())
    table.add_row("⚙️  Config:", config_file if Path(config_file).exists() else "Default")
    console.print(table)
    
    # Check for routes directory
    routes_path = Path("routes")
    if routes_path.exists():
        route_count = len([f for f in routes_path.rglob("*.py") if f.name != "__init__.py"])
        console.print(f"📁 Found {route_count} route files in ./routes/")
    else:
        console.print("[yellow]⚠️  No routes directory found")
    
    console.print()
    
    try:
        # Run uvicorn with the FastAPI app
        uvicorn.run(
            "main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            log_level=config.log_level.lower(),
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Server stopped")


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
):
    """Initialize a new PyNext project."""
    project_path = Path(name)
    
    if project_path.exists():
        console.print(f"[red]❌ Directory '{name}' already exists")
        raise typer.Exit(code=1)
    
    console.print(f"🚀 [bold blue]Creating PyNext project: {name}[/bold blue]")
    
    # Create project directory
    project_path.mkdir()
    
    # Create basic project structure
    (project_path / "routes").mkdir()
    (project_path / "routes" / "__init__.py").touch()
    (project_path / "static").mkdir()
    (project_path / "uploads").mkdir()
    
    # Create main.py
    main_content = '''"""
PyNext Application Entry Point
"""
from pynext import create_pynext_app

# Create PyNext application
pynext_app = create_pynext_app(
    title="My PyNext API",
    description="Built with PyNext framework",
    version="1.0.0"
)

# Get FastAPI app for uvicorn
app = pynext_app.get_app()

if __name__ == "__main__":
    pynext_app.run()
'''
    
    (project_path / "main.py").write_text(main_content)
    
    # Create example route
    routes_api_path = project_path / "routes" / "api"
    routes_api_path.mkdir()
    (routes_api_path / "__init__.py").touch()
    
    example_route = '''"""
Example API route
GET /api/hello
"""
from pynext import JSONResponse

async def get():
    return JSONResponse({
        "message": "Hello from PyNext!",
        "framework": "PyNext",
        "status": "success"
    })
'''
    
    (routes_api_path / "hello.py").write_text(example_route)
    
    # Create index route
    index_route = '''"""
Home page route
GET /
"""
from pynext import JSONResponse

async def get():
    return JSONResponse({
        "message": "Welcome to PyNext!",
        "docs": "/docs",
        "routes": {
            "hello": "/api/hello"
        }
    })
'''
    
    (project_path / "routes" / "index.py").write_text(index_route)
    
    # Create .env file
    env_content = '''# PyNext Configuration
DEBUG=true
HOST=127.0.0.1
PORT=8000
SECRET_KEY=dev-secret-key-change-in-production

# CORS Settings
CORS_ORIGINS=*
CORS_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=INFO

# Static Files
STATIC_FILES_ENABLED=true
STATIC_FILES_PATH=static
STATIC_FILES_URL=/static
'''
    
    (project_path / ".env").write_text(env_content)
    
    # Create .gitignore
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# PyNext
.env
uploads/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
'''
    
    (project_path / ".gitignore").write_text(gitignore_content)
    
    # Create README
    readme_content = f'''# {name}

A PyNext API project.

## Getting Started

1. Install dependencies:
   ```bash
   pip install pynext
   ```

2. Run development server:
   ```bash
   cd {name}
   pynext dev
   ```

3. Open http://localhost:8000

## Project Structure

```
{name}/
├── routes/           # API routes (file-based routing)
│   ├── index.py     # GET /
│   └── api/
│       └── hello.py # GET /api/hello
├── static/          # Static files
├── uploads/         # File uploads
├── main.py          # Application entry point
└── .env            # Configuration
```

## Available Routes

- `GET /` - Home page
- `GET /api/hello` - Example API endpoint
- `GET /docs` - API documentation

## Adding Routes

Create Python files in the `routes/` directory:

- `routes/users.py` → `GET /users`
- `routes/api/users/[id].py` → `GET /api/users/123`
- `routes/api/auth/login.py` → `GET /api/auth/login`

Export HTTP method functions:

```python
async def get():
    return {{"message": "GET request"}}

async def post():
    return {{"message": "POST request"}}
```
'''
    
    (project_path / "README.md").write_text(readme_content)
    
    console.print("✅ [green]Project created successfully!")
    console.print(f"\n📁 Project structure:")
    
    # Show project structure
    for root, dirs, files in os.walk(project_path):
        level = root.replace(str(project_path), '').count(os.sep)
        indent = ' ' * 2 * level
        console.print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            console.print(f"{subindent}{file}")
    
    console.print(f"\n🚀 To get started:")
    console.print(f"   cd {name}")
    console.print(f"   pynext dev")


@app.command()
def generate(
    item: str = typer.Argument(..., help="What to generate (route, main, middleware)"),
    name: str = typer.Argument(..., help="Name of the item"),
    path: str = typer.Option("", "--path", "-p", help="Path for the item"),
):
    """Generate boilerplate code."""
    if item == "route":
        _generate_route(name, path)
    elif item == "main":
        _generate_main()
    elif item == "middleware":
        _generate_middleware(name)
    else:
        console.print(f"[red]❌ Unknown generator: {item}")
        console.print("Available generators: route, main, middleware")
        raise typer.Exit(code=1)


def _generate_route(name: str, path: str):
    """Generate a new route file."""
    routes_path = Path("routes")
    if not routes_path.exists():
        routes_path.mkdir()
        (routes_path / "__init__.py").touch()
    
    if path:
        route_path = routes_path / path
        route_path.mkdir(parents=True, exist_ok=True)
        (route_path / "__init__.py").touch()
        file_path = route_path / f"{name}.py"
    else:
        file_path = routes_path / f"{name}.py"
    
    if file_path.exists():
        console.print(f"[red]❌ Route already exists: {file_path}")
        raise typer.Exit(code=1)
    
    # Generate route template
    route_template = f'''"""
{name.title()} route
Generated by PyNext CLI
"""
from pynext import JSONResponse, HTTPException, Request

async def get(request: Request):
    """Handle GET request."""
    return JSONResponse({{
        "message": "Hello from {name}!",
        "method": "GET",
        "path": str(request.url.path)
    }})

async def post(request: Request):
    """Handle POST request."""
    # Get request body
    body = await request.json()
    
    return JSONResponse({{
        "message": "Data received",
        "method": "POST", 
        "data": body
    }})

# Uncomment and implement other HTTP methods as needed:

# async def put(request: Request):
#     """Handle PUT request."""
#     pass

# async def delete(request: Request):
#     """Handle DELETE request."""
#     pass

# async def patch(request: Request):
#     """Handle PATCH request."""
#     pass
'''
    
    file_path.write_text(route_template)
    console.print(f"✅ [green]Route created: {file_path}")
    
    # Show URL mapping
    route_url = "/" + str(file_path.relative_to(routes_path)).replace("\\", "/").replace(".py", "")
    if route_url.endswith("/index"):
        route_url = route_url[:-6] or "/"
    console.print(f"🌐 URL: {route_url}")


def _generate_main():
    """Generate main.py file."""
    main_path = Path("main.py")
    if main_path.exists():
        if not typer.confirm("main.py already exists. Overwrite?"):
            raise typer.Exit()
    
    main_content = '''"""
PyNext Application Entry Point
"""
from pynext import create_pynext_app, get_config

# Load configuration
config = get_config()

# Create PyNext application
pynext_app = create_pynext_app(
    title="My PyNext API",
    description="Built with PyNext framework",
    version="1.0.0"
)

# Add custom middleware if needed
# pynext_app.add_auth_middleware(protected_paths=["/api/protected"])

# Get FastAPI app for uvicorn
app = pynext_app.get_app()

if __name__ == "__main__":
    pynext_app.run()
'''
    
    main_path.write_text(main_content)
    console.print("✅ [green]main.py created successfully!")


def _generate_middleware(name: str):
    """Generate a custom middleware file."""
    middleware_path = Path("middleware")
    middleware_path.mkdir(exist_ok=True)
    (middleware_path / "__init__.py").touch()
    
    file_path = middleware_path / f"{name}.py"
    
    if file_path.exists():
        console.print(f"[red]❌ Middleware already exists: {file_path}")
        raise typer.Exit(code=1)
    
    middleware_template = f'''"""
{name.title()} middleware
Generated by PyNext CLI
"""
from pynext import PyNextMiddleware, Request, Response
from typing import Callable

class {name.title()}Middleware(PyNextMiddleware):
    """Custom {name} middleware."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        # Initialize middleware parameters
        pass
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response."""
        # Pre-processing
        print(f"Processing request: {{request.method}} {{request.url.path}}")
        
        # Call next middleware/route
        response = await call_next(request)
        
        # Post-processing
        print(f"Response status: {{response.status_code}}")
        
        return response

# Usage in main.py:
# from middleware.{name} import {name.title()}Middleware  
# pynext_app.add_middleware({name.title()}Middleware)
'''
    
    file_path.write_text(middleware_template)
    console.print(f"✅ [green]Middleware created: {file_path}")


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
    
    for route_file in routes_path.rglob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        # Generate URL path
        relative_path = route_file.relative_to(routes_path)
        url_path = "/" + str(relative_path).replace("\\", "/").replace(".py", "")
        
        if url_path.endswith("/index"):
            url_path = url_path[:-6] or "/"
        
        # Check for dynamic routes
        if "[" in url_path and "]" in url_path:
            # Convert [id] to {id}
            import re
            url_path = re.sub(r'\[([^\]]+)\]', r'{\1}', url_path)
        
        # Read file to detect HTTP methods
        try:
            content = route_file.read_text()
            methods = []
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if f"async def {method}(" in content or f"def {method}(" in content:
                    methods.append(method.upper())
            
            methods_str = ", ".join(methods) if methods else "No methods found"
            table.add_row(methods_str, url_path, str(relative_path))
            
        except Exception as e:
            table.add_row("Error", url_path, f"Error reading file: {e}")
    
    console.print(table)


@app.command()  
def info():
    """Show project information and configuration."""
    console.print("ℹ️  [bold blue]PyNext Project Information[/bold blue]\n")
    
    # Load config
    config = load_config()
    
    # Project info
    info_table = Table(show_header=False, box=None)
    info_table.add_row("📁 Project Directory:", str(Path.cwd()))
    info_table.add_row("🐍 PyNext Version:", "0.1.0")
    
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
    config_table.add_row("Rate Limiting", "✅ Enabled" if config.rate_limit_enabled else "❌ Disabled")
    config_table.add_row("Log Level", config.log_level)
    
    console.print(config_table)


if __name__ == "__main__":
    app()