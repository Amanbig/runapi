# PyNext 🚀

A Next.js-inspired file-based routing framework built on FastAPI for Python backend development.

## Features

- 📁 **File-based routing** - Create API routes by simply adding Python files
- ⚡ **FastAPI integration** - Built on top of FastAPI for high performance
- 🔐 **Authentication system** - JWT-based auth with middleware support
- 🛡️ **Middleware stack** - Built-in middleware for CORS, rate limiting, security headers
- ⚙️ **Configuration management** - Environment-based configuration with `.env` support
- 🚨 **Error handling** - Comprehensive error handling with custom exceptions
- 🔧 **CLI tools** - Command-line interface for project management
- 📝 **Auto-documentation** - Automatic API documentation via FastAPI
- 🎯 **Type hints** - Full typing support with Pydantic integration

## Installation

```bash
pip install pynext
```

## Quick Start

### 1. Create a new project

```bash
pynext init my-api
cd my-api
```

### 2. Project Structure

```
my-api/
├── routes/              # API routes (file-based routing)
│   ├── index.py        # GET /
│   └── api/
│       ├── users.py    # GET, POST /api/users
│       └── users/
│           └── [id].py # GET, PUT, DELETE /api/users/{id}
├── static/             # Static files
├── uploads/            # File uploads directory  
├── main.py            # Application entry point
├── .env               # Configuration file
└── README.md
```

### 3. Create routes

Routes are created by adding Python files in the `routes/` directory:

**routes/index.py** (GET /)
```python
from pynext import JSONResponse

async def get():
    return JSONResponse({"message": "Hello PyNext!"})
```

**routes/api/users.py** (GET,POST /api/users)
```python
from pynext import JSONResponse, Request

async def get():
    return JSONResponse({"users": []})

async def post(request: Request):
    body = await request.json()
    return JSONResponse({"created": body})
```

**routes/api/users/[id].py** (GET,PUT,DELETE /api/users/{id})
```python
from pynext import JSONResponse, Request

async def get(request: Request):
    user_id = request.path_params["id"]
    return JSONResponse({"user_id": user_id})

async def put(request: Request):
    user_id = request.path_params["id"]
    body = await request.json()
    return JSONResponse({"user_id": user_id, "updated": body})

async def delete(request: Request):
    user_id = request.path_params["id"]
    return JSONResponse({"user_id": user_id, "deleted": True})
```

### 4. Run development server

```bash
pynext dev
```

Visit `http://localhost:8000` to see your API!

## Configuration

PyNext uses environment variables for configuration. Create a `.env` file:

```env
# Server Settings
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# Database (example)
DATABASE_URL=sqlite:///./app.db
```

## Authentication

PyNext includes built-in JWT authentication:

### Enable Authentication Middleware

**main.py**
```python
from pynext import create_pynext_app

app = create_pynext_app()

# Protect specific routes
app.add_auth_middleware(
    protected_paths=["/api/protected"],
    excluded_paths=["/api/auth/login", "/docs"]
)
```

### Create Login Route

**routes/api/auth/login.py**
```python
from pynext import JSONResponse, Request, create_token_response, verify_password

async def post(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")
    
    # Verify credentials (implement your logic)
    if verify_credentials(username, password):
        user_data = {"sub": "user_id", "username": username}
        tokens = create_token_response(user_data)
        return JSONResponse(tokens.dict())
    
    return JSONResponse({"error": "Invalid credentials"}, status_code=401)
```

### Protected Routes

**routes/api/protected.py**
```python
from pynext import JSONResponse, get_current_user, Depends

async def get(current_user: dict = Depends(get_current_user())):
    return JSONResponse({
        "message": "This is protected!",
        "user": current_user
    })
```

## Middleware

PyNext includes several built-in middleware:

```python
from pynext import create_pynext_app

app = create_pynext_app()

# Built-in middleware (automatically configured via .env)
# - CORS
# - Rate limiting  
# - Security headers
# - Request logging
# - Compression

# Add custom middleware
from pynext import PyNextMiddleware

class CustomMiddleware(PyNextMiddleware):
    async def dispatch(self, request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response

app.add_middleware(CustomMiddleware)
```

## Error Handling

PyNext provides comprehensive error handling:

```python
from pynext import ValidationError, NotFoundError, raise_not_found

async def get_user(user_id: str):
    if not user_id:
        raise ValidationError("User ID is required")
    
    user = find_user(user_id)
    if not user:
        raise_not_found("User not found")
    
    return user
```

## CLI Commands

PyNext includes a powerful CLI for development:

```bash
# Create new project
pynext init my-project

# Run development server
pynext dev

# Generate boilerplate code
pynext generate route users
pynext generate middleware auth
pynext generate main

# List all routes
pynext routes

# Show project info
pynext info
```

## Advanced Usage

### Custom Application Setup

**main.py**
```python
from pynext import create_pynext_app, get_config

# Load custom configuration
config = get_config()

# Create app with custom settings
app = create_pynext_app(
    title="My API",
    description="Built with PyNext",
    version="1.0.0"
)

# Add custom middleware
app.add_auth_middleware()

# Add custom startup/shutdown events
@app.get_app().on_event("startup")
async def startup():
    print("Starting up!")

# Get underlying FastAPI app
fastapi_app = app.get_app()
```

### Database Integration

```python
# Using SQLAlchemy (example)
from sqlalchemy import create_engine
from pynext import get_config

config = get_config()
engine = create_engine(config.database_url)

# Use in routes
async def get_users():
    # Your database logic here
    pass
```

### Background Tasks

```python
from fastapi import BackgroundTasks
from pynext import JSONResponse

async def send_email(email: str):
    # Send email logic
    pass

async def post(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    background_tasks.add_task(send_email, body["email"])
    return JSONResponse({"message": "Email queued"})
```

## Dynamic Routes

PyNext supports dynamic route parameters:

- `routes/users/[id].py` → `/users/{id}`
- `routes/posts/[slug].py` → `/posts/{slug}`  
- `routes/api/[...path].py` → `/api/{path:path}` (catch-all)

## File Uploads

```python
from fastapi import UploadFile, File
from pynext import JSONResponse

async def post(file: UploadFile = File(...)):
    contents = await file.read()
    # Process file
    return JSONResponse({"filename": file.filename})
```

## Testing

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app.get_app())

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello PyNext!"
```

## Production Deployment

### Using Docker

**Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Examples

Check out the `/example` directory for a complete example application demonstrating:

- File-based routing
- Authentication with JWT
- Protected routes
- Error handling
- Middleware usage
- Configuration management

Run the example:

```bash
cd example
pynext dev
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on top of [FastAPI](https://fastapi.tiangolo.com/)
- Inspired by [Next.js](https://nextjs.org/) file-based routing
- Uses [Typer](https://typer.tiangolo.com/) for CLI
- Password hashing with [Passlib](https://passlib.readthedocs.io/)

---

**PyNext** - Making Python backend development as intuitive as frontend development! 🚀