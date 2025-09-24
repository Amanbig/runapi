# pynextapi/core.py
from fastapi import FastAPI, APIRouter
from pathlib import Path
import importlib.util

def create_app(**kwargs) -> FastAPI:
    """Create a FastAPI app with PyNext routing."""
    app = FastAPI(**kwargs)
    
    def load_routes(routes_dir: Path, prefix: str = ""):
        router = APIRouter(prefix=prefix)
        for item in routes_dir.iterdir():
            if item.is_dir():
                # Recurse into subfolders (e.g., routes/api/users)
                new_prefix = f"{prefix}/{item.name}"
                sub_router = load_routes(item, new_prefix)
                app.include_router(sub_router)
            elif item.suffix == ".py" and item.name != "__init__.py":
                # Load route file (e.g., get.py or [id].py)
                route_name = item.stem
                module_name = f"routes.{prefix.replace('/', '.')}.{route_name}".strip(".")
                spec = importlib.util.spec_from_file_location(module_name, item)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Extract router or create one
                route_router = getattr(module, "router", APIRouter())
                
                # Map HTTP methods to functions
                for method in ["get", "post", "put", "delete"]:
                    if hasattr(module, method):
                        path = "/" if route_name == "index" else f"/{route_name}"
                        if route_name.startswith("[") and route_name.endswith("]"):
                            path = f"/{{{route_name[1:-1]}}}"  # Dynamic route: [id] -> {id}
                        getattr(route_router, method)(path)(getattr(module, method))
                
                app.include_router(route_router)
        return router

    # Load routes from project's routes/ folder
    routes_path = Path("routes")
    if routes_path.exists():
        load_routes(routes_path)
    
    return app