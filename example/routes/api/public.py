"""
Public API route - no authentication required
GET /api/public
POST /api/public
"""
from pynext import JSONResponse, Request
from datetime import datetime

async def get():
    """Handle GET request to public endpoint."""
    return JSONResponse({
        "message": "This is a public endpoint",
        "description": "No authentication required",
        "timestamp": datetime.utcnow().isoformat(),
        "methods": ["GET", "POST"],
        "data": {
            "server_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "framework": "PyNext",
            "public": True
        },
        "status": "success"
    })

async def post(request: Request):
    """Handle POST request to public endpoint."""
    try:
        # Get request body (if any)
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except Exception:
        body = {}
    
    return JSONResponse({
        "message": "Public POST request received",
        "description": "Data processed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "received_data": body,
        "processed": True,
        "public": True,
        "status": "success"
    })