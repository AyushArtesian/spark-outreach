"""
Pydantic schemas for campaign operations
"""
from pydantic import BaseModel, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class CampaignBase(BaseModel):
    title: str
    description: str
    content: str
    target_audience: str
    ai_model: str = "gpt-3.5-turbo"
    temperature: int = 7
    max_tokens: int = 500

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    target_audience: Optional[str] = None
    status: Optional[str] = None
    ai_model: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None
    custom_instructions: Optional[str] = None
    services: Optional[list[str]] = None  # For intent monitoring
    target_locations: Optional[list[str]] = None  # For intent monitoring

class CampaignResponse(CampaignBase):
    id: str
    owner_id: str
    status: str
    custom_instructions: Optional[str]
    max_leads: Optional[int]
    follow_up_enabled: bool
    follow_up_delay_hours: int
    services: list[str] = []
    target_locations: list[str] = []
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    @field_serializer('id', 'owner_id')
    def serialize_id(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    
    class Config:
        from_attributes = True

class CampaignDetailResponse(CampaignResponse):
    leads_count: Optional[int] = None
    converted_count: Optional[int] = None
