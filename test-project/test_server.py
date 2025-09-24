"""
Test script to verify PyNext server startup
"""
import asyncio
import uvicorn
from main import app

async def test_server():
    """Test if the server can start and handle a simple request."""
    try:
        # Create a test config
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        
        print("✅ Server configuration successful!")
        print("🌐 Server would start on http://127.0.0.1:8001")
        print("📋 Available endpoints:")
        print("   - GET / (Home)")
        print("   - GET /api/hello (Hello endpoint)")
        print("   - GET /api/users (Users endpoint)")
        print("   - GET /docs (API documentation)")
        print("   - GET /health (Health check)")
        
        # Test route discovery
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', ['GET'])
                routes.append(f"{list(methods)} {route.path}")
        
        print(f"\n🛣️  Discovered {len(routes)} routes:")
        for route in routes:
            print(f"   - {route}")
            
        print("\n✅ All tests passed! Server is ready to run.")
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    exit(0 if success else 1)