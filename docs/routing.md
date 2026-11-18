# Routing

Files in `routes/` become endpoints. Export functions named after HTTP methods.

| File | URL |
|------|-----|
| `routes/index.py` | `/` |
| `routes/users/index.py` | `/users` |
| `routes/users/[id].py` | `/users/{id}` |
| `routes/users/[id]/posts.py` | `/users/{id}/posts` |
| `routes/docs/[...slug].py` | `/docs/{slug:path}` (catch-all) |
| `routes/(admin)/stats.py` | `/stats` (route groups are not in the URL) |

Static routes are matched before dynamic ones, and catch-all routes last.

```python
# routes/users/[id].py
async def get(id: int):
    return {"id": id}
```

## WebSockets

```python
# routes/chat.py
from fastapi import WebSocket


async def websocket(ws: WebSocket):
    await ws.accept()
    await ws.send_text("hello")
```
