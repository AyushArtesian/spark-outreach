"""
Intent Monitoring Models for MongoDB
Tracks job board signals, hiring intent, and auto-discovery scanning
"""
from mongoengine import (
    Document, StringField, ListField, DictField, FloatField, 
    DateTimeField, BooleanField, ObjectIdField, IntField, EmbeddedDocument, 
    EmbeddedDocumentField, EmbeddedDocumentListField
)
from datetime import datetime, timedelta
from typing import Optional
import uuid


class IntentSignalDetail(EmbeddedDocument):
    """Embedded document for signal details"""
    posting_url = StringField()
    posting_title = StringField()
    posting_count = IntField(default=0)
    salary_range = StringField()
    required_skills = ListField(StringField())
    job_description = StringField()
    location = StringField()
    
    meta = {
        'allow_inheritance': False
    }


class IntentSignal(Document):
    """
    Tracks detected buyer intent signals from companies seeking our services
    Auto-expires every 30 days for freshness
    """
    # Tracking
    campaign_id = ObjectIdField(required=True)
    company_id = StringField()  # Company name seeking our services
    company_url = StringField()  # Company website URL if detected
    
    # Signal Classification
    signal_type = StringField(
        required=True,
        choices=['seeking_partner', 'hiring_technical', 'rfp_posted', 'digital_transformation', 'funding', 'expansion']
    )
    strength = FloatField(default=0.5, min_value=0.0, max_value=1.0)  # 0-1 buyer intent confidence
    details = EmbeddedDocumentField(IntentSignalDetail)
    
    # Source & Timing
    source = StringField(
        required=True,
        choices=['linkedin_jobs', 'indeed', 'angellist', 'crunchbase', 'web']
    )
    detected_at = DateTimeField(default=datetime.utcnow)
    
    # TTL (auto-expire after 30 days)
    # Note: TTL indexes must be created manually via MongoDB:
    # db.intent_signals.createIndex({'detected_at': 1}, {expireAfterSeconds: 2592000})
    meta = {
        'collection': 'intent_signals',
        'indexes': [
            'campaign_id',
            'company_id',
            'signal_type',
            'source',
            'detected_at'
        ]
    }
    
    def __str__(self):
        return f"{self.signal_type} ({self.strength:.2f}) - {self.company_id}"


class IntentScanSnapshot(EmbeddedDocument):
    """Embedded document for scan results"""
    companies_scanned = IntField(default=0)
    companies_found = IntField(default=0)
    leads_created = IntField(default=0)
    leads_updated = IntField(default=0)
    signals_detected = IntField(default=0)
    
    meta = {
        'allow_inheritance': False
    }


class IntentScan(Document):
    """
    Audit log for intent monitoring scans
    Tracks what happened during each scan run
    Auto-expires after 7 days
    """
    # Identification
    scan_id = StringField(required=True, unique=True, default=lambda: str(uuid.uuid4()))
    owner_id = ObjectIdField(required=True)
    
    # Scope
    campaign_ids = ListField(ObjectIdField())
    
    # Status
    status = StringField(
        required=True,
        default='queued',
        choices=['queued', 'running', 'completed', 'failed']
    )
    progress = IntField(default=0, min_value=0, max_value=100)
    
    # Results
    results = EmbeddedDocumentField(IntentScanSnapshot)
    
    # Errors
    errors = ListField(StringField())
    error_count = IntField(default=0)
    
    # Timing
    started_at = DateTimeField()
    completed_at = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    
    # TTL (auto-expire after 7 days)
    # Note: TTL indexes must be created manually via MongoDB:
    # db.intent_scans.createIndex({'created_at': 1}, {expireAfterSeconds: 604800})
    meta = {
        'collection': 'intent_scans',
        'indexes': [
            'scan_id',
            'owner_id',
            'status',
            'campaign_ids',
            'created_at'
        ]
    }
    
    def __str__(self):
        return f"Scan {self.scan_id[:8]}: {self.status} ({self.progress}%)"


