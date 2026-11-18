# Configuration

Settings are read from environment variables, or from a `.env` file in the project root. Real environment variables always take precedence over `.env`. Values are typed and validated at startup: a bad value stops the app with a message naming the variable.

| Variable | Default |
|----------|---------|
| `ENVIRONMENT` | `development` |
| `DEBUG` | depends on `ENVIRONMENT` |
| `HOST` | `127.0.0.1` |
| `PORT` | `8000` |
| `RELOAD` | `True` |
| `SECRET_KEY` | (unsafe default; must be set) |
| `ALLOWED_HOSTS` | `*` |
| `CORS_ORIGINS` | `*` |
| `CORS_CREDENTIALS` | `False` |
| `CORS_METHODS` | `*` |
| `CORS_HEADERS` | `*` |
| `DATABASE_URL` | — |
| `DATABASE_ECHO` | `False` |
| `CACHE_BACKEND` | `memory` |
| `REDIS_URL` | — |
| `CACHE_TTL` | `300` |
| `RATE_LIMIT_ENABLED` | `False` |
| `RATE_LIMIT_CALLS` | `100` |
| `RATE_LIMIT_PERIOD` | `60` |
| `TRUST_PROXY_HEADERS` | `False` |
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | (see source) |
| `LOG_JSON` | depends on `ENVIRONMENT` |
| `LOG_REQUESTS` | same as `DEBUG` |
| `STATIC_FILES_ENABLED` | `True` |
| `STATIC_FILES_PATH` | `static` |
| `STATIC_FILES_URL` | `/static` |
| `MAX_UPLOAD_SIZE` | `10485760` |
| `UPLOAD_PATH` | `uploads` |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRY` | `3600` |
| `JWT_REFRESH_EXPIRY` | `86400` |
| `HEALTH_ENABLED` | `True` |
| `STRICT_ROUTES` | depends on `ENVIRONMENT` |

Lists (`CORS_ORIGINS`, `ALLOWED_HOSTS`, ...) are comma-separated.

## Environments

`ENVIRONMENT=production` (set automatically by `runapi start`) turns debug off, enables JSON logs and strict route loading, and makes unsafe settings (default `SECRET_KEY`, debug on, wildcard CORS with credentials) abort startup. See [Deployment](deployment.md).

Run `runapi doctor` to check your configuration.

## DATABASE_URL

Checked at startup. Use an async driver URL, for example:

| Database | URL |
|----------|-----|
| SQLite | `sqlite+aiosqlite:///./app.db` |
| PostgreSQL | `postgresql+asyncpg://user:password@localhost:5432/mydb` |
| MySQL | `mysql+aiomysql://user:password@localhost:3306/mydb` |

A value with no `://` is an error; `postgres://` or a URL without an async driver produces a warning with the fix.
