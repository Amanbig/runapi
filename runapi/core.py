# runapi/core.py
import importlib.util
import inspect
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, List, Optional, Type

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from .backends import RedisRateLimitBackend, uses_redis
from .config import RunApiConfig, get_config
from .errors import ConfigurationError, RouteLoadError, setup_error_handlers
from .logging import RequestIDMiddleware, configure_logging
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
        self.middleware_stack: List[Type[RunApiMiddleware]] = []
        self.route_errors: List[str] = []
        self._startup_hooks: List[Callable[[], Any]] = []
        self._shutdown_hooks: List[Callable[[], Any]] = []
        self._readiness_checks: dict = {}
        self._user_lifespan = fastapi_kwargs.pop("lifespan", None)
        self.app = self._create_fastapi_app(**fastapi_kwargs)

        # Setup logging
        self._setup_logging()

        # Refuse to start with an unsafe production configuration
        self._validate_config()

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

        # Health and readiness endpoints
        self._setup_health_endpoints()

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

        app_kwargs["lifespan"] = self._lifespan
        return FastAPI(**app_kwargs)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """Run startup/shutdown hooks (and a user-supplied lifespan, if any)."""
        for hook in self._startup_hooks:
            await self._call_hook(hook)
        try:
            if self._user_lifespan is not None:
                async with self._user_lifespan(app):
                    yield
            else:
                yield
        finally:
            for hook in reversed(self._shutdown_hooks):
                try:
                    await self._call_hook(hook)
                except Exception:
                    self.logger.exception("Error in shutdown hook")

    @staticmethod
    async def _call_hook(hook: Callable[[], Any]):
        result = hook()
        if inspect.isawaitable(result):
            await result

    def on_startup(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a startup hook (sync or async). Usable as a decorator."""
        self._startup_hooks.append(func)
        return func

    def on_shutdown(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a shutdown hook (sync or async). Runs in reverse order."""
        self._shutdown_hooks.append(func)
        return func

    def add_readiness_check(self, name: str, check: Callable[[], Any]) -> None:
        """Register a readiness check. It must return truthy (or not raise) when healthy."""
        self._readiness_checks[name] = check

    def _validate_config(self):
        result = self.config.validate()
        for warning in result["warnings"]:
            self.logger.warning(f"Config warning: {warning}")
        if not result["errors"]:
            return
        if self.config.is_production():
            raise ConfigurationError(
                "Unsafe production configuration: " + "; ".join(result["errors"])
            )
        for error in result["errors"]:
            self.logger.warning(f"Config problem (fatal in production): {error}")

    def _setup_health_endpoints(self):
        if not self.config.health_enabled:
            return
        existing = {getattr(r, "path", None) for r in self.app.routes}

        if "/health" not in existing:

            @self.app.get("/health", include_in_schema=False)
            async def health():
                return {"status": "ok"}

        if "/ready" not in existing:

            @self.app.get("/ready", include_in_schema=False)
            async def ready():
                from fastapi.responses import JSONResponse

                results = {}
                for name, check in self._readiness_checks.items():
                    try:
                        outcome = check()
                        if inspect.isawaitable(outcome):
                            outcome = await outcome
                        results[name] = outcome is not False
                    except Exception:
                        self.logger.exception(f"Readiness check '{name}' failed")
                        results[name] = False
                healthy = all(results.values())
                return JSONResponse(
                    {"status": "ready" if healthy else "unavailable", "checks": results},
                    status_code=200 if healthy else 503,
                )

    def _setup_logging(self):
        """Setup logging configuration (JSON in production by default)."""
        configure_logging(
            self.config.log_level,
            json_logs=bool(self.config.log_json),
            text_format=self.config.log_format,
        )
        self.logger = logging.getLogger("runapi")

    def _setup_default_middleware(self):
        """Setup default middleware based on configuration."""
        # CORS middleware
        if self.config.cors_origins:
            from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

            credentials = self.config.cors_credentials
            if credentials and "*" in self.config.cors_origins:
                self.logger.warning(
                    "CORS_CREDENTIALS ignored: it cannot be used with CORS_ORIGINS='*'"
                )
                credentials = False

            self.app.add_middleware(
                FastAPICORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=credentials,
                allow_methods=self.config.cors_methods,
                allow_headers=self.config.cors_headers,
            )

        # Rate limiting middleware
        if self.config.rate_limit_enabled:
            redis_url = uses_redis(self.config)
            backend = RedisRateLimitBackend.from_url(redis_url) if redis_url else None
            self.app.add_middleware(
                RateLimitMiddleware,
                calls=self.config.rate_limit_calls,
                period=self.config.rate_limit_period,
                backend=backend,
                trust_proxy_headers=self.config.trust_proxy_headers,
            )

        # Security headers middleware
        self.app.add_middleware(SecurityHeadersMiddleware)

        # Request logging middleware
        if self.config.debug:
            self.app.add_middleware(RequestLoggingMiddleware, logger=self.logger)

        # Compression middleware
        self.app.add_middleware(CompressionMiddleware)

        # Request ID middleware (added last so it is outermost and covers everything)
        self.app.add_middleware(RequestIDMiddleware)

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

    @staticmethod
    def _segment_to_path(segment: str) -> str:
        """Convert a folder/file name segment to a URL path segment.

        - ``(group)``   -> "" (route groups organise files without affecting the URL)
        - ``[...slug]`` -> ``{slug:path}`` (catch-all)
        - ``[id]``      -> ``{id}`` (dynamic)
        """
        if segment.startswith("(") and segment.endswith(")"):
            return ""
        if segment.startswith("[...") and segment.endswith("]"):
            return f"{{{segment[4:-1]}:path}}"
        if segment.startswith("[") and segment.endswith("]"):
            return f"{{{segment[1:-1]}}}"
        return segment

    @staticmethod
    def _specificity(url_path: str) -> list:
        """Sort key so static routes register before dynamic, and catch-all last."""
        ranks = []
        for seg in url_path.strip("/").split("/"):
            if ":path}" in seg:
                ranks.append(2)
            elif seg.startswith("{"):
                ranks.append(1)
            else:
                ranks.append(0)
        return ranks

    def _load_routes_recursive(self, routes_dir: Path, prefix: str = ""):
        """Discover route files, then register them most-specific first."""
        found: List[tuple] = []
        self._collect_route_files(routes_dir, routes_dir, prefix, found)
        found.sort(key=lambda item: (self._specificity(item[2]), item[2]))
        for route_file, url_prefix, _full in found:
            self._load_route_file(route_file, url_prefix, routes_dir)

    def _collect_route_files(self, root: Path, directory: Path, prefix: str, found: list):
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                # Skip hidden directories and __pycache__
                if item.name.startswith(".") or item.name.startswith("__"):
                    continue
                part = self._segment_to_path(item.name)
                new_prefix = f"{prefix}/{part}" if part else prefix
                self._collect_route_files(root, item, new_prefix, found)
            elif item.suffix == ".py" and item.name != "__init__.py":
                file_path = self._get_route_path(item.stem)
                full = f"{prefix}{file_path}" if file_path != "/" else (prefix or "/")
                found.append((item, prefix, full))

    def _load_route_file(self, route_file: Path, prefix: str = "", routes_root: Path = None):
        """Load a single route file."""
        try:
            route_name = route_file.stem
            root = routes_root or Path("routes")
            try:
                rel_parts = route_file.relative_to(root).with_suffix("").parts
            except ValueError:
                rel_parts = (route_name,)
            safe = [re.sub(r"\W", "_", part) for part in rel_parts]
            module_name = "routes." + ".".join(safe)

            spec = importlib.util.spec_from_file_location(module_name, route_file)
            if spec is None or spec.loader is None:
                self.logger.warning(f"Could not load spec for route {route_file}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract router or create one
            route_router = getattr(module, "router", APIRouter())
            path = self._get_route_path(route_name)

            # Map HTTP methods to functions
            for method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                if hasattr(module, method):
                    getattr(route_router, method)(path)(getattr(module, method))

            # WebSocket endpoint: define `async def websocket(ws: WebSocket)`
            if callable(getattr(module, "websocket", None)):
                route_router.add_api_websocket_route(path, module.websocket)

            # Include the router with proper prefix
            final_prefix = prefix if prefix else ""
            self.app.include_router(route_router, prefix=final_prefix)

            self.logger.debug(f"Loaded route: {route_file} with prefix: {final_prefix}")

        except Exception as e:
            message = f"Failed to load route {route_file}: {e}"
            self.route_errors.append(message)
            if self.config.strict_routes:
                raise RouteLoadError(message) from e
            self.logger.exception(message)

    def _get_route_path(self, route_name: str) -> str:
        """Convert route name to FastAPI path."""
        if route_name == "index":
            return "/"
        segment = self._segment_to_path(route_name)
        return f"/{segment}" if segment else "/"

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
