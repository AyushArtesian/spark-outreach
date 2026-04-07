"""
Pydantic schemas for company profile operations
"""
from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# Project Schema
class ProjectRequest(BaseModel):
    title: str
    description: str
    industry: Optional[str] = None
    result: Optional[str] = None
    technologies: Optional[List[str]] = None

class ProjectResponse(ProjectRequest):
    id: Optional[str] = None

# ICP Schema
class IdealCustomerProfileRequest(BaseModel):
    company_sizes: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    growth_indicators: Optional[List[str]] = None
    hiring_signals: Optional[List[str]] = None
    funding_signals: Optional[List[str]] = None
    tech_stack_signals: Optional[List[str]] = None
    revenue_range: Optional[str] = None
    employee_count_range: Optional[str] = None

class IdealCustomerProfileResponse(IdealCustomerProfileRequest):
    pass

# Company Profile Schemas
class CompanyProfileCreateRequest(BaseModel):
    """Initial company setup request"""
    company_name: str
    company_size: Optional[str] = None
    company_stage: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    upwork_id: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_urls: Optional[List[str]] = None
    services: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    team_size: Optional[str] = None

class CompanyProfileUpdateRequest(BaseModel):
    """Update company profile"""
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    company_stage: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    upwork_id: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_urls: Optional[List[str]] = None
    services: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    team_size: Optional[str] = None
    team_expertise: Optional[List[str]] = None
    projects: Optional[List[ProjectRequest]] = None
    min_deal_size: Optional[str] = None
    max_deal_size: Optional[str] = None
    preferred_company_stages: Optional[List[str]] = None

class CompanyProfileResponse(BaseModel):
    """Company profile response"""
    id: str
    owner_id: str
    company_name: str
    company_size: Optional[str] = None
    company_stage: Optional[str] = None
    company_description: Optional[str] = None
    company_narrative: Optional[str] = None
    services: List[str] = []
    expertise_areas: List[str] = []
    technologies: List[str] = []
    target_industries: List[str] = []
    target_locations: List[str] = []
    team_size: Optional[str] = None
    team_expertise: List[str] = []
    projects: List[ProjectResponse] = []
    icp: Optional[dict] = None
    ideal_customer_profile: Optional[dict] = None
    avoid_patterns: List[str] = []
    hiring_signal_keywords: List[str] = []
    funding_signal_keywords: List[str] = []
    tech_signal_keywords: List[str] = []
    min_deal_size: Optional[str] = None
    max_deal_size: Optional[str] = None
    preferred_company_stages: List[str] = []
    is_complete: bool = False
    setup_step: str = "basic_info"
    created_at: datetime
    updated_at: datetime
    last_embedding_update: Optional[datetime] = None
    
    @field_serializer('id', 'owner_id')
    def serialize_id(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    
    class Config:
        from_attributes = True

class CompanySetupStepRequest(BaseModel):
    """Request for specific setup step"""
    step: str  # "basic_info", "services", "projects", "target_market", "review"
    data: dict
