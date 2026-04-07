"""
Service for lead operations using MongoDB
"""
from typing import List, Optional
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate
from datetime import datetime

class LeadService:
    """Service for lead-related operations with MongoDB"""
    
    @staticmethod
    def create_lead(lead: LeadCreate) -> Lead:
        """Create a new lead"""
        db_lead = Lead(**lead.model_dump())
        db_lead.save()
        return db_lead
    
    @staticmethod
    def create_bulk_leads(leads: List[LeadCreate]) -> List[Lead]:
        """Create multiple leads at once"""
        db_leads = [Lead(**lead.model_dump()) for lead in leads]
        Lead.objects.insert(db_leads)
        return db_leads
    
    @staticmethod
    def get_lead(lead_id: str) -> Optional[Lead]:
        """Get a lead by ID"""
        return Lead.objects(id=lead_id).first()
    
    @staticmethod
    def get_campaign_leads(
        campaign_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lead]:
        """Get all leads for a campaign"""
        return Lead.objects(campaign_id=campaign_id).skip(skip).limit(limit)
    
    @staticmethod
    def get_leads_by_status(
        campaign_id: str,
        status: str
    ) -> List[Lead]:
        """Get leads filtered by status"""
        return Lead.objects(campaign_id=campaign_id, status=status)
    
    @staticmethod
    def update_lead(
        lead_id: str,
        lead: LeadUpdate
    ) -> Optional[Lead]:
        """Update a lead"""
        db_lead = Lead.objects(id=lead_id).first()
        if not db_lead:
            return None
        
        update_data = lead.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)
        
        db_lead.updated_at = datetime.utcnow()
        db_lead.save()
        return db_lead
    
    @staticmethod
    def mark_as_contacted(lead_id: str) -> Optional[Lead]:
        """Mark a lead as contacted"""
        db_lead = Lead.objects(id=lead_id).first()
        if not db_lead:
            return None
        
        db_lead.status = "contacted"
        db_lead.message_sent = True
        db_lead.contacted_at = datetime.utcnow()
        db_lead.save()
        return db_lead
    
    @staticmethod
    def mark_as_replied(lead_id: str) -> Optional[Lead]:
        """Mark a lead as replied"""
        db_lead = Lead.objects(id=lead_id).first()
        if not db_lead:
            return None
        
        db_lead.status = "replied"
        db_lead.replied = True
        db_lead.replied_at = datetime.utcnow()
        db_lead.save()
        return db_lead
    
    @staticmethod
    def delete_lead(lead_id: str) -> bool:
        """Delete a lead"""
        db_lead = Lead.objects(id=lead_id).first()
        if not db_lead:
            return False
        
        db_lead.delete()
        return True

lead_service = LeadService()
