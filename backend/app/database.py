"""
MongoDB database configuration and connection setup
"""
from mongoengine import connect, disconnect
from app.config import settings

_db_connected = False

def init_db():
    """Initialize MongoDB connection"""
    global _db_connected

    if _db_connected:
        return

    connect(
        db=settings.MONGO_DB_NAME,
        host=settings.MONGO_URL,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
        maxPoolSize=50
    )
    _db_connected = True
    print(f"✓ Connected to MongoDB: {settings.MONGO_DB_NAME}")

def close_db():
    """Close MongoDB connection"""
    global _db_connected

    if not _db_connected:
        return

    disconnect()
    _db_connected = False
    print("✓ Disconnected from MongoDB")

