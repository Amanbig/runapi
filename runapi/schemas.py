# runapi/schemas.py
"""
Schema layer for RunAPI - Pydantic model management and auto-discovery.

Provides:
- BaseSchema with common configurations
- Schema registry for auto-discovery
- Common mixins (timestamps, pagination, etc.)
- Utility functions for schema operations
"""

import importlib.util
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("runapi.schemas")

# Type variable for generic schemas
T = TypeVar("T")


# =============================================================================
# Schema Registry
# =============================================================================


class SchemaRegistry:
    """
    Registry for auto-discovered schemas.

    Schemas placed in the `schemas/` directory are automatically discovered
    and registered here for easy access across the application.
    """

    _schemas: Dict[str, Type[BaseModel]] = {}
    _modules: Dict[str, Any] = {}
    _loaded: bool = False

    @classmethod
    def register(cls, name: str, schema: Type[BaseModel]) -> None:
        """Register a schema by name."""
        cls._schemas[name] = schema
        logger.debug(f"Registered schema: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return cls._schemas.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseModel]]:
        """Get all registered schemas."""
        return cls._schemas.copy()

    @classmethod
    def get_module(cls, name: str) -> Optional[Any]:
        """Get a loaded schema module by name."""
        return cls._modules.get(name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered schemas (useful for testing)."""
        cls._schemas.clear()
        cls._modules.clear()
        cls._loaded = False


# =============================================================================
# Base Schema Classes
# =============================================================================


class BaseSchema(BaseModel):
    """
    Base schema class with sensible defaults for API development.

    Features:
    - Automatic ORM mode for SQLAlchemy compatibility
    - Strict validation by default
    - JSON-compatible serialization

    Example:
        class UserResponse(BaseSchema):
            id: int
            email: str
            created_at: datetime
    """

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (formerly orm_mode)
        validate_assignment=True,  # Validate on attribute assignment
        str_strip_whitespace=True,  # Strip whitespace from strings
        ser_json_timedelta="iso8601",  # Pydantic v2 handles datetime ISO serialization by default
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class IDMixin(BaseModel):
    """Mixin for models with an ID field."""

    id: int = Field(..., description="Unique identifier")


# =============================================================================
# Common Response Schemas
# =============================================================================


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Generic paginated response wrapper.

    Example:
        class UserList(PaginatedResponse[UserResponse]):
            pass
    """

    items: List[T] = Field(default_factory=list, description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(
        cls, items: List[T], total: int, page: int = 1, page_size: int = 20
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class PaginationParams(BaseSchema):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size."""
        return self.page_size


class ErrorDetail(BaseSchema):
    """Error detail schema."""

    field: Optional[str] = Field(default=None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseSchema):
    """Standardized error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(default=None, description="Detailed errors")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


# =============================================================================
# Schema Discovery
# =============================================================================


def load_schemas(schemas_path: Path = None, logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Load schemas from the schemas/ directory.

    Similar to route loading, this discovers all Python files in the schemas/
    directory and imports them, making their Pydantic models available.

    Args:
        schemas_path: Path to schemas directory (defaults to ./schemas)
        logger: Logger instance for debug output

    Returns:
        Dictionary of loaded modules by name
    """
    if logger is None:
        logger = logging.getLogger("runapi.schemas")

    if schemas_path is None:
        schemas_path = Path("schemas")

    if not schemas_path.exists():
        logger.debug(f"Schemas directory not found: {schemas_path}")
        return {}

    loaded_modules = {}
    _load_schemas_recursive(schemas_path, "", loaded_modules, logger)

    SchemaRegistry._modules = loaded_modules
    SchemaRegistry._loaded = True

    return loaded_modules


def _load_schemas_recursive(
    schemas_dir: Path, prefix: str, loaded_modules: Dict[str, Any], logger: logging.Logger
) -> None:
    """Recursively load schema files from directory structure."""

    for item in schemas_dir.iterdir():
        if item.is_dir():
            # Skip hidden directories and __pycache__
            if item.name.startswith(".") or item.name.startswith("__"):
                continue

            # Recurse into subdirectories
            new_prefix = f"{prefix}.{item.name}" if prefix else item.name
            _load_schemas_recursive(item, new_prefix, loaded_modules, logger)

        elif item.suffix == ".py" and item.name != "__init__.py":
            _load_schema_file(item, prefix, loaded_modules, logger)


def _load_schema_file(
    schema_file: Path, prefix: str, loaded_modules: Dict[str, Any], logger: logging.Logger
) -> None:
    """Load a single schema file and register its Pydantic models."""

    try:
        schema_name = schema_file.stem
        module_name = f"schemas.{prefix}.{schema_name}".strip(".").replace("..", ".")

        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, schema_file)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not load spec for schema {schema_file}")
            return

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules so relative imports work
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Store the module
        loaded_modules[module_name] = module

        # Find and register all Pydantic models in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
                and not attr_name.startswith("_")
            ):
                # Register with full path and short name
                full_name = f"{module_name}.{attr_name}"
                SchemaRegistry.register(full_name, attr)

                # Check for short name collision before registering
                existing = SchemaRegistry.get(attr_name)
                if existing is not None and existing is not attr:
                    logger.warning(
                        f"Schema name collision: '{attr_name}' from {module_name} "
                        f"shadows existing schema. Use full path '{full_name}' to disambiguate."
                    )
                SchemaRegistry.register(attr_name, attr)  # Also register short name

        logger.debug(f"Loaded schema module: {module_name}")

    except Exception as e:
        logger.error(f"Failed to load schema {schema_file}: {e}")


def get_schema(name: str) -> Optional[Type[BaseModel]]:
    """
    Get a registered schema by name.

    Args:
        name: Schema name (e.g., "UserResponse" or "schemas.user.UserResponse")

    Returns:
        The schema class or None if not found
    """
    return SchemaRegistry.get(name)


def list_schemas() -> List[str]:
    """List all registered schema names."""
    return list(SchemaRegistry.get_all().keys())


# =============================================================================
# Schema Utilities
# =============================================================================


def create_response_model(
    name: str, *, include_id: bool = True, include_timestamps: bool = True, **fields: Any
) -> Type[BaseSchema]:
    """
    Dynamically create a response schema.

    Example:
        UserResponse = create_response_model(
            "UserResponse",
            include_id=True,
            include_timestamps=True,
            email=(str, ...),
            name=(str, None)
        )
    """
    bases = [BaseSchema]

    if include_id:
        bases.insert(0, IDMixin)
    if include_timestamps:
        bases.insert(0, TimestampMixin)

    return type(name, tuple(bases), {"__annotations__": fields})


def create_create_model(name: str, **fields: Any) -> Type[BaseSchema]:
    """
    Dynamically create a 'create' schema (no ID, no timestamps).

    Example:
        UserCreate = create_create_model(
            "UserCreate",
            email=(str, ...),
            password=(str, ...)
        )
    """
    return type(name, (BaseSchema,), {"__annotations__": fields})


def create_update_model(name: str, **fields: Any) -> Type[BaseSchema]:
    """
    Dynamically create an 'update' schema (all fields optional).

    Example:
        UserUpdate = create_update_model(
            "UserUpdate",
            email=str,
            name=str
        )
    """
    # Make all fields optional with None defaults
    annotations = {}
    field_defaults = {}

    for field_name, field_type in fields.items():
        if isinstance(field_type, tuple):
            # If tuple provided, use first element as type
            annotations[field_name] = Optional[field_type[0]]
        else:
            annotations[field_name] = Optional[field_type]
        field_defaults[field_name] = None

    namespace = {"__annotations__": annotations}
    namespace.update(field_defaults)

    return type(name, (BaseSchema,), namespace)
