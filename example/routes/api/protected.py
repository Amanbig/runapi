"""
Protected API route - requires authentication
GET /api/protected
POST /api/protected
PUT /api/protected
"""
from pynext import JSONResponse, Request, get_current_user, Depends
from datetime import datetime

async def get(current_user: dict = Depends(get_current_user())):
    """Handle GET request to protected endpoint."""
    return JSONResponse({
        "message": "This is a protected endpoint",
        "description": "Authentication required - JWT token needed",
        "timestamp": datetime.utcnow().isoformat(),
        "user": {
            "id": current_user.get("sub"),
            "username": current_user.get("username", "unknown"),
            "roles": current_user.get("roles", []),
            "permissions": current_user.get("permissions", [])
        },
        "methods": ["GET", "POST", "PUT"],
        "data": {
            "server_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "framework": "PyNext",
            "protected": True,
            "authenticated": True
        },
        "status": "success"
    })

async def post(request: Request, current_user: dict = Depends(get_current_user())):
    """Handle POST request to protected endpoint."""
    try:
        # Get request body (if any)
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except Exception:
        body = {}
    
    return JSONResponse({
        "message": "Protected POST request received",
        "description": "Data processed with authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "user": {
            "id": current_user.get("sub"),
            "username": current_user.get("username", "unknown")
        },
        "received_data": body,
        "processed": True,
        "protected": True,
        "authenticated": True,
        "status": "success"
    })

async def put(request: Request, current_user: dict = Depends(get_current_user())):
    """Handle PUT request to protected endpoint."""
    try:
        # Get request body (if any)
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except Exception:
        body = {}
    
    return JSONResponse({
        "message": "Protected PUT request received",
        "description": "Data updated with authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "user": {
            "id": current_user.get("sub"),
            "username": current_user.get("username", "unknown")
        },
        "received_data": body,
        "updated": True,
        "protected": True,
        "authenticated": True,
        "status": "success"
    })