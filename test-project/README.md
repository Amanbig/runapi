# test-project

A PyNext API project.

## Getting Started

1. Install dependencies:
   ```bash
   pip install pynext
   ```

2. Run development server:
   ```bash
   cd test-project
   pynext dev
   ```

3. Open http://localhost:8000

## Project Structure

```
test-project/
├── routes/           # API routes (file-based routing)
│   ├── index.py     # GET /
│   └── api/
│       └── hello.py # GET /api/hello
├── static/          # Static files
├── uploads/         # File uploads
├── main.py          # Application entry point
└── .env            # Configuration
```

## Available Routes

- `GET /` - Home page
- `GET /api/hello` - Example API endpoint
- `GET /docs` - API documentation

## Adding Routes

Create Python files in the `routes/` directory:

- `routes/users.py` -> `GET /users`
- `routes/api/users/[id].py` -> `GET /api/users/123`
- `routes/api/auth/login.py` -> `GET /api/auth/login`

Export HTTP method functions:

```python
async def get():
    return {"message": "GET request"}

async def post():
    return {"message": "POST request"}
```
