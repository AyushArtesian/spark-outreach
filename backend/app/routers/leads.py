"""
Leads router
"""
from fastapi import APIRouter, HTTPException, status, Header, BackgroundTasks, Body
from typing import List, Optional, Dict, Any
import logging

from app.models.lead import Lead
from app.models.user import User
from app.models.campaign import Campaign
from app.models.intent import IntentSignal
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadDetailResponse,
    BulkLeadCreate,
    LeadScore,
    LeadEnrichment,
    GeneratedEmail,
)
from app.services.lead_service import lead_service
from app.services.ai_service import ai_service
from app.utils.auth import decode_token
from app.utils.response import serialize_lead
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

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
    source: Optional[str] = None
    detected_location: Optional[str] = None
    score: float = 0.0
    signals: List[str] = Field(default_factory=list)
    reason: List[str] = Field(default_factory=list)
    company_fit_score: float
    signal_score: float
    signal_keywords: List[str]
    status: str
    created_at: str


class IntentScanStartResponse(BaseModel):
    scan_id: str
    status: str
    message: str


class IntentScanStatusResponse(BaseModel):
    last_scan: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    status: str
    scan_id: Optional[str] = None


class IntentScanRequest(BaseModel):
    campaign_ids: Optional[List[str]] = None
    services: Optional[List[str]] = None
    locations: Optional[List[str]] = None


def _get_company_profile_for_user(user_id: str):
    from app.models.company import CompanyProfile

    profile = None
    try:
        profile = CompanyProfile.objects(owner_id=ObjectId(str(user_id))).first()
    except Exception:
        profile = None

    if not profile:
        try:
            profile = CompanyProfile.objects(owner_id=str(user_id)).first()
        except Exception:
            profile = None

    return profile


def _get_owned_lead_or_404(lead_id: str, current_user: User) -> Lead:
    try:
        lead = Lead.objects(id=lead_id).first()
    except Exception:
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

    return lead

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
                source=lead_raw.get("source"),
                detected_location=lead_raw.get("detected_location") or lead_raw.get("location"),
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


@router.post("/run-intent-scan", response_model=IntentScanStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_intent_scan(
    scan_request: Optional[IntentScanRequest] = Body(None),
    background_tasks: BackgroundTasks = None,
    authorization: Optional[str] = Header(None),
):
    """Trigger intent monitor scan in the background for current user."""
    from app.services.intent_monitor import intent_monitor_service

    current_user = get_current_user_from_token(authorization)
    
    # Get campaign_ids from request body
    campaign_ids = None
    if scan_request and scan_request.campaign_ids:
        campaign_ids = scan_request.campaign_ids
    
    # If no campaign_ids provided, get all active campaigns for the user
    if not campaign_ids:
        user_campaigns = Campaign.objects(owner_id=str(current_user.id), status='active')
        campaign_ids = [str(c.id) for c in user_campaigns]
    
    if not campaign_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active campaigns found. Please create and activate a campaign first."
        )
    
    logger.info(f"[SCAN] Starting scan for user {current_user.id} with campaigns: {campaign_ids}")
    
    scan_id, already_running = await intent_monitor_service.start_scan(
        str(current_user.id), 
        campaign_ids=campaign_ids
    )
    if not already_running:
        background_tasks.add_task(intent_monitor_service.execute_scan, str(current_user.id), scan_id)

    return IntentScanStartResponse(
        scan_id=scan_id,
        status="running",
        message="Intent scan already running" if already_running else "Intent scan started",
    )


@router.get("/scan-status", response_model=IntentScanStatusResponse)
async def get_intent_scan_status(
    authorization: Optional[str] = Header(None),
):
    """Get latest intent scan state for current user."""
    from app.services.intent_monitor import intent_monitor_service

    current_user = get_current_user_from_token(authorization)
    payload = await intent_monitor_service.get_scan_status(str(current_user.id))

    last_scan_raw = payload.get("last_scan")
    if hasattr(last_scan_raw, "isoformat"):
        last_scan = last_scan_raw.isoformat()
    else:
        last_scan = str(last_scan_raw) if last_scan_raw else None

    return IntentScanStatusResponse(
        last_scan=last_scan,
        summary=payload.get("summary") or {},
        status=str(payload.get("status") or "idle"),
        scan_id=str(payload.get("scan_id") or "") or None,
    )


