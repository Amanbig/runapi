# Deployment

```bash
runapi init my-api --docker
cd my-api
runapi build -t my-api
docker run -p 8000:8000 -e SECRET_KEY=... -e DEBUG=false my-api
```

## Production checklist

`runapi start` runs in production mode (`ENVIRONMENT=production`) and **refuses to start** when:

- `SECRET_KEY` is the default value
- `DEBUG` is enabled
- `CORS_ORIGINS=*` is combined with `CORS_CREDENTIALS=true`

Also set specific `CORS_ORIGINS` and `ALLOWED_HOSTS`. Run `runapi doctor` to check your configuration.

Real environment variables override values in `.env`, so inject secrets through your platform.

## Health checks

`GET /health` (liveness) and `GET /ready` (readiness) are built in. Add checks:

```python
runapi_app.add_readiness_check("db", lambda: db.ping())
```

## Startup and shutdown

```python
@runapi_app.on_startup
async def connect(): ...


@runapi_app.on_shutdown
async def disconnect(): ...
```

Route files that fail to import abort startup in production (`STRICT_ROUTES`).

## Configuration & logging

Settings are typed and validated at startup; a bad value (for example `PORT=abc`) stops the app with a message naming the variable.

Set `LOG_JSON=true` (the default when `ENVIRONMENT=production`) for JSON logs. Every request carries an `X-Request-ID` header, which also appears in your logs:

```python
from runapi import get_request_id

request_id = get_request_id()
```
