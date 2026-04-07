"""
MongoDB Models for Spark Outreach
"""
from app.models.user import User
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.embedding import Embedding

__all__ = ["User", "Campaign", "Lead", "Embedding"]