@router.get("/intent-signals", response_model=List[Dict[str, Any]])
async def get_intent_signals(
    campaign_id: str,
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """Get detected intent signals for a campaign."""
    current_user = get_current_user_from_token(authorization)
    
    # Verify user owns the campaign
    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except Exception:
        campaign = None
    
    if not campaign or str(campaign.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )
    
    # Get intent signals for this campaign, ordered by newest first
    try:
        campaign_oid = ObjectId(campaign_id)
        signals = IntentSignal.objects(campaign_id=campaign_oid).limit(limit).order_by('-detected_at')
        
        # Serialize signals
        result = []
        for signal in signals:
            signal_dict = {
                'id': str(signal.id),
                'signal_type': signal.signal_type,
                'strength': signal.strength,
                'company_id': signal.company_id,
                'company_url': signal.company_url,
                'source': signal.source,
                'detected_at': signal.detected_at.isoformat() if signal.detected_at else None,
            }
            
            # Include details if present
            if signal.details:
                signal_dict['details'] = {
                    'posting_url': signal.details.posting_url,
                    'posting_title': signal.details.posting_title,
                    'posting_count': signal.details.posting_count,
                    'salary_range': signal.details.salary_range,
                    'required_skills': signal.details.required_skills,
                    'job_description': signal.details.job_description,
                    'location': signal.details.location,
                }
            
            result.append(signal_dict)
        
        return result
    except Exception as e:
        print(f"Error getting intent signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signals: {str(e)}"
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

@router.get("/all", response_model=List[LeadResponse])
async def get_all_leads(
    skip: int = 0,
    limit: int = 200,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Get all leads for the current authenticated user"""
    current_user = get_current_user_from_token(authorization)
    from app.models.campaign import Campaign

    user_campaigns = Campaign.objects(owner_id=str(current_user.id))
    campaign_ids = [str(c.id) for c in user_campaigns]
    if not campaign_ids:
        return []

    if status:
        leads = Lead.objects(campaign_id__in=campaign_ids, status=status).order_by("-created_at").skip(skip).limit(limit)
    else:
        leads = Lead.objects(campaign_id__in=campaign_ids).order_by("-created_at").skip(skip).limit(limit)

    return [serialize_lead(l) for l in leads]


@router.get("/hot", response_model=List[LeadResponse])
async def get_hot_leads(
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """Return only hot leads (grade A and total_score >= 70), sorted by score desc."""
    current_user = get_current_user_from_token(authorization)
    safe_limit = max(1, min(200, int(limit or 50)))

    user_campaigns = Campaign.objects(owner_id=str(current_user.id))
    campaign_ids = [str(c.id) for c in user_campaigns]
    if not campaign_ids:
        return []

    leads = Lead.objects(campaign_id__in=campaign_ids)
    ranked: List[tuple[Lead, int]] = []

    for lead in leads:
        score_payload = lead.score if isinstance(lead.score, dict) else {}
        if not score_payload:
            raw = lead.raw_data or {}
            fallback = raw.get("score_card")
            if isinstance(fallback, dict):
                score_payload = fallback

        total_score = int(score_payload.get("total_score", 0) or 0)
        grade = str(score_payload.get("grade") or "")
        if total_score >= 70 and grade == "A":
            ranked.append((lead, total_score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    selected = [lead for lead, _ in ranked[:safe_limit]]
    return [serialize_lead(lead) for lead in selected]


@router.post("/{lead_id}/generate-email", response_model=GeneratedEmail)
async def generate_lead_email(
    lead_id: str,
    authorization: Optional[str] = Header(None),
):
    """Generate and persist a cold email for one lead using Groq email generator."""
    from app.services.email_generator import email_generator_service

    current_user = get_current_user_from_token(authorization)
    lead = _get_owned_lead_or_404(lead_id, current_user)

    company_profile = _get_company_profile_for_user(str(current_user.id))
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company profile not found. Complete company setup first."
        )

    generated = await email_generator_service.generate_cold_email(lead, company_profile)
    email_payload = GeneratedEmail(
        subject=str(generated.get("subject") or "").strip(),
        body=str(generated.get("body") or "").strip(),
        personalization_score=int(generated.get("personalization_score", 1) or 1),
        generated_at=datetime.utcnow(),
        email_type="cold",
    )

    lead.emails = list(lead.emails or [])
    lead.emails.append(email_payload.model_dump())
    lead.ai_generated_message = f"Subject: {email_payload.subject}\n\n{email_payload.body}".strip()
    lead.raw_data = lead.raw_data or {}
    lead.raw_data["generated_email"] = email_payload.model_dump()
    lead.updated_at = datetime.utcnow()
    lead.save()

    return email_payload


@router.post("/{lead_id}/enrich", response_model=LeadDetailResponse)
async def enrich_single_lead(
    lead_id: str,
    authorization: Optional[str] = Header(None),
):
    """Manually trigger enrichment and score refresh for a specific lead."""
    from app.services.enrichment_service import enrichment_service

    current_user = get_current_user_from_token(authorization)
    lead = _get_owned_lead_or_404(lead_id, current_user)

    raw = lead.raw_data or {}
    source_url = raw.get("source_url") or raw.get("company_website") or ""
    enrichment_payload = await enrichment_service.enrich_lead(
        {
            "company_name": lead.company,
            "company_website": source_url,
            "source_url": source_url,
            "industry": lead.industry,
            "location": raw.get("detected_location") or raw.get("location") or "",
            "intent_signal": raw.get("intent_signal") or "",
            "source": raw.get("source") or "",
        }
    )

    tech_stack = enrichment_payload.get("tech_stack", {}) if isinstance(enrichment_payload.get("tech_stack"), dict) else {}
    decision_maker = enrichment_payload.get("decision_maker", {}) if isinstance(enrichment_payload.get("decision_maker"), dict) else {}
    company_signals = enrichment_payload.get("company_signals", {}) if isinstance(enrichment_payload.get("company_signals"), dict) else {}

    technologies = tech_stack.get("technologies", []) if isinstance(tech_stack.get("technologies", []), list) else []
    recent_signals: List[str] = []
    if company_signals.get("recent_funding"):
        recent_signals.append("recent_funding")
    if company_signals.get("expansion_news"):
        recent_signals.append("expansion_news")
    if company_signals.get("new_product"):
        recent_signals.append("new_product")
    recent_signals.extend([str(item) for item in (company_signals.get("news_snippets") or [])[:3] if str(item).strip()])

    enrichment_model = LeadEnrichment(
        tech_stack=[str(item) for item in technologies if str(item).strip()],
        uses_microsoft_stack=bool(tech_stack.get("uses_microsoft_stack", False)),
        ecommerce_platform=str(tech_stack.get("ecommerce_platform") or "").strip() or None,
        decision_maker=decision_maker if decision_maker else None,
        recent_signals=recent_signals,
        signal_strength=int(company_signals.get("signal_strength", 0) or 0),
    )

    lead.enrichment = enrichment_model.model_dump()
    lead.enriched_data = {
        "tech_stack": tech_stack,
        "decision_maker": decision_maker,
        "company_signals": company_signals,
        "enriched_at": enrichment_payload.get("enriched_at", ""),
    }
    lead.raw_data = lead.raw_data or {}
    lead.raw_data["tech_stack"] = tech_stack
    lead.raw_data["decision_maker"] = decision_maker
    lead.raw_data["company_signals"] = company_signals

    company_profile = _get_company_profile_for_user(str(current_user.id))
    score_payload = await lead_service.calculate_lead_score(
        lead=lead,
        company_profile=company_profile,
        service_hints=(lead.raw_data or {}).get("service_focus") or (company_profile.services if company_profile else []),
    )
    score_model = LeadScore(**score_payload)
    lead.score = score_model.model_dump()
    lead.raw_data["score_card"] = score_model.model_dump()
    lead.raw_data["final_score_100"] = score_model.total_score
    lead.raw_data["final_score"] = round(score_model.total_score / 100.0, 4)
    lead.raw_data["recommended_action"] = score_model.recommended_action
    lead.raw_data["is_hot_lead"] = score_model.is_hot_lead

    lead.updated_at = datetime.utcnow()
    lead.save()

    lead_raw = lead.raw_data or {}
    serialized = serialize_lead(lead)
    serialized.update({
        "raw_data": lead_raw,
        "enriched_data": lead.enriched_data or {},
        "company_fit_score": float(lead.company_fit_score or 0.0),
        "signal_score": float(lead.signal_score or 0.0),
        "signal_keywords": lead.signal_keywords or [],
        "reason": lead_raw.get("final_reason", []),
        "score": lead.score or lead_raw.get("score_card"),
        "ai_generated_message": lead.ai_generated_message,
        "ai_notes": lead.ai_notes,
        "contacted_at": lead.contacted_at,
        "replied_at": lead.replied_at,
    })
    return serialized

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
    
    lead_raw = lead.raw_data or {}
    serialized = serialize_lead(lead)
    serialized.update({
        "raw_data": lead_raw,
        "enriched_data": lead.enriched_data or {},
        "company_fit_score": float(lead.company_fit_score or 0.0),
        "signal_score": float(lead.signal_score or 0.0),
        "signal_keywords": lead.signal_keywords or [],
        "reason": lead_raw.get("final_reason", []),
        "score": lead.score or lead_raw.get("score_card"),
        "ai_generated_message": lead.ai_generated_message,
        "ai_notes": lead.ai_notes,
        "contacted_at": lead.contacted_at,
        "replied_at": lead.replied_at,
    })
    return serialized

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

    # Generate personalized message using intent-aware cold email for hot leads.
    message = ""
    try:
        from app.models.company import CompanyProfile
        from app.services.email_generator import email_generator_service

        company_profile = CompanyProfile.objects(owner_id=current_user.id).first()
        lead_raw = lead.raw_data or {}
        score_100 = lead_raw.get("final_score_100")
        if score_100 is None:
            try:
                score_100 = int(float(lead_raw.get("final_score", 0.0) or 0.0) * 100)
            except Exception:
                score_100 = 0

        if company_profile and int(score_100 or 0) >= 60:
            generated_email = await email_generator_service.generate_cold_email(lead, company_profile)
            subject = str(generated_email.get("subject") or "").strip()
            body = str(generated_email.get("body") or "").strip()
            message = f"Subject: {subject}\n\n{body}".strip()
            lead.raw_data = lead.raw_data or {}
            lead.raw_data["generated_email"] = generated_email
        else:
            message = await ai_service.generate_lead_message(lead, campaign)
    except Exception as e:
        print(f"[CONTACT] Intent email generation failed: {e}")
        message = await ai_service.generate_lead_message(lead, campaign)

    lead.ai_generated_message = message
    lead.save()
    
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
