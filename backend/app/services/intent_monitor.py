"""Daily intent scan orchestration service."""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from bson import ObjectId

from app.models.campaign import Campaign
from app.models.company import CompanyProfile
from app.models.lead import Lead
from app.services.enrichment_service import enrichment_service
from app.services.jobboard_service import jobboard_service
from app.services.lead_service import lead_service
from app.services.service_catalog import TARGET_SERVICE_PORTFOLIO


class IntentMonitorService:
    """Run recurring job-board intent discovery and persist scored leads."""

    def __init__(self) -> None:
        self._runtime_status: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _safe_str(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _company_key(value: str) -> str:
        import re

        normalized = re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower())
        return re.sub(r"\s+", " ", normalized).strip()

    @staticmethod
    def _profile_by_owner(user_id: str) -> Optional[CompanyProfile]:
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

    async def _update_runtime(self, user_id: str, payload: Dict[str, Any]) -> None:
        async with self._lock:
            current = dict(self._runtime_status.get(str(user_id), {}))
            current.update(payload)
            self._runtime_status[str(user_id)] = current

    async def start_scan(self, user_id: str) -> Tuple[str, bool]:
        """Reserve a scan slot and return (scan_id, already_running)."""
        uid = str(user_id)
        now = datetime.utcnow()

        async with self._lock:
            existing = self._runtime_status.get(uid) or {}
            if existing.get("status") == "running" and existing.get("scan_id"):
                return str(existing["scan_id"]), True

            scan_id = str(uuid.uuid4())
            self._runtime_status[uid] = {
                "scan_id": scan_id,
                "status": "running",
                "started_at": now,
                "summary": {},
            }

        profile = self._profile_by_owner(uid)
        if profile:
            try:
                profile.intent_scan_status = "running"
                profile.intent_scan_id = scan_id
                profile.save()
            except Exception as e:
                print(f"[INTENT MONITOR] Failed to persist running status: {e}")

        return scan_id, False

    async def get_scan_status(self, user_id: str) -> Dict[str, Any]:
        """Get scan status for the user from runtime state and persisted profile."""
        uid = str(user_id)
        async with self._lock:
            runtime = dict(self._runtime_status.get(uid, {}))

        profile = self._profile_by_owner(uid)
        persisted_summary = profile.intent_scan_last_summary if profile and profile.intent_scan_last_summary else {}
        persisted_last_scan = profile.intent_scan_last_run if profile else None
        persisted_status = self._safe_str(profile.intent_scan_status) if profile else ""
        persisted_scan_id = self._safe_str(profile.intent_scan_id) if profile else ""

        if runtime.get("status") == "running":
            return {
                "status": "running",
                "scan_id": runtime.get("scan_id") or persisted_scan_id,
                "last_scan": persisted_last_scan,
                "summary": runtime.get("summary") or persisted_summary or {},
            }

        status_value = persisted_status or ("complete" if persisted_summary else "idle")
        return {
            "status": status_value,
            "scan_id": persisted_scan_id or runtime.get("scan_id"),
            "last_scan": persisted_last_scan,
            "summary": persisted_summary or runtime.get("summary") or {},
        }

    async def run_daily_scan(self, user_id: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run one full intent scan pipeline and return summary.

        Steps:
        1. Load user company profile.
        2. Discover hiring-intent companies from job boards.
        3. Enrich candidate companies.
        4. Score leads with weighted scoring.
        5. Save qualifying leads (score >= 40) tagged as intent monitor source.
        """
        uid = str(user_id)
        started_at = datetime.utcnow()
        start_ts = time.perf_counter()

        active_scan_id = scan_id
        already_running = False
        if not active_scan_id:
            active_scan_id, already_running = await self.start_scan(uid)
            if already_running:
                return {
                    "new_leads_found": 0,
                    "hot_leads": 0,
                    "services_scanned": [],
                    "scan_duration_seconds": 0.0,
                    "scan_id": active_scan_id,
                    "message": "Scan already running",
                }

        await self._update_runtime(
            uid,
            {
                "scan_id": active_scan_id,
                "status": "running",
                "started_at": started_at,
                "summary": {},
            },
        )

        summary: Dict[str, Any] = {
            "new_leads_found": 0,
            "hot_leads": 0,
            "services_scanned": [],
            "scan_duration_seconds": 0.0,
            "scan_id": active_scan_id,
        }

        try:
            company_profile = self._profile_by_owner(uid)
            if not company_profile:
                summary["scan_duration_seconds"] = round(time.perf_counter() - start_ts, 2)
                summary["error"] = "Company profile not found"
                return summary

            services = [self._safe_str(item) for item in (company_profile.services or []) if self._safe_str(item)]
            locations = [self._safe_str(item) for item in (company_profile.target_locations or []) if self._safe_str(item)]

            if not services:
                services = list(TARGET_SERVICE_PORTFOLIO)
            if not locations:
                locations = ["India"]

            summary["services_scanned"] = services
            discovered_jobs = await jobboard_service.run_intent_discovery(
                services=services,
                locations=locations,
            )

            campaign = lead_service._get_or_create_default_campaign(uid)
            owner_campaign_ids = [str(c.id) for c in Campaign.objects(owner_id=uid)]
            existing_leads = Lead.objects(campaign_id__in=owner_campaign_ids)

            seen_domains: Set[str] = set()
            seen_companies: Set[str] = set()
            for db_lead in existing_leads:
                raw = db_lead.raw_data or {}
                domain = lead_service._canonical_domain(raw.get("source_url") or raw.get("company_website") or "")
                if domain:
                    seen_domains.add(domain)
                company_key = self._company_key(db_lead.company or db_lead.name)
                if company_key:
                    seen_companies.add(company_key)

            new_leads_found = 0
            hot_leads = 0
            discovered_day = datetime.utcnow().date().isoformat()

            for job in discovered_jobs:
                company_name = self._safe_str(job.get("company_name"))
                if not company_name:
                    continue

                website = self._safe_str(job.get("company_website"))
                domain = lead_service._canonical_domain(website)
                company_key = self._company_key(company_name)

                if domain and domain in seen_domains:
                    continue
                if company_key and company_key in seen_companies:
                    continue

                enriched = await enrichment_service.enrich_lead(
                    {
                        "company_name": company_name,
                        "company_website": website,
                        "location": self._safe_str(job.get("location")),
                        "intent_signal": "hiring",
                        "source": "intent_monitor",
                    }
                )

                decision = enriched.get("decision_maker", {}) if isinstance(enriched.get("decision_maker"), dict) else {}
                tech_stack = enriched.get("tech_stack", {}) if isinstance(enriched.get("tech_stack"), dict) else {}
                company_signals = enriched.get("company_signals", {}) if isinstance(enriched.get("company_signals"), dict) else {}

                email = self._safe_str(decision.get("email"))
                if not email and domain:
                    email = f"contact@{domain}"
                if not email:
                    email = f"unknown+{(company_key or 'intent')[:12]}@intent.local"

                location_value = self._safe_str(job.get("location"))
                job_title = self._safe_str(job.get("job_title") or "Hiring Team")
                posted_date = self._safe_str(job.get("posted_date"))

                candidate_lead = Lead(
                    campaign_id=str(campaign.id),
                    name=company_name,
                    email=email,
                    company=company_name,
                    phone=self._safe_str(decision.get("phone") or ""),
                    job_title=job_title,
                    industry=self._safe_str(job.get("industry") or ""),
                    status="new",
                    signal_keywords=["hiring"],
                    signal_score=0.0,
                    enriched_data={
                        "tech_stack": tech_stack,
                        "decision_maker": decision,
                        "company_signals": company_signals,
                        "enriched_at": enriched.get("enriched_at", ""),
                    },
                    raw_data={
                        "source": "intent_monitor",
                        "source_url": website,
                        "company_website": website,
                        "title": job_title,
                        "snippet": f"Hiring signal from {self._safe_str(job.get('source') or 'job board')}: {job_title}",
                        "location": location_value,
                        "detected_location": location_value,
                        "intent_signal": "hiring",
                        "job_posted_date": posted_date,
                        "discovered_at": discovered_day,
                        "services_scanned": services,
                        "tech_stack": tech_stack,
                        "decision_maker": decision,
                        "company_signals": company_signals,
                    },
                )

                score_card = await lead_service.calculate_lead_score(
                    lead=candidate_lead,
                    company_profile=company_profile,
                    service_hints=services,
                )
                total_score = int(score_card.get("total_score", 0) or 0)
                if total_score < 40:
                    continue

                candidate_lead.company_fit_score = round(
                    float(score_card.get("breakdown", {}).get("service_fit", 0)) / 30.0,
                    4,
                )
                candidate_lead.signal_score = max(
                    float(candidate_lead.signal_score or 0.0),
                    round(float(total_score) / 100.0, 4),
                )

                candidate_lead.raw_data = candidate_lead.raw_data or {}
                candidate_lead.raw_data["score_card"] = score_card
                candidate_lead.raw_data["final_score_100"] = total_score
                candidate_lead.raw_data["final_score"] = round(float(total_score) / 100.0, 4)
                candidate_lead.raw_data["recommended_action"] = score_card.get("recommended_action")
                candidate_lead.raw_data["is_hot_lead"] = bool(score_card.get("is_hot_lead"))

                candidate_lead.save()
                new_leads_found += 1
                if total_score >= 70:
                    hot_leads += 1

                if domain:
                    seen_domains.add(domain)
                if company_key:
                    seen_companies.add(company_key)

            summary["new_leads_found"] = new_leads_found
            summary["hot_leads"] = hot_leads
            summary["scan_duration_seconds"] = round(time.perf_counter() - start_ts, 2)
            return summary

        except Exception as e:
            summary["scan_duration_seconds"] = round(time.perf_counter() - start_ts, 2)
            summary["error"] = str(e)
            print(f"[INTENT MONITOR] run_daily_scan failed for user={uid}: {e}")
            return summary
        finally:
            await self._update_runtime(
                uid,
                {
                    "status": "complete",
                    "completed_at": datetime.utcnow(),
                    "summary": summary,
                    "scan_id": active_scan_id,
                },
            )

            profile = self._profile_by_owner(uid)
            if profile:
                try:
                    profile.intent_scan_last_run = datetime.utcnow()
                    profile.intent_scan_last_summary = summary
                    profile.intent_scan_status = "complete"
                    profile.intent_scan_id = active_scan_id
                    profile.save()
                except Exception as e:
                    print(f"[INTENT MONITOR] Failed to persist scan summary: {e}")


intent_monitor_service = IntentMonitorService()
