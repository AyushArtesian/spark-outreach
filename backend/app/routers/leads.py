"""
Leads router
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Optional

from app.models.lead import Lead
from app.models.user import User
from app.models.campaign import Campaign
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadDetailResponse, BulkLeadCreate
from app.services.lead_service import lead_service
from app.services.ai_service import ai_service
from app.utils.auth import decode_token

router = APIRouter(prefix="/leads", tags=["leads"])

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

@router.post("", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new lead"""
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=lead.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    db_lead = lead_service.create_lead(lead)
    
    # Calculate relevance score
    relevance_score = await ai_service.analyze_lead_relevance(db_lead, campaign)
    db_lead.relevance_score = relevance_score
    db_lead.save()
    
    return db_lead

@router.post("/bulk", response_model=List[LeadResponse])
async def create_bulk_leads(
    bulk_leads: BulkLeadCreate,
    authorization: Optional[str] = Header(None)
):
    """Create multiple leads at once"""
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=bulk_leads.campaign_id).first()
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    db_leads = lead_service.create_bulk_leads(bulk_leads.leads)
    
    # Calculate relevance scores for all leads
    for db_lead in db_leads:
        relevance_score = await ai_service.analyze_lead_relevance(db_lead, campaign)
        db_lead.relevance_score = relevance_score
        db_lead.save()
    
    return db_leads

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
    
    return lead

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
    
    return leads

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
    return updated_lead

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
    return updated_lead

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
