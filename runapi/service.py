# runapi/service.py
"""
Service layer for RunAPI - Business logic abstraction.

Provides:
- BaseService abstract class for business logic
- CRUDService for common CRUD operations
- Service decorators for validation, transactions, etc.
- Dependency injection utilities
"""

import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Type, TypeVar

from .errors import NotFoundError
from .repository import BaseRepository

logger = logging.getLogger("runapi.service")

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


# =============================================================================
# Base Service (Abstract)
# =============================================================================


class BaseService(ABC, Generic[T, ID]):
    """
    Abstract base service for business logic.

    Services sit between routes and repositories, handling:
    - Business rules and validation
    - Complex operations spanning multiple repositories
    - Transaction coordination
    - Authorization checks

    Example:
        class UserService(BaseService[User, int]):
            def __init__(self, user_repo: UserRepository):
                self.repository = user_repo

            async def register(self, data: dict) -> User:
                # Business logic here
                if await self.repository.get_by(email=data['email']):
                    raise ValidationError("Email already exists")
                return await self.repository.create(data)
    """

    repository: BaseRepository[T, ID]

    @abstractmethod
    async def get(self, id: ID) -> T:
        """Get an entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def update(self, id: ID, data: Dict[str, Any]) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity."""
        pass


# =============================================================================
# CRUD Service (Ready-to-use)
# =============================================================================


class CRUDService(BaseService[T, ID], Generic[T, ID]):
    """
    Ready-to-use CRUD service with common operations.

    Provides standard CRUD operations with built-in:
    - Not found error handling
    - Pagination support
    - Filter support

    Example:
        class UserService(CRUDService[User, int]):
            def __init__(self, repository: UserRepository):
                super().__init__(repository)

            # Add custom business methods
            async def deactivate(self, user_id: int) -> User:
                return await self.update(user_id, {"is_active": False})
    """

    def __init__(self, repository: BaseRepository[T, ID], entity_name: str = "Entity"):
        """
        Initialize CRUD service.

        Args:
            repository: The repository for data access
            entity_name: Name used in error messages (e.g., "User", "Product")
        """
        self.repository = repository
        self.entity_name = entity_name

    async def get(self, id: ID) -> T:
        """
        Get an entity by ID.

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.repository.get(id)
        if entity is None:
            raise NotFoundError(f"{self.entity_name} with id {id} not found")
        return entity

    async def get_or_none(self, id: ID) -> Optional[T]:
        """Get an entity by ID, returning None if not found."""
        return await self.repository.get(id)

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with pagination and optional filters."""
        return await self.repository.get_all(skip=skip, limit=limit, **filters)

    async def get_by(self, **filters) -> Optional[T]:
        """Get a single entity matching filters."""
        return await self.repository.get_by(**filters)

    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Override this method to add validation logic.
        """
        return await self.repository.create(data)

    async def update(self, id: ID, data: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Raises:
            NotFoundError: If entity not found
        """
        # Verify exists
        await self.get(id)  # Raises NotFoundError if not found

        result = await self.repository.update(id, data)
        if result is None:
            raise NotFoundError(f"{self.entity_name} with id {id} not found")
        return result

    async def delete(self, id: ID) -> bool:
        """
        Delete an entity.

        Raises:
            NotFoundError: If entity not found
        """
        # Verify exists
        await self.get(id)  # Raises NotFoundError if not found

        return await self.repository.delete(id)

    async def exists(self, id: ID) -> bool:
        """Check if an entity exists."""
        return await self.repository.exists(id)

    async def count(self, **filters) -> int:
        """Count entities matching filters."""
        return await self.repository.count(**filters)

    # Bulk operations

    async def create_many(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities."""
        return await self.repository.create_many(items)

    async def update_many(self, ids: List[ID], data: Dict[str, Any]) -> List[T]:
        """Update multiple entities."""
        return await self.repository.update_many(ids, data)

    async def delete_many(self, ids: List[ID]) -> int:
        """Delete multiple entities. Returns count of deleted."""
        return await self.repository.delete_many(ids)


# =============================================================================
# Service with Validation
# =============================================================================


class ValidatedService(CRUDService[T, ID], Generic[T, ID]):
    """
    CRUD service with schema validation support.

    Validates input data against Pydantic schemas before operations.

    Example:
        class UserService(ValidatedService[User, int]):
            create_schema = UserCreate
            update_schema = UserUpdate

            def __init__(self, repository: UserRepository):
                super().__init__(repository, "User")
    """

    create_schema: Optional[Type] = None
    update_schema: Optional[Type] = None

    def _validate_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for create operation."""
        if self.create_schema:
            validated = self.create_schema(**data)
            if hasattr(validated, "model_dump"):
                return validated.model_dump(exclude_unset=True)
            elif hasattr(validated, "dict"):
                return validated.dict(exclude_unset=True)
        return data

    def _validate_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for update operation."""
        if self.update_schema:
            validated = self.update_schema(**data)
            if hasattr(validated, "model_dump"):
                return validated.model_dump(exclude_unset=True, exclude_none=True)
            elif hasattr(validated, "dict"):
                return validated.dict(exclude_unset=True, exclude_none=True)
        return data

    async def create(self, data: Dict[str, Any]) -> T:
        """Create with validation."""
        validated_data = self._validate_create(data)
        return await self.repository.create(validated_data)

    async def update(self, id: ID, data: Dict[str, Any]) -> T:
        """Update with validation."""
        await self.get(id)  # Verify exists
        validated_data = self._validate_update(data)
        result = await self.repository.update(id, validated_data)
        if result is None:
            raise NotFoundError(f"{self.entity_name} with id {id} not found")
        return result


# =============================================================================
# Service Decorators
# =============================================================================


def validate_input(schema: Type):
    """
    Decorator to validate input data against a Pydantic schema.

    Example:
        class UserService(CRUDService):
            @validate_input(UserCreate)
            async def create(self, data: dict) -> User:
                return await self.repository.create(data)
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, data: Dict[str, Any], *args, **kwargs):
            validated = schema(**data)
            if hasattr(validated, "model_dump"):
                validated_data = validated.model_dump(exclude_unset=True)
            elif hasattr(validated, "dict"):
                validated_data = validated.dict(exclude_unset=True)
            else:
                validated_data = data
            return await func(self, validated_data, *args, **kwargs)

        return wrapper

    return decorator


