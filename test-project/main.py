"""
PyNext Application Entry Point
"""
from pynext import create_pynext_app

# Create PyNext application
pynext_app = create_pynext_app(
    title="My PyNext API",
    description="Built with PyNext framework",
    version="1.0.0"
)

# Get FastAPI app for uvicorn
app = pynext_app.get_app()

if __name__ == "__main__":
    pynext_app.run()
