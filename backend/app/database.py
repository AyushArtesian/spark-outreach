"""
MongoDB database configuration and connection setup
"""
from mongoengine import connect, disconnect, connection
from app.config import settings

_db_connected = False


def _try_ping() -> bool:
    """Ping MongoDB to verify the connection is actually reachable."""
    try:
        client = connection.get_connection()
        client.admin.command("ping")
        return True
    except Exception:
        return False

def init_db():
    """Initialize MongoDB connection"""
    global _db_connected

    if _db_connected:
        return

    try:
        connect(
            db=settings.MONGO_DB_NAME,
            host=settings.MONGO_URL,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            maxPoolSize=50,
        )
        if not _try_ping():
            raise RuntimeError("MongoDB ping failed")
        _db_connected = True
        print(f"✓ Connected to MongoDB: {settings.MONGO_DB_NAME}")
    except Exception:
        _db_connected = False
        try:
            disconnect()
        except Exception:
            pass
        raise

def close_db():
    """Close MongoDB connection"""
    global _db_connected

    if not _db_connected:
        return

    disconnect()
    _db_connected = False
    print("✓ Disconnected from MongoDB")


def is_db_available() -> bool:
    """Return current MongoDB availability without throwing."""
    if not _db_connected:
        return False
    return _try_ping()

