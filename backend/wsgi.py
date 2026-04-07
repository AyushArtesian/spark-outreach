"""
Production WSGI server entry point for deployment
"""
from app.main import app
import os

# Set environment variables for production
os.environ.setdefault('DEBUG', 'False')

# For deployment with Gunicorn: gunicorn wsgi:app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