class IntentMonitorSchedule(Document):
    """
    Configuration for recurring intent scans
    Defines when and how often to scan for each campaign
    """
    # Owner & Scope
    owner_id = ObjectIdField(required=True)
    campaign_ids = ListField(ObjectIdField())
    
    # Schedule Config
    frequency = StringField(
        required=True,
        default='daily',
        choices=['hourly', 'daily', 'weekly', 'monthly']
    )
    scheduled_time = StringField(default='02:00')  # HH:MM UTC
    enabled = BooleanField(default=True)
    
    # Scheduling Metadata
    last_run = DateTimeField()
    next_run = DateTimeField()
    error_count = IntField(default=0)
    consecutive_failures = IntField(default=0)
    
    # Options
    auto_create_leads = BooleanField(default=True)
    intent_threshold = FloatField(default=0.60, min_value=0.0, max_value=1.0)  # Min score to create lead
    job_boards = ListField(StringField(), default=['linkedin_jobs', 'indeed', 'angellist'])
    
    # Tracking
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'intent_monitor_schedules',
        'indexes': [
            'owner_id',
            'enabled',
            'frequency',
            'next_run',
            'campaign_ids'
        ]
    }
    
    def __str__(self):
        return f"Schedule {self.id}: {self.frequency} @ {self.scheduled_time}"


class LinkedInConnection(Document):
    """
    Tracks LinkedIn connection requests and conversations
    Links leads to LinkedIn outreach activities
    """
    # Reference
    lead_id = ObjectIdField(required=True)
    campaign_id = ObjectIdField(required=True)
    owner_id = ObjectIdField(required=True)
    
    # Profile
    profile_url = StringField(required=True)  # LinkedIn profile URL
    profile_name = StringField()
    profile_title = StringField()
    company_name = StringField()
    
    # Connection Status
    connection_status = StringField(
        default='pending',
        choices=['pending', 'connected', 'declined', 'cancelled', 'not_contacted']
    )
    
    # Messages
    request_message = StringField()  # Connection request note
    request_sent_at = DateTimeField()
    accepted_at = DateTimeField()
    declined_at = DateTimeField()
    
    # Engagement
    last_message_date = DateTimeField()
    last_activity = DateTimeField()
    message_count = IntField(default=0)
    reply_count = IntField(default=0)
    
    # Metadata
    connection_strength = StringField(default='secondary')  # primary, secondary, third+
    is_automation = BooleanField(default=True)
    
    # Timing
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'linkedin_connections',
        'indexes': [
            'campaign_id',
            'lead_id',
            'connection_status',
            'owner_id',
            'profile_url'
        ]
    }


class LinkedInMessage(Document):
    """
    Stores LinkedIn messages (connection requests, replies, follow-ups)
    Tracks conversation history
    """
    # Reference
    connection_id = ObjectIdField(required=True)
    lead_id = ObjectIdField(required=True)
    campaign_id = ObjectIdField(required=True)
    owner_id = ObjectIdField(required=True)
    
    # Message Content
    text = StringField(required=True)
    message_type = StringField(
        required=True,
        choices=['connection_request', 'message', 'followup', 'reply']
    )
    
    # Direction
    direction = StringField(
        required=True,
        choices=['outbound', 'inbound']
    )
    
    # Status
    status = StringField(
        default='sent',
        choices=['sent', 'failed', 'read', 'replied']
    )
    
    # Timing
    sent_at = DateTimeField(default=datetime.utcnow)
    read_at = DateTimeField()
    replied_at = DateTimeField()
    
    # Template Reference
    template_id = StringField()  # If generated from template
    template_name = StringField()
    
    # Sequence Info
    sequence_day = IntField()  # What day of sequence (0=connect, 7=first message, etc)
    
    meta = {
        'collection': 'linkedin_messages',
        'indexes': [
            'connection_id',
            'lead_id',
            'campaign_id',
            'direction',
            'status',
            'sent_at'
        ]
    }


class LinkedInSequence(Document):
    """
    Orchestrates multi-step LinkedIn outreach sequences
    Manages enrollment, timing, and automation across multiple leads
    """
    # Reference
    campaign_id = ObjectIdField(required=True)
    owner_id = ObjectIdField(required=True)
    
    # Sequence Config
    template_set = StringField(
        default='standard',
        choices=['standard', 'aggressive', 'consultative', 'value_first']
    )
    daily_limit = IntField(default=50)  # Max connections per day
    
    # Status
    status = StringField(
        default='active',
        choices=['active', 'paused', 'completed', 'archived']
    )
    
    # Enrollment
    lead_count = IntField(default=0)
    leads_enrolled = ListField(ObjectIdField())  # Lead IDs in sequence
    
    # Progress
    connections_sent = IntField(default=0)
    connections_accepted = IntField(default=0)
    messages_sent = IntField(default=0)
    replies_received = IntField(default=0)
    
    # Timing
    created_at = DateTimeField(default=datetime.utcnow)
    started_at = DateTimeField()
    completed_at = DateTimeField()
    
    meta = {
        'collection': 'linkedin_sequences',
        'indexes': [
            'campaign_id',
            'owner_id',
            'status',
            'created_at'
        ]
    }
