"""
Intent Monitoring Service
Orchestrates job board scanning, signal detection, and lead auto-creation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from bson import ObjectId

from app.models.campaign import Campaign
from app.models.intent import (
    IntentMonitorSchedule,
    IntentScan,
    IntentScanSnapshot,
    IntentSignal,
)
from app.models.lead import Lead
from app.services.jobboard_service import jobboard_service
from app.services.lead_service import lead_service

logger = logging.getLogger(__name__)


class IntentMonitorService:
    """
    Orchestrates recurring web scanning for buyer intent signals
    - Detects companies seeking our services (partnerships, RFP, digital transformation)
    - Auto-creates leads when buyer intent threshold reached
    - Tracks all scanning activity via IntentScan audit logs
    """

    def __init__(self):
        self._active_scans: Dict[str, str] = {}  # user_id -> scan_id
        self._lock = asyncio.Lock()

    async def start_scan(
        self,
        owner_id: str,
        campaign_ids: Optional[List[str]] = None,
    ) -> Tuple[str, bool]:
        """
        Start a new intent scan for owner
        
        Returns:
            (scan_id, already_running)
        """
        uid = str(owner_id)
        
        async with self._lock:
            # Check if scan already running
            if uid in self._active_scans:
                return self._active_scans[uid], True
        
        # Create scan record
        try:
            campaign_oids = [ObjectId(cid) for cid in (campaign_ids or [])]
        except Exception as e:
            logger.error(f"Invalid campaign IDs: {campaign_ids}, error: {e}")
            campaign_oids = []
        
        scan = IntentScan(
            owner_id=ObjectId(uid),
            campaign_ids=campaign_oids,
            status='running',
            results=IntentScanSnapshot(),
        )
        scan.started_at = datetime.utcnow()
        scan.save()
        
        async with self._lock:
            self._active_scans[uid] = str(scan.scan_id)
        
        logger.info(f"Started intent scan {scan.scan_id} for owner {uid}")
        return str(scan.scan_id), False

    async def get_scan_status(self, owner_id: str, scan_id: Optional[str] = None) -> Dict:
        """Get current scan status"""
        uid = str(owner_id)
        
        # Get specific scan or latest
        try:
            if scan_id:
                scan = IntentScan.objects(scan_id=scan_id, owner_id=ObjectId(uid)).first()
            else:
                scan = IntentScan.objects(owner_id=ObjectId(uid)).order_by('-created_at').first()
            
            if not scan:
                return {
                    'status': 'not_found',
                    'message': 'No scan found'
                }
            
            return {
                'scan_id': str(scan.scan_id),
                'status': scan.status,
                'progress': scan.progress,
                'created_at': scan.created_at.isoformat() if scan.created_at else None,
                'started_at': scan.started_at.isoformat() if scan.started_at else None,
                'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
                'results': {
                    'companies_scanned': scan.results.companies_scanned if scan.results else 0,
                    'companies_found': scan.results.companies_found if scan.results else 0,
                    'leads_created': scan.results.leads_created if scan.results else 0,
                    'signals_detected': scan.results.signals_detected if scan.results else 0,
                },
                'error_count': scan.error_count,
            }
        except Exception as e:
            logger.error(f"Error getting scan status: {e}")
            return {'status': 'error', 'message': str(e)}

    async def execute_scan(
        self,
        owner_id: str,
        scan_id: str,
        campaign_ids: Optional[List[str]] = None,
    ) -> Dict:
        """
        Execute complete scan workflow:
        1. For each campaign, get company context
        2. Run job board scanning
        3. Score detected signals
        4. Auto-create leads if threshold exceeded
        5. Persist all findings
        """
        uid = str(owner_id)
        
        try:
            scan = IntentScan.objects(scan_id=scan_id, owner_id=ObjectId(uid)).first()
            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return {'error': 'Scan not found'}
            
            # Initialize results
            scan.results = IntentScanSnapshot()
            scan.status = 'running'
            scan.save()
            
            # Get campaigns to scan
            if not campaign_ids:
                campaign_ids = [str(cid) for cid in (scan.campaign_ids or [])]
            
            logger.info(f"Starting scan {scan_id}: {len(campaign_ids)} campaigns")
            
            for i, campaign_id in enumerate(campaign_ids):
                await self._scan_campaign(
                    owner_id=uid,
                    campaign_id=campaign_id,
                    scan_id=scan_id,
                    progress=(i, len(campaign_ids))
                )
            
            # Mark complete
            scan.status = 'completed'
            scan.completed_at = datetime.utcnow()
            scan.save()
            
            logger.info(f"Completed scan {scan_id}")
            
            # Cleanup active status
            async with self._lock:
                if uid in self._active_scans and self._active_scans[uid] == scan_id:
                    del self._active_scans[uid]
            
            return {
                'status': 'completed',
                'scan_id': scan_id,
                'results': {
                    'companies_scanned': scan.results.companies_scanned,
                    'companies_found': scan.results.companies_found,
                    'leads_created': scan.results.leads_created,
                    'signals_detected': scan.results.signals_detected,
                }
            }
        
        except Exception as e:
            logger.error(f"Error executing scan {scan_id}: {e}", exc_info=True)
            try:
                scan.status = 'failed'
                scan.errors.append(str(e))
                scan.error_count += 1
                scan.completed_at = datetime.utcnow()
                scan.save()
            except:
                pass
            
            async with self._lock:
                if uid in self._active_scans and self._active_scans[uid] == scan_id:
                    del self._active_scans[uid]
            
            return {'error': str(e)}

    async def _scan_campaign(
        self,
        owner_id: str,
        campaign_id: str,
        scan_id: str,
        progress: Tuple[int, int],
    ):
        """Scan single campaign for intent signals"""
        try:
            campaign = Campaign.objects(id=ObjectId(campaign_id)).first()
            if not campaign:
                logger.warning(f"Campaign {campaign_id} not found")
                return
            
            # Get scan record to update
            scan = IntentScan.objects(scan_id=scan_id).first()
            
            # Use campaign search queries or default ones
            services = getattr(campaign, 'services', []) or ['Software Development', 'Web Development']
            locations = getattr(campaign, 'target_locations', []) or ['India']
            
            logger.info(f"[SCAN] Starting buyer intent scan {campaign_id}")
            logger.info(f"[SCAN] Campaign: {campaign.title}")
            logger.info(f"[SCAN] Looking for companies seeking: {getattr(campaign, 'services', [])}")
            logger.info(f"[SCAN] Services being searched: {services}")
            logger.info(f"[SCAN] Target locations: {locations}")
            
            # Run buyer intent discovery
            try:
                logger.info(f"[SCAN] Running buyer intent discovery...")
                buyer_results = await jobboard_service.run_intent_discovery(
                    services=services,
                    locations=locations,
                )
                logger.info(f"[SCAN] Buyer intent discovery complete. Found {len(buyer_results)} companies with buyer signals")
            except Exception as e:
                logger.error(f"[SCAN] Error running buyer discovery: {e}", exc_info=True)
                if scan:
                    scan.errors.append(f"Buyer discovery error: {str(e)}")
                    scan.error_count += 1
                    scan.save()
                return
            
            if not buyer_results:
                logger.warning(f"[SCAN] No buyer signals found for campaign {campaign_id}")
                if scan:
                    scan.results.companies_scanned = 0
                    scan.results.signals_detected = 0
                    scan.save()
                return
            
            logger.info(f"[SCAN] Processing {len(buyer_results)} buyer companies...")
            
            # Extract companies and assess buyer intent
            all_companies = {}
            
            for i, buyer_result in enumerate(buyer_results):
                try:
                    company_name = buyer_result.get('company_name', '').strip()
                    if not company_name:
                        continue
                    
                    # Calculate buyer intent score based on signals
                    signal_strength = self._calculate_intent_score(buyer_result)
                    
                    # Store highest-scoring posting per company
                    company_key = company_name.lower()
                    if company_key not in all_companies or signal_strength > all_companies[company_key]['strength']:
                        all_companies[company_key] = {
                            'name': company_name,
                            'strength': signal_strength,
                            'info': buyer_result,
                        }
                    
                    # Create signal record
                    if signal_strength > 0:
                        from app.models.intent import IntentSignalDetail
                        
                        signal = IntentSignal(
                            campaign_id=ObjectId(campaign_id),
                            company_id=company_name,
                            company_url=buyer_result.get('company_website'),
                            signal_type='hiring',
                            strength=signal_strength,
                            source=buyer_result.get('source', 'linked_jobs'),
                            details=IntentSignalDetail(
                                posting_url=buyer_result.get('job_url'),
                                posting_title=buyer_result.get('job_title'),
                                location=buyer_result.get('location'),
                            )
                        )
                        signal.save()
                        logger.info(f"[SCAN] Created signal for {company_name} (strength: {signal_strength:.2f})")
                        
                        if scan:
                            scan.results.signals_detected += 1
                    
                    # Update progress
                    if i % 10 == 0 and scan:
                        scan.results.companies_scanned = i
                        # Progress for this campaign's processing: campaign_index + (i / total_jobs processed per campaign)
                        campaign_progress = progress[0] + (i / max(len(buyer_results), 1)) * (1.0 / max(progress[1], 1))
                        scan.progress = min(99, int(campaign_progress * 100))
                        scan.save()
                
                except Exception as e:
                    logger.error(f"[SCAN] Error processing job result: {e}", exc_info=True)
                    if scan:
                        scan.errors.append(f"Processing error: {str(e)}")
                        scan.error_count += 1
            
            logger.info(f"[SCAN] Found {len(all_companies)} unique companies with intent signals")
            
            # Auto-create leads for high-intent companies
            schedule = IntentMonitorSchedule.objects(
                owner_id=ObjectId(owner_id),
                enabled=True
            ).first()
            
            intent_threshold = schedule.intent_threshold if schedule else 0.60
            
            for company_key, company_data in all_companies.items():
                try:
                    company_name = company_data['name']
                    signal_strength = company_data['strength']
                    job_info = company_data['info']
                    
                    if signal_strength >= intent_threshold:
                        # Check if lead already exists
                        existing = Lead.objects(
                            company_name=company_name,
                            campaign_id=ObjectId(campaign_id)
                        ).first()
                        
                        if not existing:
                            # Auto-create lead
                            lead = Lead(
                                campaign_id=ObjectId(campaign_id),
                                company_name=company_name,
                                company_url=job_info.get('company_website'),
                                source='intent_monitoring',
                                quality_score=signal_strength,
                                status='discovered',
                                raw_data={
                                    'job_title': job_info.get('job_title'),
                                    'posted_date': job_info.get('posted_date'),
                                    'location': job_info.get('location'),
                                    'intent_signal_source': job_info.get('source'),
                                }
                            )
                            lead.save()
                            
                            if scan:
                                scan.results.leads_created += 1
                            
                            logger.info(f"[SCAN] Auto-created lead: {company_name} (strength: {signal_strength:.2f})")
                        else:
                            if scan:
                                scan.results.leads_updated += 1
                            logger.info(f"[SCAN] Lead already exists: {company_name}")
                
                except Exception as e:
                    logger.error(f"[SCAN] Error creating lead for {company_key}: {e}", exc_info=True)
            
            if scan:
                scan.results.companies_found = len(all_companies)
                scan.results.companies_scanned = len(buyer_results)
                # Mark this campaign portion as complete
                scan.progress = min(99, int((progress[0] + 1) / max(progress[1], 1) * 100))
                scan.save()
                logger.info(
                    f"[SCAN] Campaign scan complete: "
                    f"{scan.results.companies_scanned} companies scanned, "
                    f"{scan.results.companies_found} found, "
                    f"{scan.results.signals_detected} signals, "
                    f"{scan.results.leads_created} leads created"
                )
        
        except Exception as e:
            logger.error(f"[SCAN] Error in _scan_campaign: {e}", exc_info=True)
            raise

    def _calculate_intent_score(self, company_info: Dict) -> float:
        """
        Calculate buyer intent score (0-1) for companies seeking our services
        
        Scoring factors:
        - Base score: 0.5
        - RFP posted: +0.35 (highest signal)
        - Seeking partner: +0.25
        - Digital transformation: +0.2
        - Recent funding: +0.15
        - Expansion stage: +0.15
        """
        score = 0.5  # Base score for any buyer signal
        
        # CRITICAL SIGNALS - Companies actively seeking services/partners
        signal_type = str(company_info.get('signal_type', '')).lower()
        buyer_signal = str(company_info.get('buyer_signal', '')).lower()
        
        # Highest priority: RFP posted (they're actively buying)
        if 'rfp' in signal_type or 'rfp' in buyer_signal:
            score += 0.35
        # High priority: Seeking partner/implementation help
        elif 'seeking_partner' in signal_type or 'partner' in buyer_signal:
            score += 0.25
        # High priority: Digital transformation (major budget initiatives)
        elif 'digital_transformation' in signal_type or 'transformation' in buyer_signal:
            score += 0.20
        # Medium priority: Funding (likely scaling, will need vendors)
        elif 'funding' in signal_type or 'funded' in buyer_signal:
            score += 0.15
        # Medium priority: Expansion (growth = hiring external services)
        elif 'expansion' in signal_type or 'expansion' in buyer_signal:
            score += 0.15
        
        # Company details - investment signals
        company_details = str(company_info.get('details', '')).lower()
        
        # Growth/scaling indicators
        if any(term in company_details for term in ['series a', 'series b', 'funded', 'expanding', 'growth']):
            score += 0.10
        
        # Large company or MNC (more likely to have budget)
        if 'mnc' in company_details or 'enterprise' in company_details:
            score += 0.05
        
        # Actively looking for specific service types
        service = str(company_info.get('service', '')).lower()
        if service and len(service) > 2:
            score += 0.05
        
        # Scale to 0-1
        return min(1.0, max(0.0, score))

    async def setup_schedule(
        self,
        owner_id: str,
        campaign_ids: List[str],
        frequency: str = 'daily',
        scheduled_time: str = '02:00',
        intent_threshold: float = 0.60,
    ) -> Dict:
        """Create or update intent monitoring schedule"""
        try:
            campaign_oids = [ObjectId(cid) for cid in campaign_ids]
            
            schedule = IntentMonitorSchedule.objects(
                owner_id=ObjectId(owner_id),
                campaign_ids=campaign_oids
            ).first()
            
            if schedule:
                schedule.frequency = frequency
                schedule.scheduled_time = scheduled_time
                schedule.intent_threshold = intent_threshold
            else:
                schedule = IntentMonitorSchedule(
                    owner_id=ObjectId(owner_id),
                    campaign_ids=campaign_oids,
                    frequency=frequency,
                    scheduled_time=scheduled_time,
                    intent_threshold=intent_threshold,
                    enabled=True,
                )
            
            # Calculate next run
            schedule.next_run = self._calculate_next_run(frequency, scheduled_time)
            schedule.updated_at = datetime.utcnow()
            schedule.save()
            
            logger.info(f"Setup schedule for {owner_id}: {frequency} @ {scheduled_time}")
            
            return {
                'status': 'created' if not schedule.id else 'updated',
                'schedule_id': str(schedule.id),
                'next_run': schedule.next_run.isoformat() if schedule.next_run else None,
            }
        
        except Exception as e:
            logger.error(f"Error setting up schedule: {e}")
            return {'error': str(e)}

    def _calculate_next_run(self, frequency: str, scheduled_time: str) -> datetime:
        """Calculate next scheduled run time"""
        now = datetime.utcnow()
        
        # Parse scheduled_time (HH:MM)
        try:
            hour, minute = map(int, scheduled_time.split(':'))
        except:
            hour, minute = 2, 0
        
        if frequency == 'hourly':
            next_run = now + timedelta(hours=1)
        elif frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_until_monday = (7 - now.weekday()) % 7
            next_run += timedelta(days=days_until_monday or 7)
        else:  # monthly
            next_run = now.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=32)
            next_run = next_run.replace(day=1)
        
        return next_run

    async def check_and_run_schedules(self):
        """
        Background task: Check all active schedules and run if due
        Should be called by APScheduler / background worker every 5 minutes
        """
        try:
            now = datetime.utcnow()
            
            # Find schedules due to run
            schedules = IntentMonitorSchedule.objects(
                enabled=True,
                next_run__lte=now
            )
            
            logger.info(f"Found {schedules.count()} schedules due to run")
            
            for schedule in schedules:
                try:
                    # Start scan
                    scan_id, already_running = await self.start_scan(
                        owner_id=str(schedule.owner_id),
                        campaign_ids=[str(cid) for cid in schedule.campaign_ids],
                    )
                    
                    if not already_running:
                        # Run async (don't wait)
                        asyncio.create_task(
                            self.execute_scan(
                                owner_id=str(schedule.owner_id),
                                scan_id=scan_id,
                                campaign_ids=[str(cid) for cid in schedule.campaign_ids],
                            )
                        )
                    
                    # Update next run
                    schedule.last_run = now
                    schedule.next_run = self._calculate_next_run(
                        schedule.frequency,
                        schedule.scheduled_time
                    )
                    schedule.consecutive_failures = 0
                    schedule.save()
                
                except Exception as e:
                    logger.error(f"Error running schedule {schedule.id}: {e}")
                    schedule.consecutive_failures += 1
                    if schedule.consecutive_failures >= 3:
                        schedule.enabled = False
                        logger.warning(f"Disabled schedule {schedule.id} after 3 failures")
                    schedule.save()
        
        except Exception as e:
            logger.error(f"Error in check_and_run_schedules: {e}", exc_info=True)


# Singleton instance
intent_monitor_service = IntentMonitorService()
