# Runapi 🚀

[![PyPI version](https://badge.fury.io/py/runapi.svg)](https://badge.fury.io/py/runapi)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Next.js-inspired file-based routing framework built on FastAPI for Python backend development. runapi makes building robust APIs as intuitive as creating files and folders.

## Why Runapi?

- 🚀 **Developer Experience**: Just like Next.js for React, runapi makes backend development intuitive
- ⚡ **Performance**: Built on FastAPI, one of the fastest Python frameworks
- 🛡️ **Production Ready**: Security, middleware, and error handling built-in
- 🎯 **Type Safe**: Full typing support with automatic validation
- 📁 **Intuitive**: File-based routing means your folder structure IS your API

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
pip install runapi
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn (for development server)

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Middleware](#middleware)
- [Error Handling](#error-handling)
- [CLI Commands](#cli-commands)
- [Advanced Usage](#advanced-usage)
- [Testing](#testing)
- [Deployment](#production-deployment)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)

## Quick Start

### 1. Create a new project

```bash
runapi init my-api
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
from runapi import JSONResponse

async def get():
    return JSONResponse({"message": "Hello runapi!"})
```

**routes/api/users.py** (GET,POST /api/users)
```python
from runapi import JSONResponse, Request

async def get():
    return JSONResponse({"users": []})

async def post(request: Request):
    body = await request.json()
    return JSONResponse({"created": body})
```

**routes/api/users/[id].py** (GET,PUT,DELETE /api/users/{id})
```python
from runapi import JSONResponse, Request

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
runapi dev
```

Visit `http://localhost:8000` to see your API!

## API Documentation

Once your server is running, you can access:

- **Interactive API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI JSON Schema**: `http://localhost:8000/openapi.json`

## Configuration

runapi uses environment variables for configuration. Create a `.env` file:

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

# Logging
LOG_LEVEL=INFO

# Static Files
STATIC_FILES_ENABLED=true
STATIC_FILES_PATH=static
STATIC_FILES_URL=/static

# JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRY=3600
JWT_REFRESH_EXPIRY=86400
```

### Configuration Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | boolean | `true` | Enable debug mode |
| `HOST` | string | `127.0.0.1` | Server host |
| `PORT` | integer | `8000` | Server port |
| `SECRET_KEY` | string | `dev-secret-key...` | Secret key for JWT |
| `CORS_ORIGINS` | string | `*` | Comma-separated allowed origins |
| `CORS_CREDENTIALS` | boolean | `true` | Allow credentials in CORS |
| `RATE_LIMIT_ENABLED` | boolean | `false` | Enable rate limiting |
| `RATE_LIMIT_CALLS` | integer | `100` | Requests per period |
| `RATE_LIMIT_PERIOD` | integer | `60` | Rate limit period in seconds |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `DATABASE_URL` | string | `None` | Database connection URL |

## Authentication

runapi includes built-in JWT authentication:

### Enable Authentication Middleware

**main.py**
```python
from runapi import create_runapi_app

app = create_runapi_app()

# Protect specific routes
app.add_auth_middleware(
    protected_paths=["/api/protected"],
    excluded_paths=["/api/auth/login", "/docs"]
)
```

### Create Login Route

**routes/api/auth/login.py**
```python
from runapi import JSONResponse, Request, create_token_response, verify_password

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
from runapi import JSONResponse, get_current_user, Depends

async def get(current_user: dict = Depends(get_current_user())):
    return JSONResponse({
        "message": "This is protected!",
        "user": current_user
    })
```

## Middleware

runapi includes several built-in middleware:

```python
from runapi import create_runapi_app

app = create_runapi_app()

# Built-in middleware (automatically configured via .env)
# - CORS
# - Rate limiting  
# - Security headers
# - Request logging
# - Compression

# Add custom middleware
from runapi import RunApiMiddleware

class CustomMiddleware(RunApiMiddleware):
    async def dispatch(self, request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response

app.add_middleware(CustomMiddleware)
```

## Error Handling

runapi provides comprehensive error handling:

```python
from runapi import ValidationError, NotFoundError, raise_not_found

async def get_user(user_id: str):
    if not user_id:
        raise ValidationError("User ID is required")
    
    user = find_user(user_id)
    if not user:
        raise_not_found("User not found")
    
    return user
```

## CLI Commands

runapi includes a powerful CLI for development:

```bash
# Create new project
runapi init my-project

# Run development server
runapi dev

# Generate boilerplate code
runapi generate route users
runapi generate middleware auth
runapi generate main

# List all routes
runapi routes

# Show project info
runapi info
```

## Advanced Usage

### Custom Application Setup

**main.py**
```python
from runapi import create_runapi_app, get_config

# Load custom configuration
config = get_config()

# Create app with custom settings
app = create_runapi_app(
    title="My API",
    description="Built with runapi",
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
from runapi import get_config

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
from runapi import JSONResponse

async def send_email(email: str):
    # Send email logic
    pass

async def post(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    background_tasks.add_task(send_email, body["email"])
    return JSONResponse({"message": "Email queued"})
```

## Dynamic Routes

runapi supports dynamic route parameters:

- `routes/users/[id].py` → `/users/{id}`
- `routes/posts/[slug].py` → `/posts/{slug}`  
- `routes/api/[...path].py` → `/api/{path:path}` (catch-all)

## File Uploads

```python
from fastapi import UploadFile, File
from runapi import JSONResponse

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
    assert response.json()["message"] == "Hello runapi!"
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

## WebSockets

runapi supports WebSocket connections through FastAPI:

```python
# routes/ws/chat.py
from fastapi import WebSocket
from runapi import get_app

app = get_app()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")
```

## API Reference

### Core Functions

#### `create_runapi_app(**kwargs)`
Creates a runapi application instance.

**Parameters:**
- `title` (str): API title
- `description` (str): API description  
- `version` (str): API version
- `config` (runapiConfig): Custom configuration

**Returns:** runapiApp instance

#### `get_config()`
Returns the global configuration instance.

#### `load_config(env_file: str = None)`
Loads configuration from environment file.

### Authentication Functions

#### `create_access_token(data: dict, expires_delta: timedelta = None)`
Creates a JWT access token.

#### `verify_token(token: str)`
Verifies and decodes a JWT token.

#### `hash_password(password: str)`
Hashes a password using bcrypt.

#### `verify_password(plain_password: str, hashed_password: str)`
Verifies a password against its hash.

### Error Functions

#### `raise_validation_error(message: str, details: dict = None)`
Raises a validation error (400).

#### `raise_not_found(message: str = "Resource not found")`
Raises a not found error (404).

#### `raise_auth_error(message: str = "Authentication required")`
Raises an authentication error (401).

## Route Conventions

### File Naming

- `index.py` → Root path `/`
- `users.py` → `/users`
- `[id].py` → `/{id}` (dynamic parameter)
- `[...slug].py` → `/{slug:path}` (catch-all)

### HTTP Methods

Export async functions named after HTTP methods:

```python
async def get():        # GET request
async def post():       # POST request
async def put():        # PUT request
async def delete():     # DELETE request
async def patch():      # PATCH request
```

### Request Handling

```python
from runapi import Request, JSONResponse

async def post(request: Request):
    # Get JSON body
    body = await request.json()
    
    # Get path parameters
    user_id = request.path_params.get("id")
    
    # Get query parameters
    limit = request.query_params.get("limit", 10)
    
    # Get headers
    auth_header = request.headers.get("authorization")
    
    return JSONResponse({"status": "success"})
```

## Troubleshooting

### Common Issues

**Import Error: No module named 'runapi'**
```bash
pip install runapi
```

**Routes not loading**
- Ensure `routes/` directory exists in your project root
- Check that route files have proper async function exports
- Verify file naming conventions

**Authentication not working**
- Set a proper `SECRET_KEY` in production
- Check that protected paths are correctly configured
- Verify JWT token format and expiration

**CORS Issues**
- Configure `CORS_ORIGINS` in your `.env` file
- Set `CORS_CREDENTIALS=true` if needed
- Check that your frontend origin is included

### Debug Mode

Enable debug mode for detailed error messages:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Performance Tips

1. **Use async/await**: All route functions should be async
2. **Enable compression**: Built-in gzip compression for responses
3. **Configure rate limiting**: Protect against abuse
4. **Use proper HTTP status codes**: For better client handling
5. **Implement caching**: For frequently accessed data

## Security Best Practices

1. **Change default secret key** in production
2. **Use HTTPS** in production
3. **Configure CORS** properly
4. **Implement rate limiting**
5. **Validate all inputs**
6. **Use environment variables** for sensitive data

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
runapi dev
```

## Roadmap

- [ ] Database integration helpers (SQLAlchemy, MongoDB)
- [ ] Built-in caching mechanisms (Redis, in-memory)
- [ ] WebSocket routing support
- [ ] Background task queue integration
- [ ] Plugin system
- [ ] More authentication providers (OAuth, LDAP)
- [ ] Performance monitoring and metrics
- [ ] GraphQL support

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/Amanbig/runapi.git
cd runapi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e .
pip install pytest httpx
```

4. Run tests:
```bash
python -m pytest tests/
```

### Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Create detailed commit messages
- Open an issue before major changes

### Reporting Issues

Please include:
- Python version
- runapi version
- Minimal code example
- Full error traceback
- Expected vs actual behavior

## Changelog

### v0.1.1 (Latest)
- **Bug Fix**: Fixed `runapi dev` command failing to import main module
- **Enhancement**: Improved CLI error handling and validation
- **Enhancement**: Better Python path management for uvicorn integration
- **Enhancement**: Added pre-validation of main.py before server startup

### v0.1.1
- Initial release
- File-based routing system
- JWT authentication
- Middleware stack
- CLI tools
- Configuration management
- Error handling system

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Community

- 📚 [Documentation](https://github.com/Amanbig/runapi)
- 🐛 [Issue Tracker](https://github.com/Amanbig/runapi/issues)
- 💬 [Discussions](https://github.com/Amanbig/runapi/discussions)
- 📧 [Email](mailto:amanpreetsinghjhiwant7@gmail.com)

## Acknowledgments

- Built on top of [FastAPI](https://fastapi.tiangolo.com/) by Sebastián Ramirez
- Inspired by [Next.js](https://nextjs.org/) file-based routing by Vercel
- Uses [Typer](https://typer.tiangolo.com/) for CLI by Sebastián Ramirez
- Password hashing with [Passlib](https://passlib.readthedocs.io/)
- Testing with [pytest](https://pytest.org/) and [httpx](https://www.python-httpx.org/)

## Related Projects

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for Python
- [Starlette](https://www.starlette.io/) - Lightweight ASGI framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation using Python type hints
- [Next.js](https://nextjs.org/) - React framework (inspiration)

## Support

If runapi has been helpful to your project:

- ⭐ Star the repo on GitHub
- 🐛 Report bugs and request features
- 📝 Contribute to documentation
- 💰 [Sponsor the project](https://github.com/sponsors/Amanbig)

---

<div align="center">

**runapi** - Making Python backend development as intuitive as frontend development! 🚀

[Get Started](https://github.com/Amanbig/runapi) | [Documentation](https://github.com/Amanbig/runapi) | [Examples](https://github.com/Amanbig/runapi/tree/main/example)

</div>