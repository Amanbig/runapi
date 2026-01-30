# runapi/cli.py
import os
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import load_config

app = typer.Typer(name="runapi", help="RunApi - Next.js-inspired Python Backend Framework")
console = Console()


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
            if spec is None:
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

    # Load configuration
    config = load_config(config_file)

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


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
):
    """Initialize a new RunApi project."""
    project_path = Path(name)

    if project_path.exists():
        console.print(f"[red]❌ Directory '{name}' already exists")
        raise typer.Exit(code=1)

    console.print(f"🚀 [bold blue]Creating RunApi project: {name}[/bold blue]")

    # Create project directory
    project_path.mkdir()

    # Create basic project structure
    (project_path / "routes").mkdir()
    (project_path / "routes" / "__init__.py").touch()
    (project_path / "schemas").mkdir()
    (project_path / "schemas" / "__init__.py").touch()
    (project_path / "repositories").mkdir()
    (project_path / "repositories" / "__init__.py").touch()
    (project_path / "services").mkdir()
    (project_path / "services" / "__init__.py").touch()
    (project_path / "static").mkdir()
    (project_path / "uploads").mkdir()

    # Create main.py
    main_content = '''"""
RunApi Application Entry Point
"""
from runapi import create_runapi_app

# Create RunApi application
runapi_app = create_runapi_app(
    title="My RunApi API",
    description="Built with RunApi framework",
    version="1.0.0"
)

# Get FastAPI app for uvicorn
app = runapi_app.get_app()

if __name__ == "__main__":
    runapi_app.run()
'''

    (project_path / "main.py").write_text(main_content, encoding="utf-8")

    # Create example route
    routes_api_path = project_path / "routes" / "api"
    routes_api_path.mkdir()
    (routes_api_path / "__init__.py").touch()

    example_route = '''"""
Example API route
GET /api/hello
"""
from runapi import JSONResponse

async def get():
    return JSONResponse({
        "message": "Hello from RunApi!",
        "framework": "RunApi",
        "status": "success"
    })
'''

    (routes_api_path / "hello.py").write_text(example_route, encoding="utf-8")

    # Create index route
    index_route = '''"""
Home page route
GET /
"""
from runapi import JSONResponse

async def get():
    return JSONResponse({
        "message": "Welcome to RunApi!",
        "docs": "/docs",
        "routes": {
            "hello": "/api/hello"
        }
    })
'''

    (project_path / "routes" / "index.py").write_text(index_route, encoding="utf-8")

    # Create .env file
    env_content = """# RunApi Configuration
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
"""

    (project_path / ".env").write_text(env_content, encoding="utf-8")

    # Create .gitignore
    gitignore_content = """# Python
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

# RunApi
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
"""

    (project_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # Create README
    readme_content = f"""# {name}

A RunApi API project.

## Getting Started

1. Install dependencies:
   ```bash
   pip install runapi
   ```

2. Run development server:
   ```bash
   cd {name}
   runapi dev
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

- `routes/users.py` -> `GET /users`
- `routes/api/users/[id].py` -> `GET /api/users/123`
- `routes/api/auth/login.py` -> `GET /api/auth/login`

Export HTTP method functions:

```python
async def get():
    return {{"message": "GET request"}}

async def post():
    return {{"message": "POST request"}}
```
"""

    (project_path / "README.md").write_text(readme_content, encoding="utf-8")

    console.print("✅ [green]Project created successfully!")
    console.print("\n📁 Project structure:")

    # Show project structure
    for root, _dirs, files in os.walk(project_path):
        level = root.replace(str(project_path), "").count(os.sep)
        indent = " " * 2 * level
        console.print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            console.print(f"{subindent}{file}")

    console.print("\n🚀 To get started:")
    console.print(f"   cd {name}")
    console.print("   runapi dev")


@app.command()
def generate(
    item: str = typer.Argument(
        ..., help="What to generate (route, schema, repository, service, main, middleware)"
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
    elif item == "main":
        _generate_main()
    elif item == "middleware":
        _generate_middleware(name)
    else:
        console.print(f"[red]❌ Unknown generator: {item}")
        console.print("Available generators: route, schema, repository, service, main, middleware")
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
Generated by RunApi CLI
"""
from runapi import JSONResponse, HTTPException, Request

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

    file_path.write_text(route_template, encoding="utf-8")
    console.print(f"✅ [green]Route created: {file_path}")

    # Show URL mapping
    route_url = "/" + str(file_path.relative_to(routes_path)).replace("\\", "/").replace(".py", "")
    if route_url.endswith("/index"):
        route_url = route_url[:-6] or "/"
    console.print(f"🌐 URL: {route_url}")


def _generate_schema(name: str, path: str):
    """Generate a new schema file."""
    schemas_path = Path("schemas")
    if not schemas_path.exists():
        schemas_path.mkdir()
        (schemas_path / "__init__.py").touch()

    if path:
        schema_path = schemas_path / path
        schema_path.mkdir(parents=True, exist_ok=True)
        (schema_path / "__init__.py").touch()
        file_path = schema_path / f"{name}.py"
    else:
        file_path = schemas_path / f"{name}.py"

    if file_path.exists():
        console.print(f"[red]❌ Schema already exists: {file_path}")
        raise typer.Exit(code=1)

    # Convert name to PascalCase for class names
    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    schema_template = f'''"""
{class_name} schemas
Generated by RunApi CLI
"""
from runapi import BaseSchema, TimestampMixin, IDMixin
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime


class {class_name}Base(BaseSchema):
    """Base schema with shared fields."""
    name: str = Field(..., min_length=1, max_length=100, description="{class_name} name")
    # Add more shared fields here


class {class_name}Create({class_name}Base):
    """Schema for creating a new {name}."""
    pass
    # Add create-specific fields here (e.g., password for user)


class {class_name}Update(BaseSchema):
    """Schema for updating an existing {name}. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    # Add more updatable fields here


class {class_name}Response({class_name}Base, IDMixin, TimestampMixin):
    """Schema for {name} responses."""
    pass
    # Response includes id and timestamps from mixins


class {class_name}List(BaseSchema):
    """Schema for listing multiple {name}s."""
    items: list[{class_name}Response] = Field(default_factory=list)
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Example usage in routes:
#
# from schemas.{name} import {class_name}Create, {class_name}Response
#
# async def post(body: {class_name}Create) -> {class_name}Response:
#     # Create {name} logic
#     return {class_name}Response(id=1, name=body.name, created_at=datetime.now())
'''

    file_path.write_text(schema_template, encoding="utf-8")
    console.print(f"✅ [green]Schema created: {file_path}")
    console.print(
        f"📦 Classes: {class_name}Base, {class_name}Create, {class_name}Update, {class_name}Response, {class_name}List"
    )


def _generate_repository(name: str, path: str):
    """Generate a new repository file."""
    repos_path = Path("repositories")
    if not repos_path.exists():
        repos_path.mkdir()
        (repos_path / "__init__.py").touch()

    if path:
        repo_path = repos_path / path
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "__init__.py").touch()
        file_path = repo_path / f"{name}.py"
    else:
        file_path = repos_path / f"{name}.py"

    if file_path.exists():
        console.print(f"[red]❌ Repository already exists: {file_path}")
        raise typer.Exit(code=1)

    # Convert name to PascalCase for class names
    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    repo_template = f'''"""
{class_name} repository
Generated by RunApi CLI
"""
from typing import Optional, List, Dict, Any
from runapi import BaseRepository, InMemoryRepository, TypedInMemoryRepository

# Option 1: Use InMemoryRepository for prototyping
# This is great for development and testing

class {class_name}Repository(InMemoryRepository):
    """
    {class_name} repository for data access.

    For production, replace InMemoryRepository with SQLAlchemyRepository
    or implement your own data access logic.
    """

    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find {name} by name."""
        return await self.get_by(name=name)

    async def find_active(self) -> List[Dict[str, Any]]:
        """Find all active {name}s."""
        return await self.get_many_by(is_active=True)


# Option 2: For typed repositories with Pydantic models
# Uncomment and modify as needed:
#
# from schemas.{name} import {class_name}Response
#
# class Typed{class_name}Repository(TypedInMemoryRepository[{class_name}Response]):
#     def __init__(self):
#         super().__init__({class_name}Response)
#
#     async def find_by_email(self, email: str) -> Optional[{class_name}Response]:
#         return await self.get_by(email=email)


# Option 3: For SQLAlchemy (if you have a database)
# Uncomment and modify as needed:
#
# from runapi import SQLAlchemyRepository, SQLALCHEMY_AVAILABLE
# from sqlalchemy.ext.asyncio import AsyncSession
#
# if SQLALCHEMY_AVAILABLE:
#     from models.{name} import {class_name}Model
#
#     class SQLAlchemy{class_name}Repository(SQLAlchemyRepository[{class_name}Model, int]):
#         def __init__(self, session: AsyncSession):
#             super().__init__(session, {class_name}Model)
#
#         async def find_by_email(self, email: str) -> Optional[{class_name}Model]:
#             return await self.get_by(email=email)


# Example usage in routes:
#
# from repositories.{name} import {class_name}Repository
#
# # Create repository instance (consider using dependency injection)
# {name}_repo = {class_name}Repository()
#
# async def get():
#     items = await {name}_repo.get_all()
#     return items
#
# async def post(request: Request):
#     body = await request.json()
#     item = await {name}_repo.create(body)
#     return item
'''

    file_path.write_text(repo_template, encoding="utf-8")
    console.print(f"✅ [green]Repository created: {file_path}")
    console.print(f"📦 Class: {class_name}Repository")


def _generate_service(name: str, path: str):
    """Generate a new service file."""
    services_path = Path("services")
    if not services_path.exists():
        services_path.mkdir()
        (services_path / "__init__.py").touch()

    if path:
        service_path = services_path / path
        service_path.mkdir(parents=True, exist_ok=True)
        (service_path / "__init__.py").touch()
        file_path = service_path / f"{name}.py"
    else:
        file_path = services_path / f"{name}.py"

    if file_path.exists():
        console.print(f"[red]❌ Service already exists: {file_path}")
        raise typer.Exit(code=1)

    # Convert name to PascalCase for class names
    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    service_template = f'''"""
{class_name} service
Generated by RunApi CLI
"""
from typing import Optional, List, Dict, Any
from runapi import NotFoundError, ValidationError


class {class_name}Service:
    """
    {class_name} service containing business logic.

    Services orchestrate between repositories and handle:
    - Business rules and validation
    - Complex operations spanning multiple repositories
    - Transaction management
    """

    def __init__(self, repository=None):
        """
        Initialize service with repository.

        Args:
            repository: The {name} repository (inject via dependency)
        """
        self.repository = repository

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get all {name}s with pagination."""
        return await self.repository.get_all(skip=skip, limit=limit, **filters)

    async def get_by_id(self, id: int) -> Dict[str, Any]:
        """Get a {name} by ID."""
        item = await self.repository.get(id)
        if not item:
            raise NotFoundError(f"{class_name} with id {{id}} not found")
        return item

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new {name}.

        Add business validation logic here.
        """
        # Example validation
        # if not data.get("name"):
        #     raise ValidationError("Name is required")

        return await self.repository.create(data)

    async def update(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing {name}."""
        # Verify exists
        existing = await self.repository.get(id)
        if not existing:
            raise NotFoundError(f"{class_name} with id {{id}} not found")

        # Add business validation here
        # ...

        result = await self.repository.update(id, data)
        return result

    async def delete(self, id: int) -> bool:
        """Delete a {name}."""
        existing = await self.repository.get(id)
        if not existing:
            raise NotFoundError(f"{class_name} with id {{id}} not found")

        # Add business rules for deletion here
        # Example: Check if item can be deleted
        # if existing.get("is_protected"):
        #     raise ValidationError("Cannot delete protected item")

        return await self.repository.delete(id)

    async def count(self, **filters) -> int:
        """Count {name}s matching filters."""
        return await self.repository.count(**filters)


# Example usage in routes:
#
# from services.{name} import {class_name}Service
# from repositories.{name} import {class_name}Repository
#
# # Setup (consider using dependency injection)
# {name}_repo = {class_name}Repository()
# {name}_service = {class_name}Service({name}_repo)
#
# async def get():
#     return await {name}_service.get_all()
#
# async def post(request: Request):
#     body = await request.json()
#     return await {name}_service.create(body)
'''

    file_path.write_text(service_template, encoding="utf-8")
    console.print(f"✅ [green]Service created: {file_path}")
    console.print(f"📦 Class: {class_name}Service")


def _generate_main():
    """Generate main.py file."""
    main_path = Path("main.py")
    if main_path.exists():
        if not typer.confirm("main.py already exists. Overwrite?"):
            raise typer.Exit()

    main_content = '''"""
RunApi Application Entry Point
"""
from runapi import create_runapi_app, get_config

# Load configuration
config = get_config()

# Create RunApi application
runapi_app = create_runapi_app(
    title="My RunApi API",
    description="Built with RunApi framework",
    version="1.0.0"
)

# Add custom middleware if needed
# runapi_app.add_auth_middleware(protected_paths=["/api/protected"])

# Get FastAPI app for uvicorn
app = runapi_app.get_app()

if __name__ == "__main__":
    runapi_app.run()
'''

    main_path.write_text(main_content, encoding="utf-8")
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
Generated by RunApi CLI
"""
from runapi import RunApiMiddleware, Request, Response
from typing import Callable

class {name.title()}Middleware(RunApiMiddleware):
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
# runapi_app.add_middleware({name.title()}Middleware)
'''

    file_path.write_text(middleware_template, encoding="utf-8")
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

            url_path = re.sub(r"\[([^\]]+)\]", r"{\1}", url_path)

        # Read file to detect HTTP methods
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

                # Deduplicate and sort
                methods = sorted(set(methods))
                methods_str = ", ".join(methods) if methods else "No methods found"
                table.add_row(methods_str, url_path, str(relative_path))
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
def info():
    """Show project information and configuration."""
    console.print("ℹ️  [bold blue]RunApi Project Information[/bold blue]\n")

    # Load config
    config = load_config()

    # Project info
    info_table = Table(show_header=False, box=None)
    info_table.add_row("📁 Project Directory:", str(Path.cwd()))
    info_table.add_row("🐍 RunApi Version:", "0.1.0")

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


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
