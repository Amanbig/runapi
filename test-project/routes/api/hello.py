"""
Example API route
GET /api/hello
"""
from pynext import JSONResponse

async def get():
    return JSONResponse({
        "message": "Hello from PyNext!",
        "framework": "PyNext",
        "status": "success"
    })
