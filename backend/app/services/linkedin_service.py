"""
LinkedIn Outreach Service
Manages connection requests, messaging, and multi-step nurture sequences
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from bson import ObjectId

from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.intent import (
    LinkedInConnection,
    LinkedInMessage,
    LinkedInSequence,
)

logger = logging.getLogger(__name__)


# Message templates for different sequence styles
SEQUENCE_TEMPLATES = {
    'standard': {
        'day_0': {
            'type': 'connection_request',
            'body': "Hi {first_name}, I came across your profile and thought we could discuss how {service} can help {company} scale faster. Let's connect!",
        },
        'day_3': {
            'type': 'followup',
            'body': "Hi {first_name}, Following up on my earlier connection request. I've been impressed with {company}'s growth in {industry}. I'd love to chat about potential opportunities.",
        },
        'day_7': {
            'type': 'message',
            'body': "Hi {first_name}, Thanks for connecting! I recently worked with similar companies on {service}. Quick question - what are your biggest challenges with {pain_point} right now?",
        },
        'day_14': {
            'type': 'message',
            'body': "Hi {first_name}, I've put together some specific ideas for {company}. Would you be open to a 20-min call next week to discuss?",
        },
    },
    'aggressive': {
        'day_0': {
            'type': 'connection_request',
            'body': "Hi {first_name}, Quick connect - I help companies like {company} with {service}. Open to exploring?",
        },
        'day_1': {
            'type': 'message',
            'body': "Hi {first_name}, Value add here: {company} could 3x efficiency with {service}. Interested in a 15-min call?",
        },
        'day_3': {
            'type': 'message',
            'body': "Hi {first_name}, Last message - most teams I work with see ROI in 30 days. Open to a quick conversation?",
        },
    },
    'consultative': {
        'day_0': {
            'type': 'connection_request',
            'body': "Hi {first_name}, I work with {industry} companies on {service}. Would love to learn more about {company}'s vision.",
        },
        'day_5': {
            'type': 'message',
            'body': "Hi {first_name}, Saw your recent {company} update on {activity}. Curious about your approach to {pain_point}. Worth a conversation?",
        },
        'day_10': {
            'type': 'message',
            'body': "Hi {first_name}, I prepared some {industry} benchmarks that might be relevant to your team. Happy to share.",
        },
    },
    'value_first': {
        'day_0': {
            'type': 'connection_request',
            'body': "Hi {first_name}, Here's a resource on {service} best practices for {industry}: [link]. Happy to discuss further.",
        },
        'day_7': {
            'type': 'message',
            'body': "Hi {first_name}, Following up - did the {service} guide help? I'd love to share more specific insights for {company}.",
        },
        'day_14': {
            'type': 'message',
            'body': "Hi {first_name}, I've mapped out 3 quick wins for {company}. Would you be open to a brief discussion?",
        },
    },
}


class LinkedInOutreachService:
    """
    Manages LinkedIn connection requests, messaging, and automated sequences
    - Sends connection requests with personalized notes
    - Tracks connection acceptance/rejection
    - Sends follow-up messages on schedule
    - Tracks replies and engagement
    - Manages multi-step nurture sequences
    """

    def __init__(self):
        self._pending_actions: Dict[str, List[str]] = {}  # campaign_id -> [message_ids]
        self._lock = asyncio.Lock()

    def _interpolate_message(
        self,
        template: str,
        lead: Lead,
        campaign: Campaign,
    ) -> str:
        """
        Replace template variables with actual values
        Variables: {first_name}, {company}, {service}, {industry}, {pain_point}, {activity}
        """
        try:
            company_name = lead.company_name or lead.company or "your company"
            
            # Extract first name from lead name
            first_name = lead.name.split()[0] if lead.name else "there"
            
            # Get campaign info
            services = ", ".join(campaign.services or []) if campaign.services else "our services"
            industry = lead.industry or "your industry"
            
            # Pain points based on industry
            pain_points = {
                'saas': 'customer acquisition costs',
                'fintech': 'compliance and security',
                'edtech': 'user engagement',
                'healthtech': 'data privacy',
                'default': 'scaling operations'
            }
            industry_lower = industry.lower()
            pain_point = next(
                (v for k, v in pain_points.items() if k in industry_lower),
                pain_points['default']
            )
            
            # Activity (generic for now)
            activity = "recent company growth"
            
            return template.format(
                first_name=first_name,
                company=company_name,
                service=services,
                industry=industry,
                pain_point=pain_point,
                activity=activity,
            )
        except Exception as e:
            logger.error(f"Error interpolating message: {e}")
            return template

    async def start_sequence(
        self,
        lead_id: str,
        campaign_id: str,
        owner_id: str,
        template_set: str = 'standard',
        linkedin_profile_url: str = None,
    ) -> Optional[str]:
        """
        Start LinkedIn outreach sequence for a lead
        
        Returns: connection_id
        """
        try:
            # Get lead and campaign
            lead = Lead.objects(id=ObjectId(lead_id)).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return None
            
            campaign = Campaign.objects(id=ObjectId(campaign_id)).first()
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return None
            
            # Create or get LinkedIn connection record
            connection = LinkedInConnection.objects(
                lead_id=ObjectId(lead_id),
                campaign_id=ObjectId(campaign_id),
            ).first()
            
            if not connection:
                connection = LinkedInConnection(
                    lead_id=ObjectId(lead_id),
                    campaign_id=ObjectId(campaign_id),
                    owner_id=ObjectId(owner_id),
                    profile_url=linkedin_profile_url or f"https://linkedin.com/in/{lead.name.lower().replace(' ', '-')}",
                    profile_name=lead.name,
                    profile_title=lead.job_title,
                    company_name=lead.company_name,
                    connection_status='pending',
                )
                connection.save()
            
            # Get or create sequence
            sequence = LinkedInSequence.objects(
                campaign_id=ObjectId(campaign_id),
                owner_id=ObjectId(owner_id),
            ).first()
            
            if not sequence:
                sequence = LinkedInSequence(
                    campaign_id=ObjectId(campaign_id),
                    owner_id=ObjectId(owner_id),
                    template_set=template_set,
                    status='active',
                )
                sequence.save()
            
            # Enroll lead in sequence
            if ObjectId(lead_id) not in sequence.leads_enrolled:
                sequence.leads_enrolled.append(ObjectId(lead_id))
                sequence.lead_count = len(sequence.leads_enrolled)
                sequence.save()
            
            logger.info(f"Started LinkedIn sequence for lead {lead_id}")
            return str(connection.id)
        
        except Exception as e:
            logger.error(f"Error starting sequence: {e}", exc_info=True)
            return None

    async def send_connection_request(
        self,
        connection_id: str,
        message_override: Optional[str] = None,
    ) -> Dict:
        """
        Send LinkedIn connection request
        TODO: Integrate with actual LinkedIn API (linkedin-api library)
        """
        try:
            connection = LinkedInConnection.objects(id=ObjectId(connection_id)).first()
            if not connection:
                return {'error': 'Connection not found'}
            
            lead = Lead.objects(id=connection.lead_id).first()
            campaign = Campaign.objects(id=connection.campaign_id).first()
            
            if not lead or not campaign:
                return {'error': 'Lead or campaign not found'}
            
            # Get template
            template_set = connection.connection_status or 'standard'
            template = SEQUENCE_TEMPLATES.get(template_set, SEQUENCE_TEMPLATES['standard'])
            day_0_msg = template.get('day_0', {})
            
            # Interpolate message
            request_message = message_override or self._interpolate_message(
                day_0_msg.get('body', ''),
                lead,
                campaign,
            )
            
            # TODO: Use linkedin-api to send actual connection request
            # For now, just log and record intent
            logger.info(
                f"[LINKEDIN] Would send connection to {connection.profile_url}: {request_message[:100]}..."
            )
            
            # Create and save message record
            message = LinkedInMessage(
                connection_id=connection.id,
                lead_id=connection.lead_id,
                campaign_id=connection.campaign_id,
                owner_id=connection.owner_id,
                text=request_message,
                message_type='connection_request',
                direction='outbound',
                status='sent',
                sequence_day=0,
            )
            message.save()
            
            # Update connection
            connection.request_message = request_message
            connection.request_sent_at = datetime.utcnow()
            connection.connection_status = 'pending'
            connection.save()
            
            logger.info(f"Sent connection request: {connection_id}")
            
            return {
                'status': 'sent',
                'message_id': str(message.id),
                'connection_id': str(connection.id),
            }
        
        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            return {'error': str(e)}

    async def send_message(
        self,
        connection_id: str,
        message_text: str,
        sequence_day: int = 1,
    ) -> Dict:
        """
        Send LinkedIn message to connected person
        TODO: Integrate with actual LinkedIn API
        """
        try:
            connection = LinkedInConnection.objects(id=ObjectId(connection_id)).first()
            if not connection:
                return {'error': 'Connection not found'}
            
            if connection.connection_status != 'connected':
                return {'error': 'Not connected yet'}
            
            # TODO: Use linkedin-api to send actual message
            logger.info(
                f"[LINKEDIN] Would send message to {connection.profile_url}: {message_text[:100]}..."
            )
            
            # Record message
            message = LinkedInMessage(
                connection_id=connection.id,
                lead_id=connection.lead_id,
                campaign_id=connection.campaign_id,
                owner_id=connection.owner_id,
                text=message_text,
                message_type='message',
                direction='outbound',
                status='sent',
                sequence_day=sequence_day,
            )
            message.save()
            
            # Update connection
            connection.message_count = (connection.message_count or 0) + 1
            connection.last_message_date = datetime.utcnow()
            connection.last_activity = datetime.utcnow()
            connection.save()
            
            logger.info(f"Sent message: {connection_id} (day {sequence_day})")
            
            return {
                'status': 'sent',
                'message_id': str(message.id),
                'sequence_day': sequence_day,
            }
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {'error': str(e)}

    async def process_pending_sequences(self):
        """
        Background task: Check sequences for pending actions
        Should be called every 6 hours or daily
        
        Workflow:
        1. Get all active sequences
        2. For each enrolled lead:
           - Check if connection exists
           - Calculate days since enrollment
           - Send appropriate action (connect, message, followup)
           - Update status
        """
        try:
            sequences = LinkedInSequence.objects(status='active')
            logger.info(f"Processing {sequences.count()} active sequences")
            
            for sequence in sequences:
                try:
                    await self._process_sequence(sequence)
                except Exception as e:
                    logger.error(f"Error processing sequence {sequence.id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in process_pending_sequences: {e}", exc_info=True)

    async def _process_sequence(self, sequence: LinkedInSequence):
        """Process single sequence for all enrolled leads"""
        template_set = sequence.template_set or 'standard'
        templates = SEQUENCE_TEMPLATES.get(template_set, SEQUENCE_TEMPLATES['standard'])
        
        campaign = Campaign.objects(id=sequence.campaign_id).first()
        if not campaign:
            logger.warning(f"Campaign {sequence.campaign_id} not found")
            return
        
        for lead_id in sequence.leads_enrolled:
            try:
                lead = Lead.objects(id=lead_id).first()
                if not lead:
                    continue
                
                # Get or create connection
                connection = LinkedInConnection.objects(
                    lead_id=lead_id,
                    campaign_id=sequence.campaign_id,
                ).first()
                
                if not connection:
                    # Create new connection (first time)
                    connection = LinkedInConnection(
                        lead_id=lead_id,
                        campaign_id=sequence.campaign_id,
                        owner_id=sequence.owner_id,
                        profile_url=f"https://linkedin.com/in/{lead.name.lower().replace(' ', '-')}",
                        profile_name=lead.name,
                        profile_title=lead.job_title,
                        company_name=lead.company_name,
                    )
                    connection.save()
                
                # Determine days since enrollment
                days_since = await self._calculate_days_since_enrollment(lead_id, sequence.id)
                
                # Determine next action based on day
                next_action = self._get_action_for_day(days_since, templates, connection)
                
                if next_action:
                    await self._execute_action(
                        connection=connection,
                        lead=lead,
                        campaign=campaign,
                        action=next_action,
                        sequence_day=days_since,
                        template_set=template_set,
                    )
            
            except Exception as e:
                logger.error(f"Error processing lead {lead_id} in sequence: {e}")

    def _get_action_for_day(
        self,
        days_since: int,
        templates: Dict,
        connection: LinkedInConnection,
    ) -> Optional[Dict]:
        """Determine what action to take based on days since enrollment"""
        # Find matching day in templates
        day_key = f"day_{days_since}"
        if day_key in templates:
            return templates[day_key]
        
        # Check if connection already established
        if connection.connection_status == 'connected' and days_since >= 7:
            # Send message on day 7 if not already sent
            if not connection.last_message_date:
                return templates.get('day_7', templates.get('day_3'))
        
        # Check for connection on day 0
        if days_since == 0 and connection.connection_status == 'not_contacted':
            return templates.get('day_0')
        
        return None

    async def _calculate_days_since_enrollment(
        self,
        lead_id: str,
        sequence_id: str,
    ) -> int:
        """Calculate days since lead enrolled in sequence"""
        # Get first message/connection for this lead in this sequence
        first_action = LinkedInMessage.objects(
            lead_id=ObjectId(lead_id),
        ).order_by('sent_at').first()
        
        if first_action and first_action.sent_at:
            days = (datetime.utcnow() - first_action.sent_at).days
            return max(0, days)
        
        # Default to day 0
        return 0

    async def _execute_action(
        self,
        connection: LinkedInConnection,
        lead: Lead,
        campaign: Campaign,
        action: Dict,
        sequence_day: int,
        template_set: str,
    ):
        """Execute single action (connection request, message, etc.)"""
        action_type = action.get('type')
        template_text = action.get('body', '')
        
        if not template_text:
            return
        
        # Interpolate message
        message_text = self._interpolate_message(template_text, lead, campaign)
        
        if action_type == 'connection_request':
            await self.send_connection_request(str(connection.id), message_text)
        
        elif action_type in ['message', 'followup']:
            if connection.connection_status == 'connected':
                await self.send_message(str(connection.id), message_text, sequence_day)
            else:
                # Not connected yet, record as pending
                logger.info(f"Deferring message, not connected yet: {connection.id}")

    async def mark_replied(
        self,
        connection_id: str,
        reply_text: str,
    ) -> Dict:
        """
        Record that contact replied
        TODO: Integrate with LinkedIn notifications/API polling
        """
        try:
            connection = LinkedInConnection.objects(id=ObjectId(connection_id)).first()
            if not connection:
                return {'error': 'Connection not found'}
            
            # Create inbound message record
            message = LinkedInMessage(
                connection_id=connection.id,
                lead_id=connection.lead_id,
                campaign_id=connection.campaign_id,
                owner_id=connection.owner_id,
                text=reply_text,
                message_type='reply',
                direction='inbound',
                status='received',
            )
            message.save()
            
            # Update connection
            connection.reply_count = (connection.reply_count or 0) + 1
            connection.last_activity = datetime.utcnow()
            connection.save()
            
            # Update sequence metrics
            sequence = LinkedInSequence.objects(campaign_id=connection.campaign_id).first()
            if sequence:
                sequence.replies_received += 1
                sequence.save()
            
            logger.info(f"Recorded reply for connection {connection_id}")
            
            return {
                'status': 'recorded',
                'message_id': str(message.id),
                'reply_count': connection.reply_count,
            }
        
        except Exception as e:
            logger.error(f"Error marking replied: {e}")
            return {'error': str(e)}

    async def get_sequence_analytics(
        self,
        sequence_id: str,
    ) -> Dict:
        """Get engagement metrics for a sequence"""
        try:
            sequence = LinkedInSequence.objects(id=ObjectId(sequence_id)).first()
            if not sequence:
                return {'error': 'Sequence not found'}
            
            # Get all messages in this sequence
            messages = LinkedInMessage.objects(campaign_id=sequence.campaign_id)
            
            connections = LinkedInConnection.objects(campaign_id=sequence.campaign_id)
            
            return {
                'sequence_id': str(sequence.id),
                'status': sequence.status,
                'leads_enrolled': sequence.lead_count,
                'connections_sent': sequence.connections_sent,
                'connections_accepted': sequence.connections_accepted,
                'messages_sent': sequence.messages_sent,
                'replies_received': sequence.replies_received,
                'total_actions': messages.count(),
                'engagement_rate': (
                    (sequence.connections_accepted + sequence.replies_received) /
                    max(sequence.lead_count, 1)
                ) if sequence.lead_count > 0 else 0,
                'created_at': sequence.created_at.isoformat() if sequence.created_at else None,
                'started_at': sequence.started_at.isoformat() if sequence.started_at else None,
            }
        
        except Exception as e:
            logger.error(f"Error getting sequence analytics: {e}")
            return {'error': str(e)}

    async def list_connections(
        self,
        campaign_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """List all connections for a campaign"""
        try:
            query = LinkedInConnection.objects(campaign_id=ObjectId(campaign_id))
            
            if status:
                query = query.filter(connection_status=status)
            
            connections = query.order_by('-created_at').limit(limit)
            
            return [
                {
                    'connection_id': str(c.id),
                    'lead_id': str(c.lead_id),
                    'profile_url': c.profile_url,
                    'profile_name': c.profile_name,
                    'company_name': c.company_name,
                    'connection_status': c.connection_status,
                    'message_count': c.message_count,
                    'reply_count': c.reply_count,
                    'request_sent_at': c.request_sent_at.isoformat() if c.request_sent_at else None,
                    'accepted_at': c.accepted_at.isoformat() if c.accepted_at else None,
                    'last_activity': c.last_activity.isoformat() if c.last_activity else None,
                }
                for c in connections
            ]
        
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
            return []


# Singleton instance
linkedin_outreach_service = LinkedInOutreachService()
