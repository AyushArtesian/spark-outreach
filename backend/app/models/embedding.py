"""
Embedding storage model for RAG system using MongoDB
"""
from mongoengine import Document, StringField, ListField, FloatField, IntField, DateTimeField, DictField
from datetime import datetime

class Embedding(Document):
    lead_id = StringField()
    campaign_id = StringField()
    
    # Embedding Data
    content = StringField(required=True)  # Original text content
    embedding_vector = ListField(FloatField())  # Vector embedding (list of floats) - PERFECT FOR MONGODB
    embedding_model = StringField(default="gemini-embedding-001")
    
    # Metadata
    chunk_index = IntField(default=0)
    embedding_metadata = DictField()  # Additional context/metadata
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'embeddings',
        'indexes': ['campaign_id', 'lead_id', 'created_at']
    }
    
    def __repr__(self):
        return f"<Embedding {self.id}>"
