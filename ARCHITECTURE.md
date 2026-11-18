# Architecture

A map of the codebase for contributors. `runapi` is a thin layer on top of FastAPI: it discovers
files, wires up sensible defaults, and provides a CLI.

## Layout

```
runapi/
├── __init__.py      public API (re-exports; keep `__all__` in sync, tests check it)
├── config.py        typed settings (pydantic-settings) + startup validation
├── errors.py        exception types and FastAPI error handlers
├── core.py          RunApiApp: builds the FastAPI app and wires everything together
├── routing.py       pure route discovery: routes/ folder -> URL patterns
├── lifecycle.py     startup/shutdown hooks, /health and /ready
├── middleware.py    request logging, rate limiting, security headers, ...
├── logging.py       JSON logs and per-request IDs
├── backends.py      memory/Redis backends (rate limiting, token revocation)
├── auth.py          JWT, password hashing, auth dependencies
├── schemas.py       schema base classes and auto-discovery of schemas/
├── repository.py    repository pattern (in-memory, SQLAlchemy)
├── service.py       service layer helpers
└── cli/
    ├── __init__.py  the `runapi` entry point (`main`)
    ├── _app.py      shared Typer app and console
    ├── _templates.py   renders the files the CLI generates
    ├── commands/    one module per command group (server, project, generate, inspect, db)
    └── templates/   the generated files, as plain `*.tmpl` files with `@@placeholders@@`
```

Dependencies point downward: `config` and `errors` know nothing about the rest; `core` and `cli`
sit on top and import everything else.

## Startup flow (`RunApiApp.__init__`)

1. Create the `FastAPI` app (lifespan comes from `Lifecycle`).
2. Configure logging, then **validate the config** (production refuses unsafe settings).
3. Add default middleware (CORS, rate limiting, security headers, compression, request IDs).
4. Install error handlers.
5. **Discover routes** (`routing.discover_routes`) and register each file's router.
   In production a route that fails to import aborts startup (`STRICT_ROUTES`).
6. Load `schemas/`, mount static files, register `/health` and `/ready`.

## Routing rules

All path conventions live in `routing.py` (see its docstring). `runapi routes` and the app both
use `discover_routes`, so they cannot disagree.

## Where do I add...

| I want to... | Edit |
|--------------|------|
| a setting | field on `RunApiConfig` in `config.py` (env var = upper-cased name); add to `validate_settings` if it can be unsafe |
| a CLI command | a function in a module under `cli/commands/` decorated with `@app.command()` (new module: import it in `cli/__init__.py`) |
| a generated file | a `*.tmpl` under `cli/templates/` and a call to `render(...)`; `tests/test_cli_templates.py` picks it up automatically |
| a rate-limit / blacklist backend | subclass in `backends.py`, select it in `core.py` / `auth.py` |
| a public name | add to `runapi/__init__.py` **and** `__all__` |

## Testing

- `pytest tests` runs everything; CI enforces a coverage floor and a clean `mypy`.
- `tests/conftest.py` restores `os.environ` and the global config after each test.
- `scripts/e2e_smoke.py` is a manual end-to-end check (installs, scaffolds and starts a real server).

## Known trade-offs

- `config`, the JWT manager and the password manager are lazily created module-level singletons
  for convenience; `RunApiApp(config=...)` accepts an explicit config.
- Generated project data layers are in-memory until you swap in a database repository.
