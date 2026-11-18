## runapi v0.3.0

Production hardening and developer-experience release.

### 🛡️ Production hardening
- **Fail fast**: route files that fail to import now abort startup in production (`STRICT_ROUTES`, on by default when `ENVIRONMENT=production`); in development the full traceback is logged and `app.route_errors` lists them
- **Safe defaults**: new `ENVIRONMENT` setting (`development` / `production`). `DEBUG` defaults to off in production; `CORS_CREDENTIALS` now defaults to `false`; `*` combined with credentials is rejected
- **Startup validation**: `config.validate_settings()` flags default/short `SECRET_KEY`, debug in production and wildcard CORS/hosts. Production refuses to start on errors; `runapi start` runs the same checks and `runapi doctor` reports them
- **Health endpoints**: built-in `GET /health` and `GET /ready` (`HEALTH_ENABLED`); register checks with `app.add_readiness_check(name, fn)`. Your own `routes/health.py` takes precedence
- **Lifecycle hooks**: `@app.on_startup` / `@app.on_shutdown` (sync or async); a custom `lifespan=` is still honoured
- **Docker**: generated `Dockerfile` is multi-stage, runs as a non-root user and has a `HEALTHCHECK`
- `runapi start` sets `ENVIRONMENT=production` (inherited by workers)

### ⚙️ Typed configuration & logging
- Configuration is now built on `pydantic-settings`: typed values, range checks, and clear `ConfigurationError`s that name the bad variable (e.g. `PORT: Input should be a valid integer`) instead of silently falling back to defaults
- **Structured logging**: `LOG_JSON` (on by default in production) emits one JSON object per line; request logs include method, path, status and duration
- **Request IDs**: every request gets an `X-Request-ID` (an incoming one is honoured), returned in the response and attached to all log lines; use `runapi.get_request_id()` in your code

### 🔁 Shared state with Redis
- New `runapi[redis]` extra. Set `CACHE_BACKEND=redis` and `REDIS_URL` to share **rate limiting** and **token revocation** across workers and hosts
- Pluggable `RateLimitBackend` (`MemoryRateLimitBackend`, `RedisRateLimitBackend`) and `TokenBlacklist` (`RedisTokenBlacklist`) for custom storage. Redis rate limiting fails open; Redis token checks fail closed
- The in-memory rate limiter now purges expired windows, so memory no longer grows with every client seen

### ✅ Quality gate
- Type checking with mypy is now clean and **blocks CI**; CI also enforces a minimum test coverage (65%, currently 70%)
- Fixed type issues found along the way (implicit `Optional` defaults, protocol variance, untyped containers)
- New tests for CLI generators, `routes`, `schemas`, `info`, `doctor` and error paths; tests now isolate the process environment

### 🧰 Scaffolding & docs
- **`runapi generate crud <name>`** creates schema, repository, service and REST routes (`GET/POST /name`, `GET/PUT/DELETE /name/{id}`) in one command; it refuses to overwrite existing files
- Documentation site workflow: builds with `mkdocs build --strict` on PRs and deploys to GitHub Pages from `main` (one-time setup: Settings -> Pages -> Source: GitHub Actions)
- New docs pages: Configuration (full variable reference) and CRUD scaffolding

### 🐛 Fixes
- `routes/<folder>/index.py` is now served at `/folder`; it was only reachable at `/folder/` (a bare `/folder` returned a 307 redirect)

### ⚠️ Behaviour changes
- `RunApiConfig.validate()` is now `validate_settings()` (it clashed with Pydantic's `BaseModel.validate`)
- **Security**: the rate limiter no longer trusts `X-Forwarded-For` by default (it could be spoofed to bypass limits). Behind a proxy you control, set `TRUST_PROXY_HEADERS=true`
- Invalid configuration values now raise an error at startup instead of being ignored. `pydantic-settings>=2.2` is a new dependency
- Real environment variables now take precedence over values in `.env` (previously `.env` overwrote them) — required for Docker/Kubernetes
- `CORS_CREDENTIALS` defaults to `false`; new projects get explicit localhost CORS origins with credentials enabled
- `config.is_production()` now means `ENVIRONMENT=production` (it used to mean "debug is off")
