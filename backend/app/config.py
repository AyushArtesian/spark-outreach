"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env file BEFORE Settings is instantiated
load_dotenv(override=True)

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Spark Outreach API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Database - MongoDB
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "spark_outreach"
    MONGO_REQUIRED_ON_STARTUP: bool = False
    # For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/spark_outreach
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "gemini"  # "gemini" or "openai"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # OpenAI API (optional, for future use)
    OPENAI_API_KEY: Optional[str] = None
    
    # Hugging Face Inference API (for embeddings)
    HF_API_KEY: Optional[str] = None
    
    # SerpAPI & Serper API (for search)
    SERPAPI_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields without error

settings = Settings()
