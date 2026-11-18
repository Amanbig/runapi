"""Application lifecycle: startup/shutdown hooks and the health/readiness endpoints."""

import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

Hook = Callable[[], Any]


async def _call(hook: Hook) -> None:
    """Run a sync or async hook."""
    result = hook()
    if inspect.isawaitable(result):
        await result


class Lifecycle:
    """Holds startup/shutdown hooks and readiness checks for one application."""

    def __init__(self, logger: Optional[logging.Logger] = None, user_lifespan: Any = None):
        self.logger = logger or logging.getLogger("runapi")
        self.startup_hooks: List[Hook] = []
        self.shutdown_hooks: List[Hook] = []
        self.readiness_checks: Dict[str, Hook] = {}
        self.user_lifespan = user_lifespan

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """FastAPI lifespan: run startup hooks, the user's lifespan (if any), then shutdown."""
        for hook in self.startup_hooks:
            await _call(hook)
        try:
            if self.user_lifespan is not None:
                async with self.user_lifespan(app):
                    yield
            else:
                yield
        finally:
            for hook in reversed(self.shutdown_hooks):
                try:
                    await _call(hook)
                except Exception:
                    self.logger.exception("Error in shutdown hook")

    def register_health_endpoints(self, app: FastAPI) -> None:
        """Add ``/health`` and ``/ready`` unless the project already defines those paths."""
        existing = {getattr(route, "path", None) for route in app.routes}

        if "/health" not in existing:

            @app.get("/health", include_in_schema=False)
            async def health():
                return {"status": "ok"}

        if "/ready" not in existing:

            @app.get("/ready", include_in_schema=False)
            async def ready():
                results = {}
                for name, check in self.readiness_checks.items():
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
