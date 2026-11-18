"""File-based route discovery: turns the ``routes/`` folder into URL patterns.

This module is pure (no FastAPI app needed) so the rules can be tested and reused, for
example by ``runapi routes``. ``RunApiApp`` uses it to register what it finds.

Conventions:
    routes/index.py              -> /
    routes/users/index.py        -> /users
    routes/users/[id].py         -> /users/{id}
    routes/docs/[...slug].py     -> /docs/{slug:path}   (catch-all)
    routes/(admin)/stats.py      -> /stats              (route groups are not in the URL)
"""

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import List

from fastapi import APIRouter

HTTP_METHODS = ("get", "post", "put", "delete", "patch", "head", "options", "trace")


@dataclass(frozen=True)
class RouteFile:
    """A discovered route file and where it is mounted."""

    file: Path
    prefix: str  # URL prefix contributed by the folders
    path: str  # path inside the router ("" for a folder's index)
    full_path: str  # the complete URL pattern
    module_name: str


def segment_to_path(segment: str) -> str:
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


def route_path(route_name: str) -> str:
    """Convert a route file's stem to a router-relative path (``index`` -> ``/``)."""
    if route_name == "index":
        return "/"
    segment = segment_to_path(route_name)
    return f"/{segment}" if segment else "/"


def specificity(url_path: str) -> List[int]:
    """Sort key so static routes register before dynamic ones, and catch-alls last."""
    ranks = []
    for seg in url_path.strip("/").split("/"):
        if ":path}" in seg:
            ranks.append(2)
        elif seg.startswith("{"):
            ranks.append(1)
        else:
            ranks.append(0)
    return ranks


def discover_routes(routes_dir: Path) -> List[RouteFile]:
    """Find every route file under ``routes_dir``, most specific first."""
    found: List[RouteFile] = []
    _walk(routes_dir, routes_dir, "", found)
    found.sort(key=lambda r: (specificity(r.full_path), r.full_path))
    return found


def _walk(root: Path, directory: Path, prefix: str, found: List[RouteFile]) -> None:
    for item in sorted(directory.iterdir()):
        if item.is_dir():
            # Skip hidden directories and __pycache__
            if item.name.startswith(".") or item.name.startswith("__"):
                continue
            part = segment_to_path(item.name)
            _walk(root, item, f"{prefix}/{part}" if part else prefix, found)
        elif item.suffix == ".py" and item.name != "__init__.py":
            path = route_path(item.stem)
            full = f"{prefix}{path}" if path != "/" else (prefix or "/")
            if path == "/" and prefix:
                # routes/users/index.py -> "/users" (not "/users/", which would redirect)
                path = ""
            found.append(RouteFile(item, prefix, path, full, _module_name(root, item)))


def _module_name(root: Path, file: Path) -> str:
    parts = file.relative_to(root).with_suffix("").parts
    return "routes." + ".".join(re.sub(r"\W", "_", part) for part in parts)


def load_module(route: RouteFile) -> ModuleType:
    """Import a route file. Raises if it cannot be imported."""
    spec = importlib.util.spec_from_file_location(route.module_name, route.file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for route {route.file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_router(module: ModuleType, path: str) -> APIRouter:
    """Attach the module's ``get``/``post``/... functions and ``websocket`` to a router."""
    router = getattr(module, "router", None) or APIRouter()
    for method in HTTP_METHODS:
        if hasattr(module, method):
            getattr(router, method)(path)(getattr(module, method))
    if callable(getattr(module, "websocket", None)):
        router.add_api_websocket_route(path, module.websocket)
    return router


def has_handlers(router: APIRouter) -> bool:
    """True if the router ended up with at least one route."""
    return bool(router.routes)


def misnamed_handlers(module: ModuleType) -> List[str]:
    """Names that look like HTTP handlers but are not exactly ``get``/``post``/...

    For example ``GET``, ``Get`` or ``get_users``: a common beginner mistake that
    otherwise silently produces an empty route file.
    """
    suspects = []
    for name, value in vars(module).items():
        if name.startswith("_") or not callable(value) or name in HTTP_METHODS:
            continue
        if getattr(value, "__module__", None) != module.__name__:
            continue  # imported, not defined here
        lowered = name.lower()
        if lowered in HTTP_METHODS or any(lowered.startswith(m + "_") for m in HTTP_METHODS):
            suspects.append(name)
    return suspects
