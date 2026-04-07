"""
Service for campaign operations using MongoDB
"""
from typing import List, Optional
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from datetime import datetime

class CampaignService:
    """Service for campaign-related operations with MongoDB"""
    
    @staticmethod
    def create_campaign(
        campaign: CampaignCreate,
        owner_id: str
    ) -> Campaign:
        """Create a new campaign"""
        db_campaign = Campaign(
            **campaign.model_dump(),
            owner_id=owner_id
        )
        db_campaign.save()
        return db_campaign
    
    @staticmethod
    def get_campaign(campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID"""
        return Campaign.objects(id=campaign_id).first()
    
    @staticmethod
    def get_user_campaigns(
        owner_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Campaign]:
        """Get all campaigns for a user"""
        return Campaign.objects(owner_id=owner_id).skip(skip).limit(limit)
    
    @staticmethod
    def update_campaign(
        campaign_id: str,
        campaign: CampaignUpdate
    ) -> Optional[Campaign]:
        """Update a campaign"""
        db_campaign = Campaign.objects(id=campaign_id).first()
        if not db_campaign:
            return None
        
        update_data = campaign.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_campaign, key, value)
        
        db_campaign.updated_at = datetime.utcnow()
        db_campaign.save()
        return db_campaign
    
    @staticmethod
    def start_campaign(campaign_id: str) -> Optional[Campaign]:
        """Start a campaign"""
        db_campaign = Campaign.objects(id=campaign_id).first()
        if not db_campaign:
            return None
        
        db_campaign.status = "active"
        db_campaign.started_at = datetime.utcnow()
        db_campaign.save()
        return db_campaign
    
    @staticmethod
    def delete_campaign(campaign_id: str) -> bool:
        """Delete a campaign"""
        db_campaign = Campaign.objects(id=campaign_id).first()
        if not db_campaign:
            return False
        
        db_campaign.delete()
        return True

campaign_service = CampaignService()
