"""
Company Profile Model for MongoDB
Stores company context, expertise, and embeddings for intelligent lead matching
"""
from mongoengine import Document, StringField, ListField, DictField, FloatField, DateTimeField, BooleanField, ObjectIdField
from datetime import datetime
from typing import Optional

class Project(Document):
    """Nested document for company projects/portfolio"""
    title = StringField(required=True)
    description = StringField(required=True)
    industry = StringField()
    result = StringField()
    technologies = ListField(StringField())
    embeddings = ListField(FloatField())  # Vector embeddings for semantic search
    
    meta = {
        'indexes': [
            'title',
            'industry'
        ]
    }

class IdealCustomerProfile(Document):
    """Nested document for ICP generated from company context"""
    company_sizes = ListField(StringField())  # e.g., ["startup", "growth", "enterprise"]
    industries = ListField(StringField())
    growth_indicators = ListField(StringField())  # e.g., ["hiring", "funding", "expansion"]
    hiring_signals = ListField(StringField())  # Signals to look for
    funding_signals = ListField(StringField())
    tech_stack_signals = ListField(StringField())
    revenue_range = StringField()  # e.g., "1M-10M"
    employee_count_range = StringField()
    
    meta = {
        'indexes': [
            'industries',
            'company_sizes'
        ]
    }

class CompanyProfile(Document):
    """
    Main company profile document
    Stores all company context and AI-generated intelligence for lead matching
    """
    # User/Owner Info
    owner_id = ObjectIdField(required=True)
    
    # Basic Company Info
    company_name = StringField(required=True)
    company_description = StringField()
    company_size = StringField()  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    company_stage = StringField()  # "early-stage", "growth", "mature", "enterprise"
    
    # Expertise & Services
    services = ListField(StringField())  # e.g., ["Web Development", "Mobile App", "AI/ML"]
    expertise_areas = ListField(StringField())  # Detailed expertise
    technologies = ListField(StringField())  # Tech stack
    target_industries = ListField(StringField())  # Industries they serve
    target_locations = ListField(StringField())  # Geographic focus
    
    # Team Information
    team_size = StringField()
    team_expertise = ListField(StringField())  # ["Backend", "Frontend", "DevOps", etc]
    
    # Projects/Portfolio
    projects = ListField(DictField())  # List of project dicts
    
    # External Links & Portfolios
    company_website = StringField()  # Main website URL
    upwork_id = StringField()  # Upwork profile ID
    github_url = StringField()  # GitHub profile URL
    linkedin_url = StringField()  # LinkedIn company URL
    portfolio_urls = ListField(StringField())  # Other portfolio/portfolio links
    fetched_website_content = StringField()  # Cached content from website scrape
    portfolio_content = DictField()  # Cached content from external portfolios
    
    # AI-Generated Intelligence
    company_narrative = StringField()  # Generated summary of company
    company_embeddings = ListField(FloatField())  # Vector embedding of company profile
    
    # Generated ICP (Ideal Customer Profile)
    icp = DictField()  # Serialized ICP document
    ideal_customer_profile = DictField()  # Alternative structure
    avoid_patterns = ListField(StringField())  # What to avoid
    
    # Signals Configuration
    hiring_signal_keywords = ListField(StringField())
    funding_signal_keywords = ListField(StringField())
    tech_signal_keywords = ListField(StringField())
    
    # Preferences
    min_deal_size = StringField()
    max_deal_size = StringField()
    preferred_company_stages = ListField(StringField())
    
    # Setup Progress
    is_complete = BooleanField(default=False)
    setup_step = StringField(default="basic_info")  # Track which step they're on
    
    # Metadata
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    last_embedding_update = DateTimeField()
    
    meta = {
        'collection': 'company_profiles',
        'indexes': [
            'owner_id',
            'company_name',
            'target_industries',
            'target_locations',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
