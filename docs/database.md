# Database & migrations

```bash
pip install "runapi[db]"
runapi db init                       # creates migrations/ (async Alembic template)
runapi db migrate -m "create users"  # autogenerate a migration
runapi db upgrade                    # apply (default: head)
runapi db downgrade                  # revert one step
```

Point `migrations/env.py` at your SQLAlchemy `Base.metadata` and set `sqlalchemy.url` in `alembic.ini`.
