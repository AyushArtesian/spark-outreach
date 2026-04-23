"""
AI router for advanced AI operations
"""
import re
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

@router.post("/insights")
async def generate_insights(
    authorization: Optional[str] = Header(None)
):
    """
    Generate AI insights from all leads using Groq Qwen model
    Provides actionable recommendations based on lead data
    """
    from app.services.llm_provider import groq_provider
    from app.config import settings
    
    current_user = get_current_user_from_token(authorization)
    
    # Fetch user's campaigns
    campaigns = list(Campaign.objects(owner_id=current_user.id))
    campaign_ids = [str(c.id) for c in campaigns]
    
    print(f"[AI INSIGHTS] User: {current_user.email}, Campaigns: {len(campaigns)}, Campaign IDs: {campaign_ids}")
    
    # Fetch leads - try both by campaign and all leads if no campaigns
    if campaign_ids:
        leads = list(Lead.objects(campaign_id__in=campaign_ids))
    else:
        # Fallback: get all leads if no campaigns
        leads = list(Lead.objects())
    
    print(f"[AI INSIGHTS] Found {len(leads)} leads")
    
    if not leads:
        return {
            "insights": "No lead data available yet. Start a lead search to generate insights.",
            "recommendations": [],
            "metrics": {
                "total_leads": 0,
                "hot_leads": 0,
                "conversion_rate": 0,
            }
        }
    
    # Calculate metrics
    hot_count = 0
    for lead in leads:
        if lead.score and isinstance(lead.score, dict):
            if lead.score.get("is_hot_lead"):
                hot_count += 1
        elif hasattr(lead, 'score') and hasattr(lead.score, 'get'):
            if lead.score.get("is_hot_lead"):
                hot_count += 1
    
    contacted = 0
    for lead in leads:
        if lead.message_sent or (lead.status and lead.status in ["contacted", "replied", "converted"]):
            contacted += 1
    
    converted = 0
    for lead in leads:
        if lead.converted or (lead.status and lead.status == "converted"):
            converted += 1
    
    conversion_rate = (converted / contacted * 100) if contacted > 0 else 0
    
    # Group by industry
    industries = {}
    for lead in leads:
        ind = lead.industry or "Unknown"
        industries[ind] = industries.get(ind, 0) + 1
    
    top_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Group by status
    statuses = {}
    for lead in leads:
        status = lead.status or "new"
        statuses[status] = statuses.get(status, 0) + 1
    
    print(f"[AI INSIGHTS] Hot: {hot_count}, Contacted: {contacted}, Converted: {converted}")
    
    # Generate insights using Groq Qwen
    if not groq_provider.client:
        print("[AI INSIGHTS] Groq client not configured")
        return {
            "insights": "AI provider not configured. Please add GROQ_API_KEY to generate insights.",
            "recommendations": [],
            "metrics": {
                "total_leads": len(leads),
                "hot_leads": hot_count,
                "conversion_rate": conversion_rate,
            }
        }
    
    summary = f"""Lead Intelligence Summary:
- Total Leads: {len(leads)}
- Hot Leads: {hot_count}
- Conversion Rate: {conversion_rate:.1f}%
- Top Industries: {', '.join([f"{ind} ({count})" for ind, count in top_industries])}
- Lead Status Distribution: {', '.join([f"{s}: {c}" for s, c in statuses.items()])}"""
    
    prompt = f"""Based on this lead data summary, provide actionable AI insights and recommendations:

{summary}

Please provide:
1. Key insights about the current lead quality and conversion patterns
2. 3-5 specific recommendations to improve lead quality and conversion rate
3. Industry trends and opportunities
4. Next steps for the user

Keep insights practical and actionable."""
    
    try:
        print("[AI INSIGHTS] Calling Groq API...")
        insights_text = await groq_provider.call_chat_completion(
            system_prompt="You are an expert sales intelligence analyst. Provide data-driven insights and recommendations.",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1500,
        )
        print(f"[AI INSIGHTS] Got response: {len(insights_text)} chars")
    except Exception as e:
        print(f"[AI INSIGHTS] Groq error: {str(e)}")
        insights_text = f"Could not generate insights: {str(e)}"
    
    # Clean up response - remove <think> tags and thinking process
    import re
    insights_text = re.sub(r'<think>.*?</think>', '', insights_text, flags=re.DOTALL)
    insights_text = insights_text.strip()
    
    # Remove leading thinking artifacts
    if insights_text.startswith("Okay"):
        # Find where actual content starts (after thinking)
        lines = insights_text.split('\n')
        clean_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith(('###', '#', '**', '1.', '2.', '3.', '-', '•', 'Key', 'Recommendation', 'Industry')):
                clean_lines = lines[i:]
                break
        if clean_lines:
            insights_text = '\n'.join(clean_lines).strip()
    
    # Parse recommendations more carefully
    recommendations = []
    lines = insights_text.split("\n")
    in_recommendations = False
    
    for i, line in enumerate(lines):
        lower = line.lower()
        
        # Look for recommendations section
        if "recommendation" in lower and (":" in line or i < len(lines) - 1):
            in_recommendations = True
            continue
        
        # Stop when hitting another major section
        if in_recommendations and any(x in lower for x in ["industry trend", "next step", "final note"]):
            in_recommendations = False
        
        # Extract recommendation lines
        if in_recommendations and line.strip():
            # Match numbered or bulleted items
            match = re.match(r'^[\s]*[\d\.\-•*]+\s*\.?\s*(.+)', line)
            if match:
                rec_text = match.group(1).strip()
                # Skip if it's a subsection header
                if not rec_text.endswith(":") and len(rec_text) > 15:
                    recommendations.append(rec_text)
    
    recommendations = recommendations[:5]
    
    return {
        "insights": insights_text,
        "recommendations": recommendations,
        "metrics": {
            "total_leads": len(leads),
            "hot_leads": hot_count,
            "conversion_rate": round(conversion_rate, 2),
            "contacted": contacted,
            "converted": converted,
            "top_industries": [{"name": ind, "count": count} for ind, count in top_industries],
        },
        "model": settings.GROQ_MODEL,
    }
