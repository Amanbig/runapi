"""RunApi Application Entry Point"""

from db import database

from runapi import create_runapi_app

runapi_app = create_runapi_app(
    title="Todo API (PostgreSQL example)",
    description="runapi + SQLAlchemy + Alembic",
    version="0.1.0",
)
runapi_app.use_database(database)  # connect on startup, dispose on shutdown, /ready check

app = runapi_app.get_app()

if __name__ == "__main__":
    runapi_app.run()
