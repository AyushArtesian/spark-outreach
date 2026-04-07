"""
User MongoDB model
"""
from mongoengine import Document, StringField, BooleanField, DateTimeField, ReferenceField
from datetime import datetime

class User(Document):
    email = StringField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    full_name = StringField(required=True)
    hashed_password = StringField(required=True)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'users',
        'indexes': ['email', 'username']
    }
    
    def __repr__(self):
        return f"<User {self.email}>"
