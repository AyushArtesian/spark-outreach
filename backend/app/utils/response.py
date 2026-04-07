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


def serialize_lead(lead) -> Dict[str, Any]:
    """Serialize a Lead MongoEngine document to dict with string IDs"""
    return {
        "id": str(lead.id),
        "campaign_id": str(lead.campaign_id),
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "phone": lead.phone,
        "job_title": lead.job_title,
        "industry": lead.industry,
        "status": lead.status,
        "relevance_score": lead.relevance_score,
        "message_sent": lead.message_sent,
        "opened": lead.opened,
        "clicked": lead.clicked,
        "replied": lead.replied,
        "converted": lead.converted,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at
    }
