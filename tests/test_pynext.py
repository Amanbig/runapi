"""
Comprehensive test script for PyNext framework functionality
Tests core features including routing, middleware, authentication, and configuration
"""
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
import json
import httpx
import pytest
from fastapi.testclient import TestClient


def test_basic_app_creation():
    """Test basic PyNext app creation"""
    print("🧪 Testing basic app creation...")
    
    from pynext import create_pynext_app
    
    app = create_pynext_app(
        title="Test API",
        description="Test PyNext API",
        version="1.0.0"
    )
    
    fastapi_app = app.get_app()
    
    assert fastapi_app.title == "Test API"
    assert fastapi_app.description == "Test PyNext API"
    assert fastapi_app.version == "1.0.0"
    
    print("✅ Basic app creation test passed!")


def test_configuration_system():
    """Test configuration management"""
    print("🧪 Testing configuration system...")
    
    from pynext.config import PyNextConfig
    
    # Test with environment variables
    os.environ['DEBUG'] = 'true'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['PORT'] = '9000'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    config = PyNextConfig()
    
    assert config.debug == True
    assert config.host == '0.0.0.0'
    assert config.port == 9000
    assert config.secret_key == 'test-secret-key'
    
    print("✅ Configuration system test passed!")


def test_error_handling():
    """Test error handling system"""
    print("🧪 Testing error handling...")
    
    from pynext import ValidationError, NotFoundError, create_error_response
    
    # Test custom exceptions
    try:
        raise ValidationError("Test validation error", {"field": "username"})
    except ValidationError as e:
        assert e.status_code == 400
        assert e.error_code == "VALIDATION_ERROR"
        assert e.details == {"field": "username"}
    
    # Test error response creation
    error_response = create_error_response(
        message="Test error",
        status_code=404,
        error_code="TEST_ERROR"
    )
    
    assert error_response.status_code == 404
    
    print("✅ Error handling test passed!")


def test_authentication_system():
    """Test JWT authentication system"""
    print("🧪 Testing authentication system...")
    
    from pynext import create_access_token, verify_token
    
    # Test token creation and verification
    user_data = {
        "sub": "user123",
        "username": "testuser",
        "roles": ["user"]
    }
    
    token = create_access_token(user_data)
    assert isinstance(token, str)
    assert len(token.split('.')) == 3  # JWT has 3 parts
    
    # Test token verification
    payload = verify_token(token)
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
        index_route = '''
from pynext import JSONResponse

async def get():
    return JSONResponse({"message": "Hello from test route!"})
'''
        
        (routes_path / "index.py").write_text(index_route, encoding='utf-8')
        
        # Create API route
        api_path = routes_path / "api"
        api_path.mkdir()
        (api_path / "__init__.py").touch()
        
        test_route = '''
from pynext import JSONResponse, Request

async def get():
    return JSONResponse({"endpoint": "test", "method": "GET"})

async def post(request: Request):
    return JSONResponse({"endpoint": "test", "method": "POST"})
'''
        
        (api_path / "test.py").write_text(test_route, encoding='utf-8')
        
        # Change to temp directory to test route loading
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            from pynext import create_pynext_app
            app = create_pynext_app()
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
    
    from pynext import create_pynext_app, PyNextMiddleware
    
    # Custom test middleware
    class TestMiddleware(PyNextMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Test-Middleware"] = "active"
            return response
    
    app = create_pynext_app()
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
        dynamic_route = '''
from pynext import JSONResponse, Request

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
'''
        
        (users_path / "[id].py").write_text(dynamic_route, encoding='utf-8')
        
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            from pynext import create_pynext_app
            app = create_pynext_app()
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
    os.environ['CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:8080'
    os.environ['CORS_CREDENTIALS'] = 'true'
    
    from pynext import create_pynext_app
    app = create_pynext_app()
    
    with TestClient(app.get_app()) as client:
        # Test preflight request
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
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
        test_file.write_text("Hello from static file!", encoding='utf-8')
        
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            from pynext import create_pynext_app
            app = create_pynext_app()
            
            with TestClient(app.get_app()) as client:
                response = client.get("/static/test.txt")
                assert response.status_code == 200
                assert response.text == "Hello from static file!"
            
        finally:
            os.chdir(old_cwd)
    
    print("✅ Static file serving test passed!")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting PyNext Framework Tests\n")
    
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
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! PyNext framework is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the output above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)