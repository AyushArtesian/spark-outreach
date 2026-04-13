"""
Pydantic schemas for lead operations
"""
from pydantic import BaseModel, EmailStr, field_serializer, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId


class LeadScore(BaseModel):
    total_score: int
    grade: Literal["A", "B", "C", "D"]
    breakdown: Dict[str, int]
    is_hot_lead: bool
    recommended_action: str


class LeadEnrichment(BaseModel):
    tech_stack: list[str] = Field(default_factory=list)
    uses_microsoft_stack: bool = False
    ecommerce_platform: Optional[str] = None
    decision_maker: Optional[Dict[str, Any]] = None
    recent_signals: list[str] = Field(default_factory=list)
    signal_strength: int = 0


class GeneratedEmail(BaseModel):
    subject: str
    body: str
    personalization_score: int
    generated_at: datetime
    email_type: Literal["cold", "followup1", "followup2", "linkedin"]

class LeadBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None

class LeadCreate(LeadBase):
    campaign_id: str
    raw_data: Optional[Dict[str, Any]] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    ai_notes: Optional[str] = None

class LeadResponse(BaseModel):
    id: str
    campaign_id: str
    name: str
    email: str  # Changed to str to allow sanitized/empty values
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    status: str
    relevance_score: Optional[float] = None
    company_fit_score: Optional[float] = 0.0
    signal_score: Optional[float] = 0.0
    signal_keywords: Optional[list[str]] = []
    message_sent: bool
    opened: bool
    clicked: bool
    replied: bool
    converted: bool
    score: Optional[LeadScore] = None
    enrichment: Optional[LeadEnrichment] = None
    emails: list[GeneratedEmail] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('id', 'campaign_id')
    def serialize_id(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    
    class Config:
        from_attributes = True

class LeadDetailResponse(LeadResponse):
    raw_data: Optional[Dict[str, Any]] = None
    enriched_data: Optional[Dict[str, Any]] = None
    company_fit_score: Optional[float] = 0.0
    signal_score: Optional[float] = 0.0
    signal_keywords: Optional[list[str]] = []
    reason: Optional[list[str]] = []
    score: Optional[LeadScore] = None
    ai_generated_message: Optional[str] = None
    ai_notes: Optional[str] = None
    contacted_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

class BulkLeadCreate(BaseModel):
    campaign_id: str
    leads: list[LeadCreate]
