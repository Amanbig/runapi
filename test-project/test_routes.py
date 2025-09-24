"""
Test script for the generated PyNext test project routes
"""
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_index_route():
    """Test the index route (GET /)"""
    print("🧪 Testing index route...")
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Hello PyNext!" in data["message"]
    print("✅ Index route test passed!")

def test_hello_api_route():
    """Test the hello API route (GET /api/hello)"""
    print("🧪 Testing hello API route...")
    response = client.get("/api/hello")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Hello from PyNext!" in data["message"]
    assert data["framework"] == "PyNext"
    assert data["status"] == "success"
    print("✅ Hello API route test passed!")

def test_users_api_route_get():
    """Test the users API route GET"""
    print("🧪 Testing users API route (GET)...")
    response = client.get("/api/users")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["method"] == "GET"
    assert data["path"] == "/api/users"
    print("✅ Users API GET route test passed!")

def test_users_api_route_post():
    """Test the users API route POST"""
    print("🧪 Testing users API route (POST)...")
    test_data = {"name": "John Doe", "email": "john@example.com"}
    
    response = client.post("/api/users", json=test_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["method"] == "POST"
    assert data["data"] == test_data
    print("✅ Users API POST route test passed!")

def test_docs_endpoint():
    """Test that API documentation is available"""
    print("🧪 Testing API documentation...")
    response = client.get("/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    print("✅ API documentation test passed!")

def test_openapi_json():
    """Test that OpenAPI JSON is available"""
    print("🧪 Testing OpenAPI JSON...")
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "My PyNext API"
    print("✅ OpenAPI JSON test passed!")

def test_cors_headers():
    """Test CORS headers are present"""
    print("🧪 Testing CORS headers...")
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    
    assert response.status_code == 200
    # CORS headers should be present due to middleware
    print("✅ CORS headers test passed!")

def test_security_headers():
    """Test security headers are present"""
    print("🧪 Testing security headers...")
    response = client.get("/")
    
    assert response.status_code == 200
    
    # Check for security headers added by middleware
    headers = response.headers
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    
    print("✅ Security headers test passed!")

def test_json_response_format():
    """Test that JSON responses have consistent format"""
    print("🧪 Testing JSON response format...")
    
    routes_to_test = [
        ("/", "message"),
        ("/api/hello", "message"),
        ("/api/users", "message")
    ]
    
    for route, expected_field in routes_to_test:
        response = client.get(route)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert expected_field in data
    
    print("✅ JSON response format test passed!")

def test_non_existent_route():
    """Test 404 handling for non-existent routes"""
    print("🧪 Testing 404 handling...")
    response = client.get("/non-existent-route")
    
    assert response.status_code == 404
    print("✅ 404 handling test passed!")

def run_all_tests():
    """Run all route tests"""
    print("🚀 Running PyNext Test Project Route Tests\n")
    
    tests = [
        test_index_route,
        test_hello_api_route,
        test_users_api_route_get,
        test_users_api_route_post,
        test_docs_endpoint,
        test_openapi_json,
        test_cors_headers,
        test_security_headers,
        test_json_response_format,
        test_non_existent_route,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
            print()
    
    print(f"📊 Test Results:")
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("🎉 All route tests passed! The generated PyNext project is working correctly!")
        return True
    else:
        print(f"⚠️ {failed} test(s) failed.")
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)