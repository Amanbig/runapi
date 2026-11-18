## runapi v0.3.0

Production hardening and developer-experience release.

### 🛡️ Production hardening
- **Fail fast**: route files that fail to import now abort startup in production (`STRICT_ROUTES`, on by default when `ENVIRONMENT=production`); in development the full traceback is logged and `app.route_errors` lists them
- **Safe defaults**: new `ENVIRONMENT` setting (`development` / `production`). `DEBUG` defaults to off in production; `CORS_CREDENTIALS` now defaults to `false`; `*` combined with credentials is rejected
- **Startup validation**: `config.validate()` flags default/short `SECRET_KEY`, debug in production and wildcard CORS/hosts. Production refuses to start on errors; `runapi start` runs the same checks and `runapi doctor` reports them
- **Health endpoints**: built-in `GET /health` and `GET /ready` (`HEALTH_ENABLED`); register checks with `app.add_readiness_check(name, fn)`. Your own `routes/health.py` takes precedence
- **Lifecycle hooks**: `@app.on_startup` / `@app.on_shutdown` (sync or async); a custom `lifespan=` is still honoured
- **Docker**: generated `Dockerfile` is multi-stage, runs as a non-root user and has a `HEALTHCHECK`
- `runapi start` sets `ENVIRONMENT=production` (inherited by workers)

### ⚠️ Behaviour changes
- Real environment variables now take precedence over values in `.env` (previously `.env` overwrote them) — required for Docker/Kubernetes
- `CORS_CREDENTIALS` defaults to `false`; new projects get explicit localhost CORS origins with credentials enabled
- `config.is_production()` now means `ENVIRONMENT=production` (it used to mean "debug is off")
