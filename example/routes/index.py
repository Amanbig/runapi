"""
Home page route
GET /
"""
from pynext import JSONResponse

async def get():
    """Handle GET request to home page."""
    return JSONResponse({
        "message": "Welcome to PyNext Framework!",
        "description": "A Next.js-inspired file-based routing framework for Python",
        "framework": "PyNext",
        "version": "0.1.0",
        "features": [
            "File-based routing",
            "FastAPI integration",
            "JWT authentication",
            "Middleware support",
            "Configuration management",
            "Error handling",
            "CLI tools"
        ],
        "endpoints": {
            "documentation": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": {
                "public": "/api/public",
                "protected": "/api/protected",
                "auth": {
                    "login": "/api/auth/login",
                    "register": "/api/auth/register"
                },
                "users": {
                    "list": "/api/users",
                    "detail": "/api/users/{id}"
                }
            }
        },
        "status": "success"
    })