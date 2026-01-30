"""
Comprehensive test script for RunApi framework functionality
Tests core features including routing, middleware, authentication, and configuration
"""

import asyncio
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


def test_basic_app_creation():
    """Test basic RunApi app creation"""
    print("🧪 Testing basic app creation...")

    from runapi import create_runapi_app

    app = create_runapi_app(title="Test API", description="Test RunApi API", version="1.0.0")

    fastapi_app = app.get_app()

    assert fastapi_app.title == "Test API"
    assert fastapi_app.description == "Test RunApi API"
    assert fastapi_app.version == "1.0.0"

    print("✅ Basic app creation test passed!")


def test_configuration_system():
    """Test configuration management"""
    print("🧪 Testing configuration system...")

    from runapi.config import RunApiConfig

    # Test with environment variables
    os.environ["DEBUG"] = "true"
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "9000"
    os.environ["SECRET_KEY"] = "test-secret-key"

    config = RunApiConfig()

    assert config.debug
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.secret_key == "test-secret-key"

    print("✅ Configuration system test passed!")


def test_error_handling():
    """Test error handling system"""
    print("🧪 Testing error handling...")

    from runapi import ValidationError, create_error_response

    # Test custom exceptions
    try:
        raise ValidationError("Test validation error", {"field": "username"})
    except ValidationError as e:
        assert e.status_code == 400
        assert e.error_code == "VALIDATION_ERROR"
        assert e.details == {"field": "username"}

    # Test error response creation
    error_response = create_error_response(
        message="Test error", status_code=404, error_code="TEST_ERROR"
    )

    assert error_response.status_code == 404

    print("✅ Error handling test passed!")


def test_authentication_system():
    """Test JWT authentication system"""
    print("🧪 Testing authentication system...")

    # Set a proper secret key for testing BEFORE importing
    os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long"

    # Use JWTManager directly with a custom secret key to avoid config caching issues
    from runapi.auth import JWTManager

    jwt_manager = JWTManager(secret_key="test-secret-key-at-least-32-characters-long")

    # Test token creation and verification
    user_data = {"sub": "user123", "username": "testuser", "roles": ["user"]}

    token = jwt_manager.create_access_token(user_data)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # JWT has 3 parts

    # Test token verification
    payload = jwt_manager.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["username"] == "testuser"

    print("✅ Authentication system test passed!")


def test_file_based_routing():
    """Test file-based routing system"""
    print("🧪 Testing file-based routing...")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        routes_path = temp_path / "routes"
        routes_path.mkdir()

        # Create a simple route file
        index_route = """
from runapi import JSONResponse

async def get():
    return JSONResponse({"message": "Hello from test route!"})
"""

        (routes_path / "index.py").write_text(index_route, encoding="utf-8")

        # Create API route
        api_path = routes_path / "api"
        api_path.mkdir()
        (api_path / "__init__.py").touch()

        test_route = """
from runapi import JSONResponse, Request

async def get():
    return JSONResponse({"endpoint": "test", "method": "GET"})

async def post(request: Request):
    return JSONResponse({"endpoint": "test", "method": "POST"})
"""

        (api_path / "test.py").write_text(test_route, encoding="utf-8")

        # Change to temp directory to test route loading
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()
            fastapi_app = app.get_app()

            # Test with TestClient
            with TestClient(fastapi_app) as client:
                # Test index route
                response = client.get("/")
                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "Hello from test route!"

                # Test API route
                response = client.get("/api/test")
                assert response.status_code == 200
                data = response.json()
                assert data["endpoint"] == "test"
                assert data["method"] == "GET"

                # Test POST to API route
                response = client.post("/api/test", json={"test": "data"})
                assert response.status_code == 200
                data = response.json()
                assert data["method"] == "POST"

        finally:
            os.chdir(old_cwd)

    print("✅ File-based routing test passed!")


