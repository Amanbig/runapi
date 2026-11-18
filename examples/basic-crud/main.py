"""CRUD example. Run with: runapi dev"""

from runapi import create_runapi_app

runapi_app = create_runapi_app(title="Todo API (runapi CRUD example)", version="0.1.0")
app = runapi_app.get_app()

if __name__ == "__main__":
    runapi_app.run()
