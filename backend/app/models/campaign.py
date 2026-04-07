"""
Campaign MongoDB model
"""
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ReferenceField, DictField, ListField
from datetime import datetime

class Campaign(Document):
    owner_id = StringField(required=True)  # Reference to User ID
    title = StringField(required=True)
    description = StringField()
    content = StringField()
    target_audience = StringField()
    status = StringField(default="draft")  # draft, active, paused, completed
    
    # AI/LLM Configuration
    ai_model = StringField(default="gemini-1.5-flash")
    temperature = IntField(default=7)  # 0-10
    max_tokens = IntField(default=500)
    custom_instructions = StringField()
    
    # Campaign Settings
    max_leads = IntField()
    follow_up_enabled = BooleanField(default=True)
    follow_up_delay_hours = IntField(default=24)
    
    # Campaign Metadata
    campaign_metadata = DictField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    started_at = DateTimeField()
    completed_at = DateTimeField()
    
    meta = {
        'collection': 'campaigns',
        'indexes': ['owner_id', 'status', 'created_at']
    }
    
    def __repr__(self):
        return f"<Campaign {self.title}>"
