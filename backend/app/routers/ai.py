"""
AI router for advanced AI operations
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Dict, Any, Optional

from pydantic import BaseModel

from app.config import settings
from app.models.user import User
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.company import CompanyProfile
from app.services.ai_service import ai_service
from app.services.llm_provider import groq_provider
from app.utils.auth import decode_token
from app.utils.json_utils import extract_json_object

router = APIRouter(prefix="/ai", tags=["ai"])


class RAGQuery(BaseModel):
    query: str
    campaign_id: str
    top_k: int = 3


class RAGResponse(BaseModel):
    results: List[Dict[str, Any]]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _top_counts(values: List[str], limit: int = 3) -> List[tuple[str, int]]:
    counts: Dict[str, int] = {}
    for val in values:
        key = (val or "Unknown").strip() or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]


def _build_rule_based_recommendations(
    total_leads: int,
    hot_count: int,
    contacted: int,
    replied: int,
    converted: int,
    conversion_rate: float,
    reply_rate: float,
    unknown_industry_count: int,
    top_industries: List[tuple[str, int]],
    top_titles: List[tuple[str, int]],
    profile: Optional[CompanyProfile],
) -> List[str]:
    recs: List[str] = []

    hot_rate = (hot_count / total_leads * 100.0) if total_leads else 0.0

    if hot_rate < 20:
        service_hint = ", ".join((profile.services or [])[:3]) if profile and profile.services else "your top services"
        recs.append(
            f"Tighten lead search filters around buyer-intent keywords and services ({service_hint}) to increase hot-lead ratio above 20%."
        )

    if hot_count > contacted:
        backlog = hot_count - contacted
        recs.append(
            f"Prioritize outreach to the {backlog} uncontacted hot leads in the next 48 hours to avoid decay in intent."
        )

    if contacted > 0 and reply_rate < 12:
        recs.append(
            "Improve first-touch messaging with industry-specific value props and a single CTA, then A/B test two subject lines for 7 days."
        )

    if contacted > 0 and converted == 0:
        recs.append(
            "Create a 2-step follow-up sequence for replied leads (case study + meeting CTA) to move pipeline from conversations to conversions."
        )

    if total_leads > 0 and unknown_industry_count / total_leads >= 0.25:
        recs.append(
            "Reduce low-context leads by enforcing industry capture during import/enrichment so scoring can rank fit accurately."
        )

    if top_industries:
        recs.append(
            f"Build a dedicated outreach track for {top_industries[0][0]} since it is your largest segment by volume right now."
        )

    if top_titles:
        recs.append(
            f"Create role-specific outreach copy for {top_titles[0][0]} to improve relevance and reply quality."
        )

    if conversion_rate >= 10:
        recs.append(
            "Scale what is already working: duplicate the highest-performing campaign targeting and messaging into one adjacent industry segment."
        )

    return recs[:5]


def _format_insights_text(
    summary: str,
    total_leads: int,
    hot_count: int,
    contacted: int,
    replied: int,
    converted: int,
    conversion_rate: float,
    reply_rate: float,
    top_industries: List[tuple[str, int]],
    top_titles: List[tuple[str, int]],
    status_counts: Dict[str, int],
    insights: List[Dict[str, str]],
) -> str:
    industry_line = ", ".join([f"{name} ({count})" for name, count in top_industries]) or "No industry pattern yet"
    title_line = ", ".join([f"{name} ({count})" for name, count in top_titles]) or "No title pattern yet"
    status_line = ", ".join([f"{name}: {count}" for name, count in sorted(status_counts.items(), key=lambda item: item[1], reverse=True)])

    lines: List[str] = [
        "### Executive Summary",
        summary.strip(),
        "",
        "### Pipeline Snapshot",
        f"- Total leads: {total_leads}",
        f"- Hot leads: {hot_count}",
        f"- Contacted: {contacted}",
        f"- Replied: {replied}",
        f"- Converted: {converted}",
        f"- Reply rate: {reply_rate:.1f}%",
        f"- Conversion rate: {conversion_rate:.1f}%",
        f"- Top industries: {industry_line}",
        f"- Top job titles: {title_line}",
        f"- Lead status mix: {status_line or 'No status data'}",
    ]

    if insights:
        lines.extend(["", "### Priority Insights"])
        for idx, insight in enumerate(insights[:5], start=1):
            title = insight.get("title", "Insight").strip() or "Insight"
            detail = insight.get("detail", "").strip()
            why = insight.get("why_it_matters", "").strip()
            message = f"{idx}. **{title}**: {detail}" if detail else f"{idx}. **{title}**"
            if why:
                message = f"{message} (Why it matters: {why})"
            lines.append(message)

    return "\n".join(lines).strip()


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
    except Exception:
        lead = None

    try:
        campaign = Campaign.objects(id=campaign_id).first()
    except Exception:
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
    Generate AI insights from user-scoped campaigns/leads and company profile context.
    """
    current_user = get_current_user_from_token(authorization)

    campaigns = list(Campaign.objects(owner_id=str(current_user.id)))
    campaign_ids = [str(c.id) for c in campaigns]

    leads = list(Lead.objects(campaign_id__in=campaign_ids)) if campaign_ids else []

    if not leads:
        return {
            "insights": "No lead data is available for your account yet. Run a lead search or import leads first.",
            "recommendations": [
                "Create or activate a campaign and run at least one lead search.",
                "Ensure your company profile is complete so lead scoring can align to your service scope.",
            ],
            "metrics": {
                "total_leads": 0,
                "hot_leads": 0,
                "conversion_rate": 0,
                "contacted": 0,
                "replied": 0,
                "converted": 0,
                "top_industries": [],
            },
            "model": settings.GROQ_MODEL if groq_provider.client else "rules-engine",
        }

    profile = CompanyProfile.objects(owner_id=current_user.id).first()
    if not profile:
        profile = CompanyProfile.objects(owner_id=str(current_user.id)).first()

    now = datetime.utcnow()
    days_14_ago = now - timedelta(days=14)
    days_28_ago = now - timedelta(days=28)

    contacted_statuses = {"contacted", "replied", "converted"}

    hot_count = 0
    contacted = 0
    replied = 0
    converted = 0
    unknown_industry_count = 0
    recent_14d = 0
    previous_14d = 0
    fit_scores: List[float] = []
    signal_scores: List[float] = []

    industries: List[str] = []
    titles: List[str] = []
    status_counts: Dict[str, int] = {}
    leads_per_campaign: Dict[str, int] = {}

    for lead in leads:
        score = lead.score if isinstance(lead.score, dict) else {}
        signal_score = _safe_float(getattr(lead, "signal_score", 0.0))
        company_fit_score = _safe_float(getattr(lead, "company_fit_score", 0.0))

        is_hot = bool(score.get("is_hot_lead")) or signal_score >= 0.65 or company_fit_score >= 0.75
        if is_hot:
            hot_count += 1

        if company_fit_score > 0:
            fit_scores.append(company_fit_score)
        if signal_score > 0:
            signal_scores.append(signal_score)

        status = (lead.status or "new").strip().lower()
        status_counts[status] = status_counts.get(status, 0) + 1

        campaign_key = str(lead.campaign_id)
        leads_per_campaign[campaign_key] = leads_per_campaign.get(campaign_key, 0) + 1

        if lead.message_sent or status in contacted_statuses or lead.contacted_at:
            contacted += 1
        if lead.replied or status in {"replied", "converted"} or lead.replied_at:
            replied += 1
        if lead.converted or status == "converted":
            converted += 1

        industry = (lead.industry or "Unknown").strip() or "Unknown"
        industries.append(industry)
        if industry.lower() == "unknown":
            unknown_industry_count += 1

        if lead.job_title:
            titles.append(lead.job_title.strip())

        created_at = getattr(lead, "created_at", None)
        if created_at:
            if created_at >= days_14_ago:
                recent_14d += 1
            elif created_at >= days_28_ago:
                previous_14d += 1

    conversion_rate = (converted / contacted * 100.0) if contacted else 0.0
    reply_rate = (replied / contacted * 100.0) if contacted else 0.0

    top_industries = _top_counts(industries, limit=3)
    top_titles = _top_counts(titles, limit=3)

    hot_rate = (hot_count / len(leads) * 100.0) if leads else 0.0
    momentum = recent_14d - previous_14d
    avg_fit = (sum(fit_scores) / len(fit_scores)) if fit_scores else 0.0
    avg_signal = (sum(signal_scores) / len(signal_scores)) if signal_scores else 0.0

    campaign_snapshot = []
    for campaign in campaigns[:6]:
        cid = str(campaign.id)
        campaign_snapshot.append({
            "campaign_id": cid,
            "title": campaign.title,
            "status": campaign.status,
            "lead_count": leads_per_campaign.get(cid, 0),
        })

    profile_context = {
        "company_name": profile.company_name if profile else None,
        "services": (profile.services[:6] if profile and profile.services else []),
        "target_industries": (profile.target_industries[:6] if profile and profile.target_industries else []),
        "target_locations": (profile.target_locations[:6] if profile and profile.target_locations else []),
    }

    llm_payload = {
        "metrics": {
            "total_leads": len(leads),
            "hot_leads": hot_count,
            "hot_lead_rate": round(hot_rate, 2),
            "contacted": contacted,
            "replied": replied,
            "converted": converted,
            "reply_rate": round(reply_rate, 2),
            "conversion_rate": round(conversion_rate, 2),
            "avg_company_fit_score": round(avg_fit, 3),
            "avg_signal_score": round(avg_signal, 3),
            "new_leads_last_14_days": recent_14d,
            "new_leads_prev_14_days": previous_14d,
            "momentum_last_14_days": momentum,
            "status_distribution": status_counts,
            "top_industries": [{"name": name, "count": count} for name, count in top_industries],
            "top_job_titles": [{"name": name, "count": count} for name, count in top_titles],
            "unknown_industry_count": unknown_industry_count,
        },
        "campaigns": campaign_snapshot,
        "company_profile": profile_context,
    }

    summary = (
        f"You have {len(leads)} leads across {len(campaigns)} campaigns. "
        f"Hot lead ratio is {hot_rate:.1f}%, reply rate is {reply_rate:.1f}%, "
        f"and conversion rate is {conversion_rate:.1f}%."
    )

    insights_items: List[Dict[str, str]] = [
        {
            "title": "Lead quality baseline",
            "detail": f"Hot lead ratio is {hot_rate:.1f}% ({hot_count}/{len(leads)}).",
            "why_it_matters": "This indicates how efficiently current search filters capture high-intent buyers.",
        },
        {
            "title": "Pipeline progression",
            "detail": f"{contacted} contacted, {replied} replied, {converted} converted.",
            "why_it_matters": "This shows whether the bottleneck is top-of-funnel targeting or post-contact conversion.",
        },
    ]

    model_name = "rules-engine"
    llm_recommendations: List[str] = []

    if groq_provider.client:
        try:
            llm_response = await groq_provider.call_chat_completion(
                system_prompt=(
                    "You are a B2B outbound optimization analyst. "
                    "Return concise, data-grounded insights with no speculation. "
                    "Output only JSON."
                ),
                user_prompt=(
                    "Analyze this account intelligence and return JSON with fields: "
                    "summary (string), insights (array of objects with title/detail/why_it_matters), "
                    "recommendations (array of action strings).\n\n"
                    f"DATA:\n{llm_payload}\n\n"
                    "Rules: recommendations must be specific and executable in CRM/outreach workflow; "
                    "keep each under 180 characters; max 5 recommendations."
                ),
                temperature=0.2,
                max_tokens=1200,
                require_json=True,
            )
            parsed = extract_json_object(llm_response) or {}
            if isinstance(parsed, dict):
                llm_summary = str(parsed.get("summary") or "").strip()
                if llm_summary:
                    summary = llm_summary

                raw_insights = parsed.get("insights")
                if isinstance(raw_insights, list):
                    normalized_insights = []
                    for item in raw_insights:
                        if not isinstance(item, dict):
                            continue
                        title = str(item.get("title") or "").strip()
                        detail = str(item.get("detail") or "").strip()
                        why = str(item.get("why_it_matters") or "").strip()
                        if title or detail:
                            normalized_insights.append({
                                "title": title or "Insight",
                                "detail": detail,
                                "why_it_matters": why,
                            })
                    if normalized_insights:
                        insights_items = normalized_insights[:5]

                raw_recs = parsed.get("recommendations")
                if isinstance(raw_recs, list):
                    llm_recommendations = [str(rec).strip() for rec in raw_recs if str(rec).strip()][:5]

                model_name = settings.GROQ_MODEL
        except Exception as exc:
            print(f"[AI INSIGHTS] LLM generation failed: {exc}")

    if not llm_recommendations:
        llm_recommendations = _build_rule_based_recommendations(
            total_leads=len(leads),
            hot_count=hot_count,
            contacted=contacted,
            replied=replied,
            converted=converted,
            conversion_rate=conversion_rate,
            reply_rate=reply_rate,
            unknown_industry_count=unknown_industry_count,
            top_industries=top_industries,
            top_titles=top_titles,
            profile=profile,
        )

    if not llm_recommendations:
        llm_recommendations = [
            "Run one focused campaign for your top industry and monitor reply rates for 7 days.",
            "Prioritize contact for newly added hot leads within 24-48 hours.",
            "Refine lead filters based on industries and titles that already respond.",
        ]

    insights_text = _format_insights_text(
        summary=summary,
        total_leads=len(leads),
        hot_count=hot_count,
        contacted=contacted,
        replied=replied,
        converted=converted,
        conversion_rate=conversion_rate,
        reply_rate=reply_rate,
        top_industries=top_industries,
        top_titles=top_titles,
        status_counts=status_counts,
        insights=insights_items,
    )

    return {
        "insights": insights_text,
        "recommendations": llm_recommendations[:5],
        "metrics": {
            "total_leads": len(leads),
            "hot_leads": hot_count,
            "conversion_rate": round(conversion_rate, 2),
            "contacted": contacted,
            "replied": replied,
            "converted": converted,
            "top_industries": [{"name": ind, "count": count} for ind, count in top_industries],
        },
        "model": model_name,
    }
