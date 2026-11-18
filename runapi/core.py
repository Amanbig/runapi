# runapi/core.py
import logging
from pathlib import Path
from typing import Any, Callable, List, Optional, Type

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .backends import RedisRateLimitBackend, uses_redis
from .config import RunApiConfig, get_config
from .errors import ConfigurationError, RouteLoadError, setup_error_handlers
from .lifecycle import Lifecycle
from .logging import RequestIDMiddleware, configure_logging
from .middleware import (
    AuthMiddleware,
    CompressionMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RunApiMiddleware,
    SecurityHeadersMiddleware,
)
from .routing import RouteFile, build_router, discover_routes, load_module
from .schemas import SchemaRegistry, load_schemas


class RunApiApp:
    """Enhanced RunApi application class with configuration and middleware support."""

    def __init__(self, config: Optional[RunApiConfig] = None, **fastapi_kwargs):
        self.config = config or get_config()
        self.middleware_stack: List[Type[RunApiMiddleware]] = []
        self.route_errors: List[str] = []
        self.lifecycle = Lifecycle(user_lifespan=fastapi_kwargs.pop("lifespan", None))
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
        if self.config.health_enabled:
            self.lifecycle.register_health_endpoints(self.app)

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

        app_kwargs["lifespan"] = self.lifecycle.lifespan
        return FastAPI(**app_kwargs)

    def on_startup(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a startup hook (sync or async). Usable as a decorator."""
        self.lifecycle.startup_hooks.append(func)
        return func

    def on_shutdown(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a shutdown hook (sync or async). Runs in reverse order."""
        self.lifecycle.shutdown_hooks.append(func)
        return func

    def add_readiness_check(self, name: str, check: Callable[[], Any]) -> None:
        """Register a readiness check. It must return truthy (or not raise) when healthy."""
        self.lifecycle.readiness_checks[name] = check

    def _validate_config(self):
        result = self.config.validate_settings()
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
        """Discover route files in the project's routes/ folder and register them."""
        routes_path = Path("routes")
        if not routes_path.exists():
            return
        for route in discover_routes(routes_path):
            self._register_route(route)

    def _register_route(self, route: RouteFile):
        try:
            router = build_router(load_module(route), route.path)
            self.app.include_router(router, prefix=route.prefix)
            self.logger.debug(f"Loaded route: {route.file} with prefix: {route.prefix}")
        except Exception as e:
            message = f"Failed to load route {route.file}: {e}"
            self.route_errors.append(message)
            if self.config.strict_routes:
                raise RouteLoadError(message) from e
            self.logger.exception(message)

    def add_middleware(self, middleware_class: Type[RunApiMiddleware], **kwargs):
        """Add custom middleware to the application."""
        self.app.add_middleware(middleware_class, **kwargs)  # type: ignore[arg-type]
        self.middleware_stack.append(middleware_class)
        self.logger.debug(f"Added middleware: {middleware_class.__name__}")

    def add_auth_middleware(
        self,
        protected_paths: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
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

    def run(self, host: Optional[str] = None, port: Optional[int] = None, **uvicorn_kwargs):
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
