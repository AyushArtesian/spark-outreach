"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
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
        "database": "MongoDB",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
