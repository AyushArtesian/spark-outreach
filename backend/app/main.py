"""
FastAPI main application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pymongo.errors import PyMongoError
from mongoengine.connection import ConnectionFailure

from app.config import settings
from app.database import init_db, close_db, is_db_available
from app.routers import auth_router, campaigns_router, leads_router, ai_router, company_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize MongoDB
    try:
        init_db()
    except Exception as e:
        print(f"Warning: MongoDB initialization: {e}")
        if settings.MONGO_REQUIRED_ON_STARTUP:
            raise
        print("Continuing without MongoDB. Set MONGO_REQUIRED_ON_STARTUP=True to fail fast.")
    
    yield
    
    # Shutdown - Close MongoDB connection
    try:
        close_db()
    except Exception:
        pass

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Spark Outreach - AI-powered lead outreach platform with MongoDB",
    version="0.0.1",
    lifespan=lifespan
)


@app.exception_handler(PyMongoError)
async def mongodb_exception_handler(request: Request, exc: PyMongoError):
    """Return clean 503 responses when MongoDB is unavailable."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Please ensure MongoDB is running and reachable.",
            "error": "mongodb_unavailable",
        },
    )


@app.exception_handler(ConnectionFailure)
async def mongoengine_connection_exception_handler(request: Request, exc: ConnectionFailure):
    """Return clean 503 response when MongoEngine has no live default connection."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Please ensure MongoDB is running and reachable.",
            "error": "mongodb_unavailable",
        },
    )

# Add CORS middleware - must be added BEFORE route handlers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(campaigns_router, prefix=settings.API_V1_STR)
app.include_router(leads_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(company_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Spark Outreach API",
        "version": "0.0.1",
        "database": "connected" if is_db_available() else "unavailable",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = is_db_available()
    status_text = "healthy" if db_ok else "degraded"
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": status_text,
            "database": "connected" if db_ok else "unavailable",
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
