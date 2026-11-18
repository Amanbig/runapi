## runapi v0.4.0

First-class database support: pick your database with an extra, get sessions, migrations and a working example.

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
