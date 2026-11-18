## runapi v0.3.5

First-class database support (pick your database with an extra, get sessions, migrations and a working example), plus developer-experience polish.

### ✨ Developer experience
- **Clearer route errors**: a route file that defines no handlers now logs a warning explaining why the URL returns 404, and suggests renames for near-misses such as `GET` or `get_users` (`app.route_warnings`)
- **`LOG_REQUESTS`**: turn request/response logging on or off independently of `DEBUG` (default: same as `DEBUG`)
- **`DATABASE_URL` checks**: malformed URLs are an error (fatal in production); `postgres://` and URLs without an async driver produce a warning with the exact fix
- **New example**: `examples/basic-crud`, a todo API showing routes -> service -> repository, with curl commands and tests
- Docs: `DATABASE_URL` reference and a routing troubleshooting section

### 🗄️ Database
- **New extras**: `runapi[sqlite]`, `runapi[postgres]`, `runapi[mysql]` install SQLAlchemy, Alembic and the matching async driver. `runapi[db]` stays as an alias for the SQLite stack. The code is identical across databases; only `DATABASE_URL` changes
- **`Database`**: async engine and session manager. `Depends(database.get_session)` gives a session that commits when the request succeeds and rolls back on errors. `runapi_app.use_database(database)` connects on startup, disposes on shutdown and adds a `database` check to `/ready`. `runapi.Base` is the declarative base for models
- **`runapi init --db sqlite|postgres`** scaffolds models, `db.py`, an example route, migrations and, for PostgreSQL, a `docker-compose.yml`
- **`runapi db init`** now sets up an async Alembic environment that reads `DATABASE_URL` and `Base.metadata` (SQLite-safe batch mode included); `db migrate | upgrade | downgrade` use it
- **`runapi doctor`** checks that the driver for your `DATABASE_URL` is installed and prints the exact `pip install runapi[...]` fix

### 📚 Examples & docs
- New `examples/postgres-todo`: async CRUD on PostgreSQL with a committed migration and `docker-compose.yml` (also runs on SQLite)
- CI runs that example against a real PostgreSQL service container
- New docs: rewritten *Database & migrations* and a *Schemas & storage* page (registration, collisions, storage modes, in-memory limits)

### 🐛 Fixes
- Schema files now load in alphabetical order, so which class wins a duplicate short name is deterministic (it used to depend on the filesystem)
- `runapi doctor` no longer swallows `[extra]` text in hints

### ✅ Tests
- 40+ new tests: database sessions and rollback, driver hints, init/db CLI flows, schema registration and failure cases, and the PostgreSQL example end to end
