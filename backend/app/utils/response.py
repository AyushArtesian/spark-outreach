"""
Response serialization utilities for MongoDB ObjectId conversion
"""
from bson import ObjectId
from typing import Any, Dict
from datetime import datetime


def serialize_objectid(obj: Any) -> Any:
    """Convert ObjectId to string in objects and dicts"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_objectid(item) for item in obj]
    return obj


def serialize_user(user) -> Dict[str, Any]:
    """Serialize a User MongoEngine document to dict with string IDs"""
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


def serialize_campaign(campaign) -> Dict[str, Any]:
    """Serialize a Campaign MongoEngine document to dict with string IDs"""
    return {
        "id": str(campaign.id),
        "owner_id": str(campaign.owner_id),
        "title": campaign.title,
        "description": campaign.description,
        "content": campaign.content,
        "target_audience": campaign.target_audience,
        "ai_model": campaign.ai_model,
        "temperature": campaign.temperature,
        "max_tokens": campaign.max_tokens,
        "status": campaign.status,
        "custom_instructions": campaign.custom_instructions,
        "max_leads": campaign.max_leads,
        "follow_up_enabled": campaign.follow_up_enabled,
        "follow_up_delay_hours": campaign.follow_up_delay_hours,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
        "started_at": campaign.started_at,
        "completed_at": campaign.completed_at
    }


def _sanitize_email(email: str) -> str:
    """Extract valid email from malformed/URL strings like 'http://info@rubixtech.in'"""
    if not email:
        return ""
    
    email = str(email).strip()
    
    # Remove common URL prefixes
    for prefix in ["http://", "https://", "www."]:
        if email.startswith(prefix):
            email = email[len(prefix):]
    
    # If there's a slash, get the part before it
    if "/" in email:
        email = email.split("/")[0]
    
    # Validate basic email format
    if "@" in email and "." in email.split("@")[-1]:
        return email
    
    return ""


def serialize_lead(lead) -> Dict[str, Any]:
    """Serialize a Lead MongoEngine document to dict with string IDs"""
    # Sanitize email to ensure it's valid
    email = _sanitize_email(lead.email)

    score_payload = lead.score if isinstance(lead.score, dict) and lead.score else None
    if not score_payload and lead.raw_data:
        fallback = lead.raw_data.get("score_card")
        if isinstance(fallback, dict) and fallback:
            score_payload = fallback
    
    # Ensure score_payload has all required fields or is None
    if score_payload and not all(k in score_payload for k in ["total_score", "grade", "breakdown", "is_hot_lead", "recommended_action"]):
        score_payload = None

    enrichment_payload = lead.enrichment if isinstance(lead.enrichment, dict) else None
    if not enrichment_payload and lead.enriched_data:
        tech_stack = lead.enriched_data.get("tech_stack", {}) if isinstance(lead.enriched_data, dict) else {}
        decision_maker = lead.enriched_data.get("decision_maker", {}) if isinstance(lead.enriched_data, dict) else {}
        company_signals = lead.enriched_data.get("company_signals", {}) if isinstance(lead.enriched_data, dict) else {}
        technologies = tech_stack.get("technologies", []) if isinstance(tech_stack, dict) else []
        if isinstance(technologies, str):
            technologies = [technologies]
        recent_signals = []
        if isinstance(company_signals, dict):
            if company_signals.get("recent_funding"):
                recent_signals.append("recent_funding")
            if company_signals.get("expansion_news"):
                recent_signals.append("expansion_news")
            if company_signals.get("new_product"):
                recent_signals.append("new_product")
            for snippet in company_signals.get("news_snippets", [])[:3]:
                if snippet:
                    recent_signals.append(str(snippet))

        enrichment_payload = {
            "tech_stack": [str(item) for item in technologies if str(item).strip()],
            "uses_microsoft_stack": bool(tech_stack.get("uses_microsoft_stack", False)) if isinstance(tech_stack, dict) else False,
            "ecommerce_platform": str(tech_stack.get("ecommerce_platform") or "").strip() or None if isinstance(tech_stack, dict) else None,
            "decision_maker": decision_maker if isinstance(decision_maker, dict) and decision_maker else None,
            "recent_signals": recent_signals,
            "signal_strength": int(company_signals.get("signal_strength", 0) or 0) if isinstance(company_signals, dict) else 0,
        }

    emails_payload = []
    for item in (lead.emails or []):
        if not isinstance(item, dict):
            continue
        email_type = str(item.get("email_type") or "cold").strip().lower()
        if email_type not in {"cold", "followup1", "followup2", "linkedin"}:
            email_type = "cold"
        emails_payload.append(
            {
                "subject": str(item.get("subject") or ""),
                "body": str(item.get("body") or ""),
                "personalization_score": int(item.get("personalization_score", 0) or 0),
                "generated_at": item.get("generated_at") or datetime.utcnow(),
                "email_type": email_type,
            }
        )
    
    return {
        "id": str(lead.id),
        "campaign_id": str(lead.campaign_id),
        "name": lead.name,
        "email": email,
        "company": lead.company,
        "phone": lead.phone,
        "job_title": lead.job_title,
        "industry": lead.industry,
        "status": lead.status,
        "relevance_score": lead.relevance_score,
        "company_fit_score": float(lead.company_fit_score or 0.0),
        "signal_score": float(lead.signal_score or 0.0),
        "signal_keywords": lead.signal_keywords or [],
        "message_sent": lead.message_sent,
        "opened": lead.opened,
        "clicked": lead.clicked,
        "replied": lead.replied,
        "converted": lead.converted,
        "score": score_payload,
        "enrichment": enrichment_payload,
        "emails": emails_payload,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at
    }
