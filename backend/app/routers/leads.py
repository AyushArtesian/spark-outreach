"""
Leads router
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Optional, Dict, Any

from app.models.lead import Lead
from app.models.user import User
from app.models.campaign import Campaign
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadDetailResponse, BulkLeadCreate
from app.services.lead_service import lead_service
from app.services.ai_service import ai_service
from app.utils.auth import decode_token
from app.utils.response import serialize_lead
from pydantic import BaseModel, Field

router = APIRouter(prefix="/leads", tags=["leads"])

# Request/Response models for search
class LeadSearchRequest(BaseModel):
    query: str
    campaign_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 20
    sort_by: str = "combined"  # combined, fit_score, signal_score, created_at

class LeadSearchResult(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str]
    job_title: Optional[str]
    industry: Optional[str]
    source_url: Optional[str] = None
    company_summary: Optional[str] = None
    score: float = 0.0
    signals: List[str] = Field(default_factory=list)
    reason: List[str] = Field(default_factory=list)
    company_fit_score: float
    signal_score: float
    signal_keywords: List[str]
    status: str
    created_at: str

# Helper to get current user from JWT token
def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> User:
    """Extract current user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = User.objects(email=token_data["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/search", response_model=List[LeadSearchResult])
async def search_leads(
    search_request: LeadSearchRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Search leads using company fit scoring, growth signals, and query relevance
    
    Query examples:
    - "Find companies hiring in tech that need .NET development"
    - "Find SaaS companies in Series A funding stage"
    - "Find eCommerce companies using outdated tech"
    
    sort_by options:
    - combined: (50% company fit + 30% signals + 20% query match)
    - fit_score: company profile alignment
    - signal_score: hiring/funding/growth signals
    - created_at: newest leads first
    """
    current_user = get_current_user_from_token(authorization)
    
    try:
        # Search leads using company fit and signals
        results = await lead_service.search_leads_by_company_fit(
            owner_id=str(current_user.id),
            query=search_request.query,
            campaign_id=search_request.campaign_id,
            filters=search_request.filters,
            top_k=search_request.top_k,
            sort_by=search_request.sort_by
        )
        
        # Format results
        search_results = []
        for lead in results:
            lead_raw = lead.raw_data or {}
            signals = lead_raw.get("discovery_signals") or lead.signal_keywords or []
            score_10 = round(float(lead_raw.get("final_score", 0.0) or 0.0) * 10.0, 2)
            search_results.append(LeadSearchResult(
                id=str(lead.id),
                name=lead.name,
                email=lead.email,
                phone=lead.phone,
                company=lead.company,
                job_title=lead.job_title,
                industry=lead.industry,
                source_url=lead_raw.get("source_url") or lead_raw.get("company_website"),
                company_summary=lead_raw.get("company_summary"),
                score=score_10,
                signals=signals,
                reason=lead_raw.get("final_reason", []),
                company_fit_score=lead.company_fit_score or 0.0,
                signal_score=lead.signal_score or 0.0,
                signal_keywords=lead.signal_keywords or [],
                status=lead.status,
                created_at=lead.created_at.isoformat() if lead.created_at else ""
            ))
        
        return search_results
    except Exception as e:
        print(f"Error searching leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search leads: {str(e)}"
        )

@router.post("", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new lead"""
    from app.models.company import CompanyProfile
    
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    db_lead = lead_service.create_lead(lead)
    
    # Enrich lead with embeddings and signals
    company_profile = CompanyProfile.objects(owner_id=current_user.id).first()
    if company_profile:
        db_lead = await lead_service.enrich_lead_profile(db_lead, company_profile)
    
    # Calculate relevance score
    relevance_score = await ai_service.analyze_lead_relevance(db_lead, campaign)
    db_lead.relevance_score = relevance_score
    db_lead.save()
    
    return serialize_lead(db_lead)

@router.post("/bulk", response_model=List[LeadResponse])
async def create_bulk_leads(
    bulk_leads: BulkLeadCreate,
    authorization: Optional[str] = Header(None)
):
    """Create multiple leads at once"""
    from app.models.company import CompanyProfile
    
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=bulk_leads.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    db_leads = lead_service.create_bulk_leads(bulk_leads.leads)
    
    # Get company profile for enrichment
    company_profile = CompanyProfile.objects(owner_id=current_user.id).first()
    
    # Enrich and score all leads
    for db_lead in db_leads:
        # Enrich lead with embeddings and signals
        if company_profile:
            db_lead = await lead_service.enrich_lead_profile(db_lead, company_profile)
        
        # Calculate relevance score
        relevance_score = await ai_service.analyze_lead_relevance(db_lead, campaign)
        db_lead.relevance_score = relevance_score
        db_lead.save()
    
    return [serialize_lead(lead) for lead in db_leads]

@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(
    lead_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get a specific lead"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        lead = Lead.objects(id=lead_id).first()
    except:
        lead = None
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this lead"
        )
    
    return serialize_lead(lead)

@router.get("/campaign/{campaign_id}", response_model=List[LeadResponse])
async def get_campaign_leads(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    authorization: Optional[str] = Header(None)
):
    """Get all leads for a campaign"""
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=campaign_id).first()
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if status:
        leads = lead_service.get_leads_by_status(campaign_id, status)
    else:
        leads = lead_service.get_campaign_leads(campaign_id, skip, limit)
    
    return [serialize_lead(l) for l in leads]

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    authorization: Optional[str] = Header(None)
):
    """Update a lead"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        lead = Lead.objects(id=lead_id).first()
    except:
        lead = None
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this lead"
        )
    
    updated_lead = lead_service.update_lead(lead_id, lead_update)
    return serialize_lead(updated_lead)

@router.post("/{lead_id}/contact", response_model=LeadResponse)
async def contact_lead(
    lead_id: str,
    authorization: Optional[str] = Header(None)
):
    """Mark a lead as contacted and generate message"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        lead = Lead.objects(id=lead_id).first()
    except:
        lead = None
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Generate personalized message
    message = await ai_service.generate_lead_message(lead, campaign)
    lead.ai_generated_message = message
    
    # Mark as contacted
    updated_lead = lead_service.mark_as_contacted(lead_id)
    return serialize_lead(updated_lead)

@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a lead"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        lead = Lead.objects(id=lead_id).first()
    except:
        lead = None
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    lead_service.delete_lead(lead_id)
    return {"detail": "Lead deleted successfully"}
