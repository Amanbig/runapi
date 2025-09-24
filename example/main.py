"""
PyNext Example Application
Demonstrates the usage of PyNext framework features
"""
from pynext import create_pynext_app, get_config

# Load configuration
config = get_config()

# Create PyNext application
pynext_app = create_pynext_app(
    title="PyNext Example API",
    description="Example application built with PyNext framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add authentication middleware for protected routes
pynext_app.add_auth_middleware(
    protected_paths=["/api/protected"],
    excluded_paths=["/", "/docs", "/redoc", "/openapi.json", "/api/auth/login", "/api/public"]
)

# Get FastAPI app for uvicorn
app = pynext_app.get_app()

# Add custom startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 PyNext Example API is starting up!")
    print(f"📖 Documentation available at: http://{config.host}:{config.port}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 PyNext Example API is shutting down!")

if __name__ == "__main__":
    pynext_app.run()