def require_exists(entity_name: str = "Entity"):
    """
    Decorator to ensure an entity exists before operation.

    Example:
        class UserService(CRUDService):
            @require_exists("User")
            async def update(self, id: int, data: dict) -> User:
                return await self.repository.update(id, data)
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, id: Any, *args, **kwargs):
            exists = await self.repository.exists(id)
            if not exists:
                raise NotFoundError(f"{entity_name} with id {id} not found")
            return await func(self, id, *args, **kwargs)

        return wrapper

    return decorator


def log_operation(operation_name: str = None):
    """
    Decorator to log service operations.

    Example:
        class UserService(CRUDService):
            @log_operation("create_user")
            async def create(self, data: dict) -> User:
                return await self.repository.create(data)
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            logger.info(f"Starting operation: {op_name}")
            try:
                result = await func(self, *args, **kwargs)
                logger.info(f"Completed operation: {op_name}")
                return result
            except Exception as e:
                logger.error(f"Failed operation: {op_name} - {e}")
                raise

        return wrapper

    return decorator


# =============================================================================
# Service Factory
# =============================================================================


class ServiceFactory:
    """
    Factory for creating and managing service instances.

    Useful for dependency injection and testing.

    Example:
        factory = ServiceFactory()
        factory.register("users", UserService, user_repository)

        # In route handler
        user_service = factory.get("users")
    """

    _services: Dict[str, Any] = {}
    _factories: Dict[str, tuple] = {}

    @classmethod
    def register(cls, name: str, service_class: Type[BaseService], *args, **kwargs) -> None:
        """
        Register a service factory.

        Args:
            name: Service name for lookup
            service_class: The service class
            *args, **kwargs: Arguments to pass to service constructor
        """
        cls._factories[name] = (service_class, args, kwargs)
        logger.debug(f"Registered service factory: {name}")

    @classmethod
    def get(cls, name: str) -> BaseService:
        """
        Get or create a service instance.

        Creates a new instance on first access, then returns cached instance.
        """
        if name not in cls._services:
            if name not in cls._factories:
                raise ValueError(f"Service '{name}' not registered")
            service_class, args, kwargs = cls._factories[name]
            cls._services[name] = service_class(*args, **kwargs)
        return cls._services[name]

    @classmethod
    def create(cls, name: str) -> BaseService:
        """Create a new service instance (not cached)."""
        if name not in cls._factories:
            raise ValueError(f"Service '{name}' not registered")
        service_class, args, kwargs = cls._factories[name]
        return service_class(*args, **kwargs)

    @classmethod
    def list_services(cls) -> List[str]:
        """List all registered service names."""
        return list(cls._factories.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services and instances."""
        cls._services.clear()
        cls._factories.clear()


# =============================================================================
# Dependency Injection Helper
# =============================================================================


def create_service_dependency(
    service_class: Type[BaseService], repository_class: Type[BaseRepository], **service_kwargs
) -> Callable:
    """
    Create a FastAPI dependency for a service.

    Example:
        from fastapi import Depends

        get_user_service = create_service_dependency(UserService, UserRepository)

        async def get_users(service: UserService = Depends(get_user_service)):
            return await service.get_all()
    """
    # Cache the repository instance
    _repository = None
    _service = None

    def get_service() -> BaseService:
        nonlocal _repository, _service
        if _repository is None:
            _repository = repository_class()
        if _service is None:
            _service = service_class(_repository, **service_kwargs)
        return _service

    return get_service


# =============================================================================
# Utility Functions
# =============================================================================


def create_crud_service(
    repository: BaseRepository[T, ID], entity_name: str = "Entity"
) -> CRUDService[T, ID]:
    """
    Quick factory to create a CRUD service.

    Example:
        user_repo = UserRepository()
        user_service = create_crud_service(user_repo, "User")
    """
    return CRUDService(repository, entity_name)
