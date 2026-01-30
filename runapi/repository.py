# runapi/repository.py
"""
Repository pattern for RunAPI - Data access layer abstraction.

Provides:
- BaseRepository abstract class with common CRUD operations
- InMemoryRepository for testing and prototyping
- SQLAlchemy integration (optional, if installed)
- Generic typing for type-safe repositories
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

logger = logging.getLogger("runapi.repository")

# Type variables for generic repositories
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type (usually int or str)
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


# =============================================================================
# Repository Protocol (Interface)
# =============================================================================


@runtime_checkable
class RepositoryProtocol(Protocol[T, ID]):
    """Protocol defining the repository interface."""

    async def get(self, id: ID) -> Optional[T]: ...
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]: ...
    async def create(self, data: Dict[str, Any]) -> T: ...
    async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]: ...
    async def delete(self, id: ID) -> bool: ...
    async def count(self) -> int: ...


# =============================================================================
# Base Repository (Abstract)
# =============================================================================


class BaseRepository(ABC, Generic[T, ID]):
    """
    Abstract base repository with common CRUD operations.

    Inherit from this class and implement the abstract methods
    to create repositories for your data sources.

    Example:
        class UserRepository(BaseRepository[User, int]):
            async def get(self, id: int) -> Optional[User]:
                # Implementation
                pass
    """

    @abstractmethod
    async def get(self, id: ID) -> Optional[T]:
        """Get a single entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with pagination and optional filters."""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity by ID. Returns True if deleted."""
        pass

    async def count(self, **filters) -> int:
        """Count entities matching filters. Default implementation."""
        items = await self.get_all(skip=0, limit=999999, **filters)
        return len(items)

    async def exists(self, id: ID) -> bool:
        """Check if an entity exists."""
        return await self.get(id) is not None

    async def get_by(self, **filters) -> Optional[T]:
        """Get a single entity matching filters."""
        items = await self.get_all(skip=0, limit=1, **filters)
        return items[0] if items else None

    async def get_many_by(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get multiple entities matching filters."""
        return await self.get_all(skip=skip, limit=limit, **filters)

    async def create_many(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities. Default implementation."""
        return [await self.create(item) for item in items]

    async def update_many(self, ids: List[ID], data: Dict[str, Any]) -> List[T]:
        """Update multiple entities. Default implementation."""
        results = []
        for id in ids:
            result = await self.update(id, data)
            if result:
                results.append(result)
        return results

    async def delete_many(self, ids: List[ID]) -> int:
        """Delete multiple entities. Returns count of deleted."""
        count = 0
        for id in ids:
            if await self.delete(id):
                count += 1
        return count


# =============================================================================
# In-Memory Repository (for testing/prototyping)
# =============================================================================


class InMemoryRepository(BaseRepository[Dict[str, Any], int]):
    """
    In-memory repository for testing and prototyping.

    Stores entities in a dictionary. Useful for:
    - Unit testing without database
    - Rapid prototyping
    - Development before database setup

    Example:
        repo = InMemoryRepository()
        user = await repo.create({"name": "John", "email": "john@example.com"})
        users = await repo.get_all()
    """

    def __init__(self):
        self._storage: Dict[int, Dict[str, Any]] = {}
        self._id_counter = 0

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        return self._storage.get(id)

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Dict[str, Any]]:
        """Get all entities with pagination and filters."""
        items = list(self._storage.values())

        # Apply filters
        if filters:
            items = [item for item in items if all(item.get(k) == v for k, v in filters.items())]

        # Apply pagination
        return items[skip : skip + limit]

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new entity."""
        entity = data.copy()
        entity["id"] = self._next_id()
        entity["created_at"] = datetime.now(timezone.utc)
        entity["updated_at"] = datetime.now(timezone.utc)
        self._storage[entity["id"]] = entity
        return entity

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing entity."""
        if id not in self._storage:
            return None

        entity = self._storage[id]
        for key, value in data.items():
            if value is not None:  # Only update non-None values
                entity[key] = value
        entity["updated_at"] = datetime.now(timezone.utc)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete an entity."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self, **filters) -> int:
        """Count entities."""
        if not filters:
            return len(self._storage)
        return len(await self.get_all(**filters))

    def clear(self):
        """Clear all entities (useful for testing)."""
        self._storage.clear()
        self._id_counter = 0


# =============================================================================
# Typed In-Memory Repository
# =============================================================================


