"""
Pydantic schemas for lead operations
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class LeadBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None

class LeadCreate(LeadBase):
    campaign_id: int
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

class LeadResponse(LeadBase):
    id: int
    campaign_id: int
    status: str
    relevance_score: Optional[float]
    message_sent: bool
    opened: bool
    clicked: bool
    replied: bool
    converted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LeadDetailResponse(LeadResponse):
    raw_data: Optional[Dict[str, Any]] = None
    enriched_data: Optional[Dict[str, Any]] = None
    ai_generated_message: Optional[str] = None
    ai_notes: Optional[str] = None
    contacted_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

class BulkLeadCreate(BaseModel):
    campaign_id: int
    leads: list[LeadCreate]
