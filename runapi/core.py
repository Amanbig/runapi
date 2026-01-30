# runapi/core.py
import importlib.util
import logging
from pathlib import Path
from typing import List, Optional, Type

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from .config import RunApiConfig, get_config
from .errors import setup_error_handlers
from .middleware import (
    AuthMiddleware,
    CompressionMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RunApiMiddleware,
    SecurityHeadersMiddleware,
)
from .schemas import SchemaRegistry, load_schemas


class RunApiApp:
    """Enhanced RunApi application class with configuration and middleware support."""

    def __init__(self, config: Optional[RunApiConfig] = None, **fastapi_kwargs):
        self.config = config or get_config()
        self.app = self._create_fastapi_app(**fastapi_kwargs)
        self.middleware_stack: List[Type[RunApiMiddleware]] = []

        # Setup logging
        self._setup_logging()

        # Setup default middleware
        self._setup_default_middleware()

        # Setup error handlers
        self._setup_error_handlers()

        # Load routes
        self._load_routes()

        # Load schemas
        self._load_schemas()

        # Setup static files
        self._setup_static_files()

    def _create_fastapi_app(self, **kwargs) -> FastAPI:
        """Create FastAPI application with configuration."""
        # Merge config with kwargs
        app_kwargs = {
            "debug": self.config.debug,
            "title": kwargs.get("title", "RunApi API"),
            "description": kwargs.get("description", "API built with RunApi framework"),
            "version": kwargs.get("version", "1.0.0"),
        }
        app_kwargs.update(kwargs)

        return FastAPI(**app_kwargs)

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()), format=self.config.log_format
        )
        self.logger = logging.getLogger("runapi")

    def _setup_default_middleware(self):
        """Setup default middleware based on configuration."""
        # CORS middleware
        if self.config.cors_origins:
            from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

            self.app.add_middleware(
                FastAPICORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=self.config.cors_credentials,
                allow_methods=self.config.cors_methods,
                allow_headers=self.config.cors_headers,
            )

        # Rate limiting middleware
        if self.config.rate_limit_enabled:
            self.app.add_middleware(
                RateLimitMiddleware,
                calls=self.config.rate_limit_calls,
                period=self.config.rate_limit_period,
            )

        # Security headers middleware
        self.app.add_middleware(SecurityHeadersMiddleware)

        # Request logging middleware
        if self.config.debug:
            self.app.add_middleware(RequestLoggingMiddleware, logger=self.logger)

        # Compression middleware
        self.app.add_middleware(CompressionMiddleware)

    def _setup_error_handlers(self):
        """Setup error handlers for the application."""
        setup_error_handlers(self.app, self.logger, self.config.debug)

    def _setup_static_files(self):
        """Setup static file serving."""
        if self.config.static_files_enabled:
            static_path = Path(self.config.static_files_path)
            if static_path.exists():
                self.app.mount(
                    self.config.static_files_url,
                    StaticFiles(directory=str(static_path)),
                    name="static",
                )

    def _load_schemas(self):
        """Load schemas from project's schemas/ folder."""
        schemas_path = Path("schemas")
        if schemas_path.exists():
            loaded = load_schemas(schemas_path, self.logger)
            self.logger.debug(f"Loaded {len(loaded)} schema modules")

    def _load_routes(self):
        """Load routes from project's routes/ folder."""
        routes_path = Path("routes")
        if routes_path.exists():
            self._load_routes_recursive(routes_path)

    def _load_routes_recursive(self, routes_dir: Path, prefix: str = ""):
        """Recursively load routes from directory structure."""

        for item in routes_dir.iterdir():
            if item.is_dir():
                # Skip hidden directories and __pycache__
                if item.name.startswith(".") or item.name.startswith("__"):
                    continue

                # Recurse into subfolders (e.g., routes/api/users)
                new_prefix = f"{prefix}/{item.name}"
                self._load_routes_recursive(item, new_prefix)
            elif item.suffix == ".py" and item.name != "__init__.py":
                self._load_route_file(item, prefix)

    def _load_route_file(self, route_file: Path, prefix: str = ""):
        """Load a single route file."""
        try:
            route_name = route_file.stem
            prefix_part = prefix.replace("/", ".").strip(".")
            module_name = (
                f"routes.{prefix_part}.{route_name}" if prefix_part else f"routes.{route_name}"
            )

            spec = importlib.util.spec_from_file_location(module_name, route_file)
            if spec is None or spec.loader is None:
                self.logger.warning(f"Could not load spec for route {route_file}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract router or create one
            route_router = getattr(module, "router", APIRouter())

            # Map HTTP methods to functions
            for method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                if hasattr(module, method):
                    path = self._get_route_path(route_name)
                    getattr(route_router, method)(path)(getattr(module, method))

            # Include the router with proper prefix
            final_prefix = prefix if prefix else ""
            self.app.include_router(route_router, prefix=final_prefix)

            self.logger.debug(f"Loaded route: {route_file} with prefix: {final_prefix}")

        except Exception as e:
            self.logger.error(f"Failed to load route {route_file}: {e}")

    def _get_route_path(self, route_name: str) -> str:
        """Convert route name to FastAPI path."""
        if route_name == "index":
            return "/"
        elif route_name.startswith("[") and route_name.endswith("]"):
            # Dynamic route: [id] -> {id}
            param_name = route_name[1:-1]
            return f"/{{{param_name}}}"
        elif route_name.startswith("[...") and route_name.endswith("]"):
            # Catch-all route: [...slug] -> {slug:path}
            param_name = route_name[4:-1]
            return f"/{{{param_name}:path}}"
        else:
            return f"/{route_name}"

    def add_middleware(self, middleware_class: Type[RunApiMiddleware], **kwargs):
        """Add custom middleware to the application."""
        self.app.add_middleware(middleware_class, **kwargs)
        self.middleware_stack.append(middleware_class)
        self.logger.debug(f"Added middleware: {middleware_class.__name__}")

    def add_auth_middleware(
        self, protected_paths: List[str] = None, excluded_paths: List[str] = None
    ):
        """Add JWT authentication middleware."""
        if (
            not self.config.secret_key
            or self.config.secret_key == "dev-secret-key-change-in-production"
        ):
            self.logger.warning("Using default secret key. Change SECRET_KEY in production!")

        self.add_middleware(
            AuthMiddleware,
            secret_key=self.config.secret_key,
            protected_paths=protected_paths,
            excluded_paths=excluded_paths,
        )

    def get_app(self) -> FastAPI:
        """Get the underlying FastAPI application."""
        return self.app

    def get_schema(self, name: str):
        """Get a registered schema by name."""
        return SchemaRegistry.get(name)

    def list_schemas(self) -> List[str]:
        """List all registered schema names."""
        return list(SchemaRegistry.get_all().keys())

    def run(self, host: str = None, port: int = None, **uvicorn_kwargs):
        """Run the application with uvicorn."""
        import uvicorn

        run_kwargs = {
            "host": host or self.config.host,
            "port": port or self.config.port,
            "reload": self.config.reload,
            "log_level": self.config.log_level.lower(),
            **uvicorn_kwargs,
        }

        self.logger.info(f"Starting RunApi server on {run_kwargs['host']}:{run_kwargs['port']}")
        uvicorn.run(self.app, **run_kwargs)


def create_app(config: Optional[RunApiConfig] = None, **kwargs) -> FastAPI:
    """Create a RunApi FastAPI application."""
    runapi_app = RunApiApp(config=config, **kwargs)
    return runapi_app.get_app()


def create_runapi_app(config: Optional[RunApiConfig] = None, **kwargs) -> RunApiApp:
    """Create a RunApi application instance."""
    return RunApiApp(config=config, **kwargs)
