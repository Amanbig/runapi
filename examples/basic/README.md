# Basic example

```bash
pip install runapi
cp .env.example .env   # then set SECRET_KEY
runapi dev
```

| Route | File |
|-------|------|
| `GET /` | `routes/index.py` |
| `GET /health` | `routes/(public)/health.py` |
| `GET /api/users` | `routes/api/users/index.py` |
| `GET /api/users/{id}` | `routes/api/users/[id].py` |
| `WS /api/echo` | `routes/api/echo.py` |
