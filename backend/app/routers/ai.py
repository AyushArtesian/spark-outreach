"""
AI router for advanced AI operations
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Dict, Any, Optional

from app.models.user import User
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.services.ai_service import ai_service
from app.utils.auth import decode_token
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["ai"])

class RAGQuery(BaseModel):
    query: str
    campaign_id: str
    top_k: int = 3

class RAGResponse(BaseModel):
    results: List[Dict[str, Any]]

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

@router.post("/rag-search", response_model=RAGResponse)
async def rag_search(
    query: RAGQuery,
    authorization: Optional[str] = Header(None)
):
    """
    Perform a RAG (Retrieval-Augmented Generation) search
    Retrieves relevant campaign content based on a query
    """
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=query.campaign_id).first()
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    results = await ai_service.retrieve_relevant_context(
        query.query,
        query.campaign_id,
        top_k=query.top_k
    )
    
    return {"results": results}

@router.post("/generate-message")
async def generate_message(
    lead_id: str,
    campaign_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Generate a personalized outreach message for a lead
    """
    current_user = get_current_user_from_token(authorization)
    
    try:
        lead = Lead.objects(id=lead_id).first()
    except:
        lead = None
    
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except:
        campaign = None
    
    if not lead or not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead or campaign not found"
        )
    
    if str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    message = await ai_service.generate_lead_message(lead, campaign)
    
    return {
        "lead_id": lead_id,
        "campaign_id": campaign_id,
        "message": message
    }

@router.post("/create-embeddings")
async def create_embeddings(
    campaign_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Create or refresh embeddings for a campaign's content
    """
    current_user = get_current_user_from_token(authorization)
    
    campaign = Campaign.objects(id=campaign_id).first()
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    count = await ai_service.create_campaign_embeddings(campaign)
    
    return {
        "campaign_id": campaign_id,
        "embeddings_created": count,
        "message": f"Created {count} embeddings for campaign"
    }