class TypedInMemoryRepository(BaseRepository[T, int], Generic[T]):
    """
    Type-safe in-memory repository using Pydantic models.

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            id: Optional[int] = None
            name: str
            email: str

        repo = TypedInMemoryRepository(User)
        user = await repo.create({"name": "John", "email": "john@example.com"})
        # user is a User instance
    """

    def __init__(self, model_class: Type[T]):
        self._model_class = model_class
        self._storage: Dict[int, T] = {}
        self._id_counter = 0

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def _to_model(self, data: Dict[str, Any]) -> T:
        """Convert dict to model instance."""
        return self._model_class(**data)

    def _to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model to dict."""
        if hasattr(model, "model_dump"):
            return model.model_dump()
        elif hasattr(model, "dict"):
            return model.dict()
        elif hasattr(model, "__dict__"):
            return {k: v for k, v in model.__dict__.items() if not k.startswith("_")}
        raise TypeError(f"Cannot convert {type(model).__name__} to dict")

    async def get(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        return self._storage.get(id)

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with pagination and filters."""
        items = list(self._storage.values())

        # Apply filters
        if filters:
            filtered = []
            for item in items:
                item_dict = self._to_dict(item)
                if all(item_dict.get(k) == v for k, v in filters.items()):
                    filtered.append(item)
            items = filtered

        return items[skip : skip + limit]

    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        entity_data = data.copy()
        entity_data["id"] = self._next_id()

        # Add timestamps if the model supports them
        now = datetime.now(timezone.utc)
        if "created_at" not in entity_data:
            entity_data["created_at"] = now
        if "updated_at" not in entity_data:
            entity_data["updated_at"] = now

        entity = self._to_model(entity_data)
        self._storage[entity_data["id"]] = entity
        return entity

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity."""
        if id not in self._storage:
            return None

        existing = self._storage[id]
        existing_dict = self._to_dict(existing)

        for key, value in data.items():
            if value is not None:
                existing_dict[key] = value

        existing_dict["updated_at"] = datetime.now(timezone.utc)

        entity = self._to_model(existing_dict)
        self._storage[id] = entity
        return entity

    async def delete(self, id: int) -> bool:
        """Delete an entity."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def count(self, **filters) -> int:
        """Count entities."""
        if not filters:
            return len(self._storage)
        return len(await self.get_all(**filters))

    def clear(self):
        """Clear all entities."""
        self._storage.clear()
        self._id_counter = 0


# =============================================================================
# SQLAlchemy Repository (Optional)
# =============================================================================

try:
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    SQLALCHEMY_AVAILABLE = True

    class SQLAlchemyRepository(BaseRepository[T, ID], Generic[T, ID]):
        """
        SQLAlchemy-based repository for async database operations.

        Requires SQLAlchemy with async support.

        Example:
            class UserRepository(SQLAlchemyRepository[User, int]):
                def __init__(self, session: AsyncSession):
                    super().__init__(session, User)

            async with async_session() as session:
                repo = UserRepository(session)
                user = await repo.create({"name": "John", "email": "john@example.com"})
        """

        def __init__(self, session: AsyncSession, model_class: Type[T]):
            self.session = session
            self.model_class = model_class

        async def get(self, id: ID) -> Optional[T]:
            """Get entity by ID."""
            result = await self.session.get(self.model_class, id)
            return result

        async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
            """Get all entities with pagination and filters."""
            query = select(self.model_class)

            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)

            query = query.offset(skip).limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())

        async def create(self, data: Dict[str, Any]) -> T:
            """Create a new entity."""
            entity = self.model_class(**data)
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity

        async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
            """Update an existing entity."""
            entity = await self.get(id)
            if not entity:
                return None

            for key, value in data.items():
                if value is not None and hasattr(entity, key):
                    setattr(entity, key, value)

            await self.session.flush()
            await self.session.refresh(entity)
            return entity

        async def delete(self, id: ID) -> bool:
            """Delete an entity."""
            entity = await self.get(id)
            if not entity:
                return False

            await self.session.delete(entity)
            await self.session.flush()
            return True

        async def count(self, **filters) -> int:
            """Count entities."""
            query = select(func.count()).select_from(self.model_class)

            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)

            result = await self.session.execute(query)
            return result.scalar() or 0

        async def commit(self):
            """Commit the current transaction."""
            await self.session.commit()

        async def rollback(self):
            """Rollback the current transaction."""
            await self.session.rollback()

except ImportError:
    SQLALCHEMY_AVAILABLE = False
    SQLAlchemyRepository = None  # type: ignore


# =============================================================================
# Repository Factory
# =============================================================================


class RepositoryFactory:
    """
    Factory for creating repository instances.

    Useful for dependency injection and testing.

    Example:
        factory = RepositoryFactory()
        factory.register("users", UserRepository)

        # In route handler
        user_repo = factory.create("users", session=db_session)
    """

    _repositories: Dict[str, Type[BaseRepository]] = {}

    @classmethod
    def register(cls, name: str, repository_class: Type[BaseRepository]) -> None:
        """Register a repository class."""
        cls._repositories[name] = repository_class
        logger.debug(f"Registered repository: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseRepository]]:
        """Get a registered repository class."""
        return cls._repositories.get(name)

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseRepository:
        """Create an instance of a registered repository."""
        repo_class = cls._repositories.get(name)
        if not repo_class:
            raise ValueError(f"Repository '{name}' not registered")
        return repo_class(**kwargs)

    @classmethod
    def list_repositories(cls) -> List[str]:
        """List all registered repository names."""
        return list(cls._repositories.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered repositories."""
        cls._repositories.clear()


# =============================================================================
# Utility Functions
# =============================================================================


def create_repository(model_class: Type[T], storage: str = "memory") -> BaseRepository[T, int]:
    """
    Create a repository for a model.

    Args:
        model_class: The Pydantic model class
        storage: Storage backend ("memory" or "sqlalchemy")

    Returns:
        A repository instance
    """
    if storage == "memory":
        return TypedInMemoryRepository(model_class)
    elif storage == "sqlalchemy":
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy is required for SQLAlchemy repositories. "
                "Install with: pip install sqlalchemy[asyncio]"
            )
        raise ValueError(
            "SQLAlchemy repositories require a session. "
            "Use SQLAlchemyRepository directly with a session."
        )
    else:
        raise ValueError(f"Unknown storage backend: {storage}")
