"""
Home page route
GET /
"""
from pynext import JSONResponse

async def get():
    return JSONResponse({
        "message": "Welcome to PyNext!",
        "docs": "/docs",
        "routes": {
            "hello": "/api/hello"
        }
    })
