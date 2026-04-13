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
    score = DictField()  # Structured score card (optional)
    enrichment = DictField()  # Structured enrichment payload (optional)
    emails = ListField(DictField(), default=list)  # Generated email history (optional)
    
    # AI/RAG Information
    embeddings = ListField(FloatField())  # Vector embeddings (stored as list of floats)
    relevance_score = FloatField()  # 0-1 relevance score to campaign
    lead_embedding = ListField(FloatField())  # Lead profile embedding (768-dim)
    company_fit_score = FloatField(default=0.0)  # 0-1 score: how well lead matches company profile
    signal_keywords = ListField(StringField())  # Detected hiring/funding/growth signals
    signal_score = FloatField(default=0.0)  # 0-1 strength of growth signals
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
        'indexes': ['campaign_id', 'email', 'status', 'created_at', 'company_fit_score']
    }
    
    def __repr__(self):
        return f"<Lead {self.email}>"
