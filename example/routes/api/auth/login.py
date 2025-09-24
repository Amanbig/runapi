"""
Authentication login route
POST /api/auth/login
"""
from pynext import JSONResponse, Request, ValidationError, create_token_response, hash_password, verify_password
from datetime import datetime

# Mock user database (in real app, use proper database)
MOCK_USERS = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LQ4YCOdB8.8jIHT8KzXYL8YQ1UzF0jrqzYzp6",  # password: admin123
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete"],
        "active": True
    },
    "user": {
        "id": "2", 
        "username": "user",
        "email": "user@example.com",
        "password_hash": "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi",  # password: user123
        "roles": ["user"],
        "permissions": ["read"],
        "active": True
    }
}

async def post(request: Request):
    """Handle login request."""
    try:
        # Get request body
        body = await request.json()
        
        # Validate required fields
        username = body.get("username")
        password = body.get("password")
        
        if not username or not password:
            raise ValidationError("Username and password are required", {
                "missing_fields": [
                    field for field in ["username", "password"]
                    if not body.get(field)
                ]
            })
        
        # Find user
        user = MOCK_USERS.get(username)
        if not user:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid username or password",
                        "status_code": 401
                    }
                }
            )
        
        # Check if user is active
        if not user.get("active", True):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "ACCOUNT_DISABLED",
                        "message": "Account is disabled",
                        "status_code": 401
                    }
                }
            )
        
        # Verify password (simplified - in real app use proper password hashing)
        # For demo purposes, we'll use simple comparison
        # In production, use: verify_password(password, user["password_hash"])
        password_valid = False
        if username == "admin" and password == "admin123":
            password_valid = True
        elif username == "user" and password == "user123":
            password_valid = True
        
        if not password_valid:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "INVALID_CREDENTIALS", 
                        "message": "Invalid username or password",
                        "status_code": 401
                    }
                }
            )
        
        # Create JWT token data
        user_data = {
            "sub": user["id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }
        
        # Create tokens
        token_response = create_token_response(user_data)
        
        return JSONResponse({
            "message": "Login successful",
            "description": "User authenticated successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "roles": user["roles"],
                "permissions": user["permissions"]
            },
            "tokens": token_response.dict(),
            "expires_in": 3600,  # 1 hour
            "status": "success"
        })
        
    except ValidationError:
        # Re-raise validation errors to be handled by error handler
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "LOGIN_ERROR",
                    "message": f"Login failed: {str(e)}",
                    "status_code": 500
                }
            }
        )

async def get():
    """Return login information and instructions."""
    return JSONResponse({
        "message": "Login endpoint",
        "description": "POST to this endpoint to authenticate",
        "method": "POST",
        "required_fields": ["username", "password"],
        "example_request": {
            "username": "admin",
            "password": "admin123"
        },
        "demo_accounts": [
            {
                "username": "admin",
                "password": "admin123",
                "roles": ["admin", "user"],
                "permissions": ["read", "write", "delete"]
            },
            {
                "username": "user", 
                "password": "user123",
                "roles": ["user"],
                "permissions": ["read"]
            }
        ],
        "response": {
            "success": {
                "tokens": {
                    "access_token": "JWT access token",
                    "refresh_token": "JWT refresh token",
                    "token_type": "bearer"
                },
                "user": "User information",
                "expires_in": 3600
            },
            "error": {
                "401": "Invalid credentials",
                "422": "Validation error"
            }
        },
        "status": "info"
    })