def test_middleware_system():
    """Test middleware system"""
    print("🧪 Testing middleware system...")

    from runapi import RunApiMiddleware, create_runapi_app

    # Custom test middleware
    class TestMiddleware(RunApiMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Test-Middleware"] = "active"
            return response

    app = create_runapi_app()
    app.add_middleware(TestMiddleware)

    # Create a simple route for testing
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/test-middleware")
    async def test_endpoint():
        return {"message": "middleware test"}

    app.get_app().include_router(router)

    # Test middleware
    with TestClient(app.get_app()) as client:
        response = client.get("/test-middleware")
        assert response.status_code == 200
        assert response.headers.get("X-Test-Middleware") == "active"

    print("✅ Middleware system test passed!")


def test_dynamic_routes():
    """Test dynamic route parameters"""
    print("🧪 Testing dynamic routes...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        routes_path = temp_path / "routes"
        routes_path.mkdir()

        # Create users directory
        users_path = routes_path / "users"
        users_path.mkdir()
        (users_path / "__init__.py").touch()

        # Create dynamic route [id].py
        dynamic_route = """
from runapi import JSONResponse, Request

async def get(request: Request):
    user_id = request.path_params.get("id")
    return JSONResponse({
        "user_id": user_id,
        "message": f"User {user_id} retrieved"
    })

async def put(request: Request):
    user_id = request.path_params.get("id")
    body = await request.json()
    return JSONResponse({
        "user_id": user_id,
        "updated": body,
        "message": f"User {user_id} updated"
    })
"""

        (users_path / "[id].py").write_text(dynamic_route, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()
            fastapi_app = app.get_app()

            with TestClient(fastapi_app) as client:
                # Test GET with dynamic parameter
                response = client.get("/users/123")
                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == "123"
                assert "User 123 retrieved" in data["message"]

                # Test PUT with dynamic parameter
                test_data = {"name": "John Doe", "email": "john@example.com"}
                response = client.put("/users/456", json=test_data)
                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == "456"
                assert data["updated"] == test_data

        finally:
            os.chdir(old_cwd)

    print("✅ Dynamic routes test passed!")


def test_cors_configuration():
    """Test CORS configuration"""
    print("🧪 Testing CORS configuration...")

    # Set CORS configuration
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"
    os.environ["CORS_CREDENTIALS"] = "true"

    from runapi import create_runapi_app

    app = create_runapi_app()

    with TestClient(app.get_app()) as client:
        # Test preflight request
        response = client.options(
            "/", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
        )

        # Should allow the request
        assert response.status_code in [200, 204]

    print("✅ CORS configuration test passed!")


def test_static_file_serving():
    """Test static file serving"""
    print("🧪 Testing static file serving...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        static_path = temp_path / "static"
        static_path.mkdir()

        # Create a test file
        test_file = static_path / "test.txt"
        test_file.write_text("Hello from static file!", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()

            with TestClient(app.get_app()) as client:
                response = client.get("/static/test.txt")
                assert response.status_code == 200
                assert response.text == "Hello from static file!"

        finally:
            os.chdir(old_cwd)

    print("✅ Static file serving test passed!")


def test_schema_system():
    """Test schema base classes and utilities"""
    print("🧪 Testing schema system...")

    from datetime import datetime
    from typing import Optional

    from runapi import (
        BaseSchema,
        IDMixin,
        MessageResponse,
        PaginatedResponse,
        PaginationParams,
        TimestampMixin,
    )

    # Test BaseSchema
    class UserResponse(BaseSchema, IDMixin, TimestampMixin):
        email: str
        name: Optional[str] = None

    user = UserResponse(id=1, email="test@example.com", name="Test User", created_at=datetime.now())

    assert user.id == 1
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.created_at is not None

    # Test MessageResponse
    msg = MessageResponse(message="Operation successful")
    assert msg.message == "Operation successful"
    assert msg.success

    # Test PaginationParams
    params = PaginationParams(page=2, page_size=10)
    assert params.offset == 10  # (2-1) * 10
    assert params.limit == 10

    # Test PaginatedResponse
    items = [user]
    paginated = PaginatedResponse.create(items=items, total=100, page=1, page_size=10)
    assert paginated.total == 100
    assert paginated.pages == 10
    assert len(paginated.items) == 1

    print("✅ Schema system test passed!")


def test_schema_auto_discovery():
    """Test schema auto-discovery from schemas/ folder"""
    print("🧪 Testing schema auto-discovery...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        schemas_path = temp_path / "schemas"
        schemas_path.mkdir()
        (schemas_path / "__init__.py").touch()

        # Create a test schema file
        user_schema = """
from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
"""

        (schemas_path / "user.py").write_text(user_schema, encoding="utf-8")

        # Create nested schema
        api_schemas = schemas_path / "api"
        api_schemas.mkdir()
        (api_schemas / "__init__.py").touch()

        product_schema = """
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
"""

        (api_schemas / "product.py").write_text(product_schema, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi.schemas import SchemaRegistry, get_schema, list_schemas, load_schemas

            # Clear registry before test
            SchemaRegistry.clear()

            # Load schemas
            loaded = load_schemas(schemas_path)

            assert len(loaded) >= 2, f"Expected at least 2 modules, got {len(loaded)}"

            # Check registry
            user_create = get_schema("UserCreate")
            assert user_create is not None, "UserCreate schema not found"

            user_response = get_schema("UserResponse")
            assert user_response is not None, "UserResponse schema not found"

            product_create = get_schema("ProductCreate")
            assert product_create is not None, "ProductCreate schema not found"

            # Test schema functionality
            user = user_create(email="test@example.com", name="Test User")
            assert user.email == "test@example.com"

            # Test list_schemas
            schema_names = list_schemas()
            assert "UserCreate" in schema_names
            assert "ProductResponse" in schema_names

        finally:
            os.chdir(old_cwd)
            SchemaRegistry.clear()

    print("✅ Schema auto-discovery test passed!")


def test_schema_integration_with_routes():
    """Test using schemas in route handlers"""
    print("🧪 Testing schema integration with routes...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create schemas directory
        schemas_path = temp_path / "schemas"
        schemas_path.mkdir()
        (schemas_path / "__init__.py").touch()

        user_schema = """
from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
"""
        (schemas_path / "user.py").write_text(user_schema, encoding="utf-8")

        # Create routes directory
        routes_path = temp_path / "routes"
        routes_path.mkdir()
        (routes_path / "__init__.py").touch()

        api_path = routes_path / "api"
        api_path.mkdir()
        (api_path / "__init__.py").touch()

        # Create route that uses schemas
        users_route = '''
from runapi import JSONResponse, Request
from schemas.user import UserCreate, UserResponse

async def get():
    """Get list of users."""
    users = [
        {"id": 1, "email": "user1@example.com", "name": "User One"},
        {"id": 2, "email": "user2@example.com", "name": "User Two"},
    ]
    return JSONResponse([UserResponse(**u).model_dump() for u in users])

async def post(request: Request):
    """Create a new user."""
    body = await request.json()
    user_data = UserCreate(**body)
    # Simulate user creation
    new_user = UserResponse(id=123, email=user_data.email, name=user_data.name)
    return JSONResponse(new_user.model_dump(), status_code=201)
'''
        (api_path / "users.py").write_text(users_route, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Add temp_dir to path so schemas can be imported
            import sys

            sys.path.insert(0, temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()
            fastapi_app = app.get_app()

            with TestClient(fastapi_app) as client:
                # Test GET users
                response = client.get("/api/users")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["email"] == "user1@example.com"

                # Test POST user
                new_user_data = {"email": "new@example.com", "name": "New User"}
                response = client.post("/api/users", json=new_user_data)
                assert response.status_code == 201
                data = response.json()
                assert data["id"] == 123
                assert data["email"] == "new@example.com"
                assert data["name"] == "New User"

        finally:
            os.chdir(old_cwd)
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)

    print("✅ Schema integration with routes test passed!")


def test_repository_in_memory():
    """Test InMemoryRepository basic operations"""
    print("🧪 Testing InMemoryRepository...")

    from runapi import InMemoryRepository

    async def run_tests():
        repo = InMemoryRepository()

        # Test create
        user1 = await repo.create({"name": "John", "email": "john@example.com"})
        assert user1["id"] == 1
        assert user1["name"] == "John"
        assert "created_at" in user1

        user2 = await repo.create({"name": "Jane", "email": "jane@example.com"})
        assert user2["id"] == 2

        # Test get
        fetched = await repo.get(1)
        assert fetched["name"] == "John"

        # Test get_all
        all_users = await repo.get_all()
        assert len(all_users) == 2

        # Test get_all with filters
        johns = await repo.get_all(name="John")
        assert len(johns) == 1
        assert johns[0]["name"] == "John"

        # Test update
        updated = await repo.update(1, {"name": "Johnny"})
        assert updated["name"] == "Johnny"
        assert updated["email"] == "john@example.com"

        # Test count
        count = await repo.count()
        assert count == 2

        # Test exists
        assert await repo.exists(1)
        assert not await repo.exists(999)

        # Test delete
        deleted = await repo.delete(1)
        assert deleted

        remaining = await repo.get_all()
        assert len(remaining) == 1

        # Test get_by
        found = await repo.get_by(email="jane@example.com")
        assert found["name"] == "Jane"

        # Clear for next tests
        repo.clear()
        assert await repo.count() == 0

    asyncio.run(run_tests())
    print("✅ InMemoryRepository test passed!")


def test_typed_repository():
    """Test TypedInMemoryRepository with Pydantic models"""
    print("🧪 Testing TypedInMemoryRepository...")

    from datetime import datetime
    from typing import Optional

    from pydantic import BaseModel

    from runapi import TypedInMemoryRepository

    class User(BaseModel):
        id: Optional[int] = None
        name: str
        email: str
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None

    async def run_tests():
        repo = TypedInMemoryRepository(User)

        # Test create - returns User model instance
        user = await repo.create({"name": "Alice", "email": "alice@example.com"})
        assert isinstance(user, User)
        assert user.id == 1
        assert user.name == "Alice"

        # Test get - returns User model instance
        fetched = await repo.get(1)
        assert isinstance(fetched, User)
        assert fetched.email == "alice@example.com"

        # Test update - returns User model instance
        updated = await repo.update(1, {"name": "Alicia"})
        assert isinstance(updated, User)
        assert updated.name == "Alicia"

        # Test get_all - returns list of User instances
        all_users = await repo.get_all()
        assert all(isinstance(u, User) for u in all_users)

        repo.clear()

    asyncio.run(run_tests())
    print("✅ TypedInMemoryRepository test passed!")


def test_repository_factory():
    """Test RepositoryFactory registration and creation"""
    print("🧪 Testing RepositoryFactory...")

    from runapi import InMemoryRepository, RepositoryFactory

    # Clear any existing registrations
    RepositoryFactory.clear()

    # Test register
    RepositoryFactory.register("users", InMemoryRepository)

    # Test get
    repo_class = RepositoryFactory.get("users")
    assert repo_class == InMemoryRepository

    # Test list
    repos = RepositoryFactory.list_repositories()
    assert "users" in repos

    # Test create
    repo = RepositoryFactory.create("users")
    assert isinstance(repo, InMemoryRepository)

    # Clean up
    RepositoryFactory.clear()

    print("✅ RepositoryFactory test passed!")


def test_repository_with_routes():
    """Test using repositories in route handlers"""
    print("🧪 Testing repository integration with routes...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create routes directory
        routes_path = temp_path / "routes"
        routes_path.mkdir()
        (routes_path / "__init__.py").touch()

        api_path = routes_path / "api"
        api_path.mkdir()
        (api_path / "__init__.py").touch()

        # Create route that uses repository
        items_route = '''
from runapi import JSONResponse, Request, InMemoryRepository
from datetime import datetime

# Create repository instance
items_repo = InMemoryRepository()

def serialize_item(item):
    """Convert datetime objects to ISO format strings."""
    result = {}
    for k, v in item.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result

async def get():
    """Get all items."""
    items = await items_repo.get_all()
    return JSONResponse([serialize_item(i) for i in items])

async def post(request: Request):
    """Create a new item."""
    body = await request.json()
    item = await items_repo.create(body)
    return JSONResponse(serialize_item(item), status_code=201)
'''
        (api_path / "items.py").write_text(items_route, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()
            fastapi_app = app.get_app()

            with TestClient(fastapi_app) as client:
                # Initially empty
                response = client.get("/api/items")
                assert response.status_code == 200
                assert response.json() == []

                # Create item
                response = client.post("/api/items", json={"name": "Test Item", "price": 9.99})
                assert response.status_code == 201
                data = response.json()
                assert data["id"] == 1
                assert data["name"] == "Test Item"

                # Now should have one item
                response = client.get("/api/items")
                assert response.status_code == 200
                items = response.json()
                assert len(items) == 1

        finally:
            os.chdir(old_cwd)

    print("✅ Repository integration with routes test passed!")


def test_crud_service():
    """Test CRUDService basic operations"""
    print("🧪 Testing CRUDService...")

    from runapi import CRUDService, InMemoryRepository, NotFoundError

    async def run_tests():
        repo = InMemoryRepository()
        service = CRUDService(repo, "User")

        # Test create
        user = await service.create({"name": "John", "email": "john@example.com"})
        assert user["id"] == 1
        assert user["name"] == "John"

        # Test get
        fetched = await service.get(1)
        assert fetched["name"] == "John"

        # Test get - not found
        try:
            await service.get(999)
            raise AssertionError("Should have raised NotFoundError")
        except NotFoundError as e:
            assert "999" in str(e)

        # Test get_or_none
        result = await service.get_or_none(999)
        assert result is None

        # Test get_all
        await service.create({"name": "Jane", "email": "jane@example.com"})
        all_users = await service.get_all()
        assert len(all_users) == 2

        # Test update
        updated = await service.update(1, {"name": "Johnny"})
        assert updated["name"] == "Johnny"

        # Test update - not found
        try:
            await service.update(999, {"name": "Nobody"})
            raise AssertionError("Should have raised NotFoundError")
        except NotFoundError:
            pass

        # Test delete
        deleted = await service.delete(1)
        assert deleted

        # Test delete - not found
        try:
            await service.delete(999)
            raise AssertionError("Should have raised NotFoundError")
        except NotFoundError:
            pass

        # Test exists
        assert await service.exists(2)
        assert not await service.exists(999)

        # Test count
        count = await service.count()
        assert count == 1

        repo.clear()

    asyncio.run(run_tests())
    print("✅ CRUDService test passed!")


def test_validated_service():
    """Test ValidatedService with schema validation"""
    print("🧪 Testing ValidatedService...")

    from typing import Optional

    from pydantic import BaseModel, Field

    from runapi import InMemoryRepository, ValidatedService

    class UserCreate(BaseModel):
        name: str = Field(..., min_length=1)
        email: str

    class UserUpdate(BaseModel):
        name: Optional[str] = None
        email: Optional[str] = None

    class UserService(ValidatedService):
        create_schema = UserCreate
        update_schema = UserUpdate

    async def run_tests():
        repo = InMemoryRepository()
        service = UserService(repo, "User")

        # Test create with validation
        user = await service.create({"name": "Alice", "email": "alice@example.com"})
        assert user["name"] == "Alice"

        # Test create with invalid data
        try:
            await service.create({"name": "", "email": "test@example.com"})
            raise AssertionError("Should have raised validation error")
        except Exception:
            pass  # Pydantic validation error expected

        # Test update with validation
        updated = await service.update(user["id"], {"name": "Alicia"})
        assert updated["name"] == "Alicia"

        repo.clear()

    asyncio.run(run_tests())
    print("✅ ValidatedService test passed!")


def test_service_factory():
    """Test ServiceFactory registration and creation"""
    print("🧪 Testing ServiceFactory...")

    from runapi import CRUDService, InMemoryRepository, ServiceFactory

    # Clear any existing registrations
    ServiceFactory.clear()

    # Create repository
    repo = InMemoryRepository()

    # Test register
    ServiceFactory.register("users", CRUDService, repo, "User")

    # Test list
    services = ServiceFactory.list_services()
    assert "users" in services

    # Test get (creates and caches)
    service1 = ServiceFactory.get("users")
    service2 = ServiceFactory.get("users")
    assert service1 is service2  # Same instance

    # Test create (new instance)
    service3 = ServiceFactory.create("users")
    assert service3 is not service1  # Different instance

    # Clean up
    ServiceFactory.clear()

    print("✅ ServiceFactory test passed!")


def test_service_with_routes():
    """Test using services in route handlers"""
    print("🧪 Testing service integration with routes...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create routes directory
        routes_path = temp_path / "routes"
        routes_path.mkdir()
        (routes_path / "__init__.py").touch()

        api_path = routes_path / "api"
        api_path.mkdir()
        (api_path / "__init__.py").touch()

        # Create route that uses service
        products_route = '''
from runapi import JSONResponse, Request, InMemoryRepository, CRUDService, NotFoundError
from datetime import datetime

# Setup service layer
product_repo = InMemoryRepository()
product_service = CRUDService(product_repo, "Product")

def serialize(item):
    """Convert datetime objects to ISO format strings."""
    result = {}
    for k, v in item.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result

async def get():
    """Get all products."""
    products = await product_service.get_all()
    return JSONResponse([serialize(p) for p in products])

async def post(request: Request):
    """Create a new product."""
    body = await request.json()
    product = await product_service.create(body)
    return JSONResponse(serialize(product), status_code=201)
'''
        (api_path / "products.py").write_text(products_route, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            from runapi import create_runapi_app

            app = create_runapi_app()
            fastapi_app = app.get_app()

            with TestClient(fastapi_app) as client:
                # Initially empty
                response = client.get("/api/products")
                assert response.status_code == 200
                assert response.json() == []

                # Create product via service
                response = client.post("/api/products", json={"name": "Widget", "price": 19.99})
                assert response.status_code == 201
                data = response.json()
                assert data["id"] == 1
                assert data["name"] == "Widget"

                # Verify created
                response = client.get("/api/products")
                assert response.status_code == 200
                products = response.json()
                assert len(products) == 1

        finally:
            os.chdir(old_cwd)

    print("✅ Service integration with routes test passed!")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting RunApi Framework Tests\n")

    tests = [
        test_basic_app_creation,
        test_configuration_system,
        test_error_handling,
        test_authentication_system,
        test_file_based_routing,
        test_middleware_system,
        test_dynamic_routes,
        test_cors_configuration,
        test_static_file_serving,
        test_schema_system,
        test_schema_auto_discovery,
        test_schema_integration_with_routes,
        test_repository_in_memory,
        test_typed_repository,
        test_repository_factory,
        test_repository_with_routes,
        test_crud_service,
        test_validated_service,
        test_service_factory,
        test_service_with_routes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1

    print("\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed / (passed + failed) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 All tests passed! RunApi framework is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the output above.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
