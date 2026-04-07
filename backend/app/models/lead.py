"""
Lead MongoDB model
"""
from mongoengine import Document, StringField, IntField, FloatField, BooleanField, DateTimeField, DictField, ListField
from datetime import datetime

class Lead(Document):
    campaign_id = StringField(required=True)
    
    # Lead Information
    name = StringField(required=True)
    email = StringField(required=True)
    company = StringField()
    phone = StringField()
    job_title = StringField()
    industry = StringField()
    
    # Lead Data
    raw_data = DictField()  # Original scraped/imported data
    enriched_data = DictField()  # Enriched lead information
    
    # AI/RAG Information
    embeddings = ListField(FloatField())  # Vector embeddings (stored as list of floats)
    relevance_score = FloatField()  # 0-1 relevance score
    ai_notes = StringField()  # AI-generated notes
    
    # Campaign Interaction
    status = StringField(default="new")  # new, contacted, replied, converted, rejected
    message_sent = BooleanField(default=False)
    message_content = StringField()
    ai_generated_message = StringField()
    
    # Engagement Metrics
    opened = BooleanField(default=False)
    clicked = BooleanField(default=False)
    replied = BooleanField(default=False)
    converted = BooleanField(default=False)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    contacted_at = DateTimeField()
    replied_at = DateTimeField()
    
    meta = {
        'collection': 'leads',
        'indexes': ['campaign_id', 'email', 'status', 'created_at']
    }
    
    def __repr__(self):
        return f"<Lead {self.email}>"
