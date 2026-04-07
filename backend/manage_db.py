"""
MongoDB database management utilities
"""
import sys
from mongoengine import connect, disconnect
from app.models import User, Campaign, Lead, Embedding
from app.utils.auth import get_password_hash
from app.config import settings

def init_db():
    """Initialize MongoDB connection and create indexes"""
    print("Connecting to MongoDB...")
    try:
        connect(
            db=settings.MONGO_DB_NAME,
            host=settings.MONGO_URL
        )
        print(f"✓ Connected to MongoDB: {settings.MONGO_DB_NAME}")
        print("✓ Database initialized successfully!")
        print("✓ Collections and indexes created")
    except Exception as e:
        print(f"✗ Error connecting to MongoDB: {e}")
        print("Make sure MongoDB is running. You can start it with:")
        print("  - Local: mongod")
        print("  - Docker: docker run -d -p 27017:27017 mongo")
        return False
    finally:
        disconnect()
    return True

def create_admin_user(email: str, password: str, full_name: str):
    """Create an admin user"""
    try:
        connect(
            db=settings.MONGO_DB_NAME,
            host=settings.MONGO_URL
        )
        
        # Check if user already exists
        existing_user = User.objects(email=email).first()
        if existing_user:
            print(f"✗ User with email {email} already exists!")
            return False
        
        # Create admin user
        admin_user = User(
            email=email,
            username=email.split('@')[0],
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_admin=True,
            is_active=True
        )
        admin_user.save()
        print(f"✓ Admin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        return True
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        return False
    finally:
        disconnect()

def reset_db():
    """Reset the database (drop all collections and recreate)"""
    print("WARNING: This will delete all data from MongoDB!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        try:
            connect(
                db=settings.MONGO_DB_NAME,
                host=settings.MONGO_URL
            )
            print("Dropping all collections...")
            User.drop_collection()
            Campaign.drop_collection()
            Lead.drop_collection()
            Embedding.drop_collection()
            print("✓ All collections dropped!")
            print("✓ Database reset successfully!")
        except Exception as e:
            print(f"✗ Error resetting database: {e}")
        finally:
            disconnect()
    else:
        print("Operation cancelled.")

def check_db():
    """Check MongoDB connection and status"""
    try:
        connect(
            db=settings.MONGO_DB_NAME,
            host=settings.MONGO_URL,
            serverSelectionTimeoutMS=5000
        )
        print("✓ MongoDB connection successful!")
        print(f"✓ Database: {settings.MONGO_DB_NAME}")
        
        # Check collections
        collections = ['users', 'campaigns', 'leads', 'embeddings']
        db = User._get_db()
        existing = db.list_collection_names()
        
        for collection in collections:
            status = "✓" if collection in existing else "✗"
            print(f"{status} Collection: {collection}")
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
    finally:
        disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("MongoDB Database Management Script")
        print("\nUsage: python manage_db.py <command>")
        print("\nCommands:")
        print("  init              Initialize MongoDB connection and indexes")
        print("  reset             Reset database (delete all collections)")
        print("  check             Check MongoDB connection")
        print("  create-admin      Create an admin user")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_db()
    elif command == "reset":
        reset_db()
    elif command == "check":
        check_db()
    elif command == "create-admin":
        if len(sys.argv) < 4:
            print("Usage: python manage_db.py create-admin <email> <password> <full_name>")
            print("Example: python manage_db.py create-admin admin@example.com password123 'Admin User'")
            sys.exit(1)
        
        email = sys.argv[2]
        password = sys.argv[3]
        full_name = sys.argv[4] if len(sys.argv) > 4 else email
        create_admin_user(email, password, full_name)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
