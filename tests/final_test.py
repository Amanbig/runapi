"""
Final Comprehensive Test Suite for RunApi Framework
Tests all major functionality and ensures everything works correctly
"""

import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


def test_framework_installation():
    """Test that RunApi is properly installed and importable"""
    print("🧪 Testing RunApi installation...")
    try:
        import runapi

        print("✅ RunApi framework imports successfully!")
        print(f"   Version: {getattr(runapi, '__version__', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_cli_functionality():
    """Test CLI is working"""
    print("🧪 Testing CLI functionality...")
    try:
        import subprocess

        result = subprocess.run(["runapi", "--help"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "RunApi" in result.stdout:
            print("✅ CLI is working correctly!")
            return True
        else:
            print(f"❌ CLI test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI test failed with exception: {e}")
        return False


def test_basic_app_creation():
    """Test basic RunApi app creation and configuration"""
    print("🧪 Testing basic app creation...")
    try:
        from runapi import create_runapi_app, get_config

        # Test app creation
        app = create_runapi_app(title="Test API", description="Test Description", version="1.0.0")

        fastapi_app = app.get_app()
        assert fastapi_app.title == "Test API"
        assert fastapi_app.description == "Test Description"
        assert fastapi_app.version == "1.0.0"

        # Test configuration
        config = get_config()
        assert hasattr(config, "debug")
        assert hasattr(config, "host")
        assert hasattr(config, "port")

        print("✅ Basic app creation and configuration works!")
        return True
    except Exception as e:
        print(f"❌ App creation test failed: {e}")
        return False


def test_file_based_routing():
    """Test file-based routing with actual route files"""
    print("🧪 Testing file-based routing...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_path = Path(temp_dir)
            routes_path = temp_path / "routes"
            routes_path.mkdir()
            (routes_path / "__init__.py").touch()

            # Create index route
            index_content = """
from runapi import JSONResponse

async def get():
    return JSONResponse({"message": "Hello from index", "route": "index"})
"""
            (routes_path / "index.py").write_text(index_content, encoding="utf-8")

            # Create API directory and route
            api_path = routes_path / "api"
            api_path.mkdir()
            (api_path / "__init__.py").touch()

            api_content = """
from runapi import JSONResponse, Request

async def get():
    return JSONResponse({"message": "API endpoint", "method": "GET"})

async def post(request: Request):
    return JSONResponse({"message": "API endpoint", "method": "POST"})
"""
            (api_path / "test.py").write_text(api_content, encoding="utf-8")

            # Create dynamic route
            users_path = routes_path / "users"
            users_path.mkdir()
            (users_path / "__init__.py").touch()

            dynamic_content = """
from runapi import JSONResponse, Request

async def get(request: Request):
    user_id = request.path_params.get("id", "unknown")
    return JSONResponse({"user_id": user_id, "method": "GET"})
"""
            (users_path / "[id].py").write_text(dynamic_content, encoding="utf-8")

            # Change to temp directory and test
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                from runapi import create_runapi_app

                app = create_runapi_app()

                with TestClient(app.get_app()) as client:
                    # Test index route
                    response = client.get("/")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["route"] == "index"

                    # Test API route
                    response = client.get("/api/test")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["method"] == "GET"

                    # Test POST to API route
                    response = client.post("/api/test")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["method"] == "POST"

                    # Test dynamic route
                    response = client.get("/users/123")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["user_id"] == "123"

                print("✅ File-based routing works correctly!")
                return True

            finally:
                os.chdir(old_cwd)

        except Exception as e:
            print(f"❌ File-based routing test failed: {e}")
            import traceback

            print(traceback.format_exc())
            return False


def test_middleware_and_security():
    """Test middleware functionality and security features"""
    print("🧪 Testing middleware and security...")
    try:
        from runapi import create_runapi_app

        app = create_runapi_app()

        with TestClient(app.get_app()) as client:
            # Test that security headers are added
            response = client.get("/docs")
            assert response.status_code == 200

            # Check for security headers
            headers = response.headers
            assert "X-Content-Type-Options" in headers
            assert headers["X-Content-Type-Options"] == "nosniff"
            assert "X-Frame-Options" in headers

            print("✅ Middleware and security features work!")
            return True
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        return False


def test_error_handling():
    """Test error handling system"""
    print("🧪 Testing error handling...")
    try:
        from runapi import ValidationError, create_error_response

        # Test custom exceptions
        try:
            raise ValidationError("Test validation error", {"field": "test"})
        except ValidationError as e:
            assert e.status_code == 400
            assert e.error_code == "VALIDATION_ERROR"
            assert e.details["field"] == "test"

        # Test error response creation
        response = create_error_response("Test error", 404, "TEST_ERROR")
        assert response.status_code == 404

        print("✅ Error handling system works!")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_generated_project():
    """Test that generated projects work correctly"""
    print("🧪 Testing generated project functionality...")

    # Test the current test-project if it exists
    if os.path.exists("test-project") and os.path.exists("test-project/main.py"):
        try:
            import sys

            sys.path.insert(0, "test-project")

            # Import the generated project's app
            from main import app

            with TestClient(app) as client:
                # Test index route
                response = client.get("/")
                assert response.status_code == 200
                data = response.json()
                assert "message" in data

                # Test API routes if they exist
                response = client.get("/api/hello")
                if response.status_code == 200:
                    data = response.json()
                    assert "message" in data

                # Test docs
                response = client.get("/docs")
                assert response.status_code == 200

            print("✅ Generated project works correctly!")
            return True

        except Exception as e:
            print(f"❌ Generated project test failed: {e}")
            return False
        finally:
            if "test-project" in sys.path:
                sys.path.remove("test-project")
    else:
        print("⏭️ Skipping generated project test (no test-project found)")
        return True


def test_documentation_generation():
    """Test automatic API documentation generation"""
    print("🧪 Testing API documentation generation...")
    try:
        from runapi import create_runapi_app

        app = create_runapi_app(
            title="Documentation Test API", description="Testing automatic docs generation"
        )

        with TestClient(app.get_app()) as client:
            # Test OpenAPI JSON
            response = client.get("/openapi.json")
            assert response.status_code == 200

            openapi_data = response.json()
            assert "openapi" in openapi_data
            assert "info" in openapi_data
            assert openapi_data["info"]["title"] == "Documentation Test API"

            # Test Swagger UI
            response = client.get("/docs")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

            # Test ReDoc
            response = client.get("/redoc")
            assert response.status_code == 200

        print("✅ API documentation generation works!")
        return True
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")
        return False


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 RunApi Framework - Final Comprehensive Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("Framework Installation", test_framework_installation),
        ("CLI Functionality", test_cli_functionality),
        ("Basic App Creation", test_basic_app_creation),
        ("File-based Routing", test_file_based_routing),
        ("Middleware & Security", test_middleware_and_security),
        ("Error Handling", test_error_handling),
        ("Generated Project", test_generated_project),
        ("Documentation Generation", test_documentation_generation),
    ]

    passed = 0
    failed = 0
    results = []

    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
                results.append((test_name, "✅ PASS"))
            else:
                failed += 1
                results.append((test_name, "❌ FAIL"))
        except Exception as e:
            failed += 1
            results.append((test_name, f"❌ ERROR: {e}"))

        print()

    # Print final summary
    print("=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)

    for test_name, result in results:
        print(f"{result:<10} {test_name}")

    print()
    print("📊 Summary:")
    print(f"   ✅ Passed: {passed}/{len(tests)}")
    print(f"   ❌ Failed: {failed}/{len(tests)}")
    print(f"   📈 Success Rate: {(passed / len(tests) * 100):.1f}%")
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED! RunApi framework is working perfectly!")
        print("🚀 The framework is ready for production use!")
        print()
        print("✨ Features successfully tested:")
        print("   • File-based routing with dynamic routes")
        print("   • Middleware system with security features")
        print("   • Configuration management")
        print("   • Error handling and custom exceptions")
        print("   • CLI tools for project management")
        print("   • Automatic API documentation")
        print("   • FastAPI integration")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the output above.")
        print("🔧 The framework may need additional debugging.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
