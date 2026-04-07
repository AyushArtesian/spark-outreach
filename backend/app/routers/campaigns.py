"""
Campaigns router
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Optional

from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse, CampaignDetailResponse
from app.services.campaign_service import campaign_service
from app.services.ai_service import ai_service
from app.utils.auth import decode_token

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

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

@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new campaign"""
    current_user = get_current_user_from_token(authorization)
    
    db_campaign = campaign_service.create_campaign(campaign, str(current_user.id))
    
    # Create embeddings for the campaign content
    await ai_service.create_campaign_embeddings(db_campaign)
    
    return db_campaign

@router.get("", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 10,
    authorization: Optional[str] = Header(None)
):
    """Get all campaigns for current user"""
    current_user = get_current_user_from_token(authorization)
    
    campaigns = campaign_service.get_user_campaigns(str(current_user.id), skip, limit)
    return campaigns

@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get a specific campaign"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except:
        campaign = None
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_update: CampaignUpdate,
    authorization: Optional[str] = Header(None)
):
    """Update a campaign"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except:
        campaign = None
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    updated_campaign = campaign_service.update_campaign(campaign_id, campaign_update)
    return updated_campaign

@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: str,
    authorization: Optional[str] = Header(None)
):
    """Start a campaign"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except:
        campaign = None
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    started_campaign = campaign_service.start_campaign(campaign_id)
    return started_campaign

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a campaign"""
    current_user = get_current_user_from_token(authorization)
    
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except:
        campaign = None
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    campaign_service.delete_campaign(campaign_id)
    return {"detail": "Campaign deleted successfully"}

