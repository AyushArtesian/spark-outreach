"""
Service for lead operations using MongoDB
"""
from typing import List, Optional, Dict, Any, Set, Tuple
import asyncio
from app.models.lead import Lead
from app.models.company import CompanyProfile
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.embeddings import embedding_service
from app.services.web_scraper import _normalize_location_text, analyze_business_signals
from app.services.apollo_service import apollo_service
from app.services.service_catalog import infer_services_from_text
from datetime import datetime, timedelta
from bson import ObjectId
from urllib.parse import urlparse
import re
import hashlib


NEARBY_LOCATION_HINTS = {
    "mohali": [
        "sahibzada ajit singh nagar",
        "sas nagar",
        "chandigarh",
        "panchkula",
        "zirakpur",
        "kharar",
    ],
    "chandigarh": ["mohali", "panchkula", "zirakpur", "kharar"],
    "gurgaon": ["gurugram", "delhi", "new delhi", "noida", "faridabad", "manesar", "sohna"],
    "gurugram": ["gurgaon", "delhi", "new delhi", "noida", "faridabad", "manesar", "sohna"],
    "bangalore": ["bengaluru", "electronic city", "whitefield"],
    "bengaluru": ["bangalore", "electronic city", "whitefield"],
    "pune": ["hinjewadi", "wakad", "baner"],
    "hyderabad": ["hitech city", "gachibowli", "secunderabad"],
    "delhi": ["new delhi", "noida", "gurgaon", "gurugram", "faridabad"],
    "new delhi": ["delhi", "noida", "gurgaon", "gurugram", "faridabad"],
}

class LeadService:
    """Service for lead-related operations with MongoDB"""

    @staticmethod
    def _as_service_list(value: Any) -> List[str]:
        """Convert service filters to a clean string list."""
        if not value:
            return []
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, (list, tuple, set)):
            items = [str(item) for item in value]
        else:
            items = [str(value)]

        cleaned: List[str] = []
        seen: Set[str] = set()
        for item in items:
            normalized = re.sub(r"\s+", " ", str(item).strip())
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(normalized)
        return cleaned

    @staticmethod
    def _extract_service_candidates(
        service_focus: Any,
        company_services: Optional[List[str]],
        query: str,
        limit: int = 3,
    ) -> List[str]:
        """Pick top service candidates for intent-focused SERP query building."""
        candidates: List[str] = []
        seen: Set[str] = set()

        def _add_service(raw_service: str) -> None:
            service = re.sub(r"\s+", " ", str(raw_service).strip())
            if not service:
                return
            key = service.lower()
            if key in seen:
                return
            seen.add(key)
            candidates.append(service)

        for service in LeadService._as_service_list(service_focus):
            _add_service(service)
            if len(candidates) >= limit:
                return candidates

        for service in LeadService._as_service_list(company_services or []):
            _add_service(service)
            if len(candidates) >= limit:
                return candidates

        inferred_services = infer_services_from_text(query, limit=limit)
        for label in inferred_services:
            _add_service(label)
            if len(candidates) >= limit:
                return candidates

        if not candidates:
            _add_service("Custom software development")

        return candidates[:limit]

    @staticmethod
    def _append_current_year(query: str, year: int) -> str:
        """Append current year if it is not already present."""
        compact = re.sub(r"\s+", " ", str(query or "").strip())
        if not compact:
            return ""
        if re.search(rf"\b{year}\b", compact):
            return compact
        return f"{compact} {year}"

    @staticmethod
    def _resolve_search_industry(industry: Optional[str], query: str) -> Optional[str]:
        """Resolve industry from filters first, then infer from query text."""
        value = str(industry or "").strip().lower()
        if value and value != "all":
            return value

        query_lower = str(query or "").lower()
        industry_keywords = {
            "e-commerce": ["e-commerce", "ecommerce", "e commerce", "retail", "marketplace", "shopping"],
            "saas": ["saas", "software-as-a-service", "subscription"],
            "fintech": ["fintech", "finance", "banking", "payments", "crypto"],
            "healthcare": ["healthcare", "health", "medical", "pharma", "biotech"],
            "edtech": ["edtech", "education", "learning", "training"],
            "proptech": ["proptech", "real estate", "property"],
            "logistics": ["logistics", "supply chain", "shipping", "delivery"],
            "manufacturing": ["manufacturing", "industrial", "factory"],
            "travel": ["travel", "tourism", "hospitality"],
            "gaming": ["game", "gaming", "esports"],
        }
        for industry_name, keywords in industry_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return industry_name

        return None

    @staticmethod
    def _build_search_key(
        location: Optional[str],
        industry: Optional[str],
        service_focus: Any,
        query: str,
    ) -> str:
        """Build a stable signature for current search intent."""
        services_key = "|".join(
            sorted([str(s).strip().lower() for s in LeadService._as_service_list(service_focus) if str(s).strip()])
        )
        search_seed = (
            f"{str(location or '').strip().lower()}|"
            f"{str(industry or '').strip().lower()}|"
            f"{services_key}|"
            f"{str(query or '').strip().lower()}"
        )
        return hashlib.md5(search_seed.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _ensure_negative_filters(query: str) -> str:
        """Ensure common job-page exclusions are always present in SERP queries."""
        compact = re.sub(r"\s+", " ", str(query or "").strip())
        if not compact:
            return ""

        has_jobs = bool(re.search(r"(?:^|\s)-jobs(?:\s|$)", compact))
        has_careers = bool(re.search(r"(?:^|\s)-careers(?:\s|$)", compact))
        suffix: List[str] = []
        if not has_jobs:
            suffix.append("-jobs")
        if not has_careers:
            suffix.append("-careers")
        if not suffix:
            return compact
        return f"{compact} {' '.join(suffix)}"

    @staticmethod
    def _build_buyer_intent_serp_queries(
        service_focus: Any,
        company_services: Optional[List[str]],
        location: Optional[str],
        target_locations: Optional[List[str]],
        query: str,
        max_queries: int = 10,
    ) -> List[str]:
        """Build high-intent, buyer-focused SERP queries for lead discovery."""
        location_text = _normalize_location_text(str(location or "").strip()) or str(location or "").strip()
        if not location_text and target_locations:
            location_text = (
                _normalize_location_text(str(target_locations[0]).strip())
                or str(target_locations[0]).strip()
            )
        if not location_text:
            location_text = "India"

        services = LeadService._extract_service_candidates(
            service_focus=service_focus,
            company_services=company_services,
            query=query,
            limit=3,
        )

        current_year = datetime.utcnow().year
        queries: List[str] = []
        seen: Set[str] = set()

        for service in services:
            base_patterns = [
                f'"hire {service} developer" OR "looking for {service}" {location_text}',
                f'"{service} implementation partner" {location_text}',
                f'"{service} consultant" "contact us" "get a quote" {location_text}',
                f'intitle:"{service}" "request a demo" OR "get a quote" {location_text}',
                f'"{service}" "digital transformation" "implementation partner" {location_text} company',
            ]

            service_lower = service.lower()
            if any(token in service_lower for token in ["power apps", "power platform", "power automate"]):
                base_patterns.extend(
                    [
                        f'"Microsoft Power Platform" "implementation partner" {location_text}',
                        f'"Power Apps" "Power Automate" services "get a quote" {location_text}',
                    ]
                )

            if any(
                token in service_lower
                for token in ["ecommerce", "e-commerce", "shopify", "woocommerce", "magento"]
            ):
                base_patterns.extend(
                    [
                        f'"Shopify development" agency "get a quote" {location_text}',
                        f'"WooCommerce" OR "Magento" development company "implementation partner" {location_text}',
                    ]
                )

            for pattern in base_patterns:
                enriched = LeadService._append_current_year(pattern, current_year)
                enriched = LeadService._ensure_negative_filters(enriched)
                key = enriched.lower()
                if not enriched or key in seen:
                    continue
                seen.add(key)
                queries.append(enriched)
                if len(queries) >= max_queries:
                    return queries

        return queries

    @staticmethod
    def _canonical_domain(value: str) -> str:
        """Normalize URL/domain to a stable root domain for dedupe checks."""
        raw = (value or "").strip().lower()
        if not raw:
            return ""

        if "://" in raw:
            host = (urlparse(raw).netloc or "").lower()
        else:
            host = raw.split("/", 1)[0]

        host = host.split(":", 1)[0].replace("www.", "").replace("m.", "")
        if not host or "." not in host:
            return host

        parts = [p for p in host.split(".") if p]
        if len(parts) <= 2:
            return host

        # Keep 3 labels for domains like example.co.in
        if parts[-2] == "co" and parts[-1] in {"in", "uk", "au", "nz", "jp"}:
            return ".".join(parts[-3:])

        return ".".join(parts[-2:])

    @staticmethod
    def _build_location_scope(
        requested_location: Optional[str],
        target_locations: Optional[List[str]] = None,
    ) -> List[str]:
        """Build normalized location tokens including nearby-city variants."""
        scope: Set[str] = set()

        raw_locations = []
        if requested_location:
            raw_locations.append(str(requested_location))
        if isinstance(target_locations, str):
            if target_locations.strip():
                raw_locations.append(target_locations)
        else:
            raw_locations.extend(str(loc) for loc in (target_locations or []) if str(loc).strip())

        for raw in raw_locations:
            lowered = str(raw).strip().lower()
            if not lowered:
                continue

            normalized = _normalize_location_text(lowered)
            for token in [lowered, normalized]:
                if token:
                    scope.add(token)
                for part in [p.strip() for p in token.split(",") if p.strip()]:
                    scope.add(part)

            nearby = NEARBY_LOCATION_HINTS.get(normalized) or NEARBY_LOCATION_HINTS.get(lowered) or []
            for near in nearby:
                near_norm = _normalize_location_text(near)
                if near_norm:
                    scope.add(near_norm)

        # Remove weak tokens that cause false positives.
        return sorted([token for token in scope if len(token) >= 3])

    @staticmethod
    def _extract_location_hit(text: str, location_scope: List[str]) -> str:
        """Return matched location token from text; empty string if no location hit."""
        if not location_scope:
            return ""

        searchable = _normalize_location_text((text or "").lower())
        if not searchable:
            return ""

        for token in location_scope:
            pattern = rf"\b{re.escape(token)}\b"
            if re.search(pattern, searchable):
                return token

        return ""

    @staticmethod
    def _lead_dedupe_key(lead: Lead) -> str:
        """Build a stable dedupe key for result collapsing."""
        raw = lead.raw_data or {}
        domain = LeadService._canonical_domain(str(raw.get("source_url", "")))
        if domain:
            return f"domain:{domain}"

        company = re.sub(r"\s+", " ", str(lead.company or lead.name or "").strip().lower())
        if company:
            return f"company:{company}"

        return f"lead:{str(lead.id)}"

    @staticmethod
    def _clamp_int(value: float, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, int(round(value))))

    @staticmethod
    def _grade_from_total(total_score: int) -> str:
        if total_score >= 70:
            return "A"
        if total_score >= 50:
            return "B"
        if total_score >= 30:
            return "C"
        return "D"

    @staticmethod
    def _recommended_action(total_score: int) -> str:
        if total_score >= 70:
            return "contact_immediately"
        if total_score >= 50:
            return "add_to_sequence"
        if total_score >= 30:
            return "nurture"
        return "skip"

    @staticmethod
    def _extract_employee_count(raw: Dict[str, Any]) -> Optional[int]:
        candidates = [
            raw.get("employee_count"),
            raw.get("employees"),
            raw.get("company_size"),
            raw.get("apollo_employee_count"),
            raw.get("apollo_num_employees"),
            raw.get("organization_num_employees"),
        ]

        for value in candidates:
            if value is None:
                continue
            if isinstance(value, (int, float)):
                count = int(value)
                if count > 0:
                    return count

            text = str(value).strip().lower()
            if not text:
                continue

            range_match = re.search(r"(\d{1,6})\s*(?:-|to)\s*(\d{1,6})", text)
            if range_match:
                low = int(range_match.group(1))
                high = int(range_match.group(2))
                if high >= low:
                    return (low + high) // 2

            number_match = re.search(r"\d{1,6}", text)
            if number_match:
                return int(number_match.group(0))

        return None

    @staticmethod
    def _score_size_fit(employee_count: Optional[int]) -> int:
        if employee_count is None or employee_count <= 0:
            return 0
        if 50 <= employee_count <= 200:
            return 10
        if 20 <= employee_count < 50 or 200 < employee_count <= 500:
            return 7
        if 500 < employee_count <= 1000:
            return 3
        return 0

    @staticmethod
    def _score_intent(
        raw: Dict[str, Any],
        enriched: Dict[str, Any],
        service_hints: List[str],
    ) -> int:
        source = str(raw.get("source", "")).strip().lower()
        intent_signal = str(raw.get("intent_signal", "")).strip().lower()
        if intent_signal == "hiring" or source.startswith("job_board"):
            return 25

        company_signals = enriched.get("company_signals", {}) if isinstance(enriched, dict) else {}
        searchable = " ".join(
            [
                str(raw.get("snippet", "")),
                str(raw.get("company_summary", "")),
                str(raw.get("title", "")),
                str(company_signals.get("news_snippets", "")),
            ]
        ).lower()

        service_tokens = []
        for service in service_hints:
            service_tokens.extend([token for token in re.split(r"\W+", str(service).lower()) if len(token) >= 3])
        has_service_mention = any(token in searchable for token in set(service_tokens)) if service_tokens else True

        has_rfq = any(
            phrase in searchable
            for phrase in ["request a demo", "get a quote", "rfq", "contact us", "request for proposal"]
        )
        if has_rfq and has_service_mention:
            return 15

        if bool(company_signals.get("recent_funding")):
            return 10

        if bool(company_signals.get("digital_transformation")) or "digital transformation" in searchable:
            return 5

        return 0

    @staticmethod
    def _score_tech_stack(
        enriched: Dict[str, Any],
        service_hints: List[str],
    ) -> int:
        tech = enriched.get("tech_stack", {}) if isinstance(enriched, dict) else {}
        technologies = [str(t).strip().lower() for t in (tech.get("technologies") or []) if str(t).strip()]
        cms = str(tech.get("cms", "")).strip().lower()
        ecommerce_platform = str(tech.get("ecommerce_platform", "")).strip()
        uses_microsoft_stack = bool(tech.get("uses_microsoft_stack", False))
        fallback_text = " ".join(
            [
                " ".join([str(t).strip().lower() for t in (tech.get("technologies") or []) if str(t).strip()]),
                str(tech.get("cms", "")).strip().lower(),
                str(tech.get("ecommerce_platform", "")).strip().lower(),
            ]
        ).strip()

        service_text = " ".join([str(s).strip().lower() for s in service_hints if str(s).strip()])
        power_apps_focus = any(token in service_text for token in ["power apps", "power platform", "power automate", "dynamics"])
        ecommerce_focus = any(token in service_text for token in ["ecommerce", "e-commerce", "shopify", "woocommerce", "magento"])

        if power_apps_focus and uses_microsoft_stack:
            return 20
        if ecommerce_focus and ecommerce_platform:
            return 20

        service_tokens = [token for token in re.split(r"\W+", service_text) if len(token) >= 3]
        tech_tokens = set(technologies)
        if cms:
            tech_tokens.add(cms)
        if ecommerce_platform:
            tech_tokens.add(ecommerce_platform.lower())

        overlap_hits = 0
        for token in set(service_tokens):
            if any(token in candidate for candidate in tech_tokens):
                overlap_hits += 1
            elif token in fallback_text:
                overlap_hits += 1

        if overlap_hits >= 2:
            return 20
        if overlap_hits == 1 or uses_microsoft_stack or bool(ecommerce_platform):
            return 10
        return 0

    @staticmethod
    def _score_contact_availability(raw: Dict[str, Any], enriched: Dict[str, Any]) -> int:
        decision = enriched.get("decision_maker", {}) if isinstance(enriched, dict) else {}
        tech = enriched.get("tech_stack", {}) if isinstance(enriched, dict) else {}

        name = str(decision.get("name", "")).strip()
        title = str(decision.get("title", "")).strip()
        email = str(decision.get("email", "")).strip() or str(raw.get("company_email", "")).strip()
        has_contact_form = bool(decision.get("has_contact_form", False) or tech.get("has_contact_form", False))

        if name and email and (title or name):
            return 15
        if email:
            return 8
        if has_contact_form:
            return 4
        return 0

    async def calculate_lead_score(
        self,
        lead: Lead,
        company_profile: Optional[CompanyProfile] = None,
        service_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Calculate transparent 0-100 lead score with weighted component breakdown."""
        raw = lead.raw_data or {}
        enriched = lead.enriched_data if isinstance(lead.enriched_data, dict) else {}
        service_candidates = self._as_service_list(service_hints or raw.get("service_focus") or [])
        if not service_candidates and company_profile and company_profile.services:
            service_candidates = self._as_service_list(company_profile.services)

        # 1) Service fit (0-30) based on existing embedding infrastructure.
        similarity = float(lead.company_fit_score or 0.0)
        if company_profile and company_profile.company_embeddings and lead.lead_embedding:
            try:
                similarities = await embedding_service.similarity_search(
                    company_profile.company_embeddings,
                    [lead.lead_embedding],
                    top_k=1,
                )
                if similarities:
                    similarity = float(similarities[0][1] or 0.0)
            except Exception as e:
                print(f"[LEAD SCORE] Similarity calculation failed for {lead.company}: {e}")

        similarity = max(0.0, min(1.0, similarity))
        service_fit_score = self._clamp_int(similarity * 30.0, 0, 30)

        # 2) Intent score (0-25).
        intent_score = self._clamp_int(
            self._score_intent(raw=raw, enriched=enriched, service_hints=service_candidates),
            0,
            25,
        )

        # 3) Tech stack match (0-20).
        tech_stack_score = self._clamp_int(
            self._score_tech_stack(enriched=enriched, service_hints=service_candidates),
            0,
            20,
        )

        # 4) Contact availability (0-15).
        contact_score = self._clamp_int(
            self._score_contact_availability(raw=raw, enriched=enriched),
            0,
            15,
        )

        # 5) Company size fit (0-10).
        employee_count = self._extract_employee_count(raw)
        size_fit_score = self._clamp_int(self._score_size_fit(employee_count), 0, 10)

        total_score = self._clamp_int(
            service_fit_score + intent_score + tech_stack_score + contact_score + size_fit_score,
            0,
            100,
        )
        grade = self._grade_from_total(total_score)
        recommended_action = self._recommended_action(total_score)

        return {
            "total_score": total_score,
            "grade": grade,
            "breakdown": {
                "service_fit": service_fit_score,
                "intent_score": intent_score,
                "tech_stack": tech_stack_score,
                "contact_availability": contact_score,
                "size_fit": size_fit_score,
            },
            "is_hot_lead": total_score >= 70,
            "recommended_action": recommended_action,
        }
    
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

    @staticmethod
    def _get_or_create_default_campaign(owner_id: str):
        """Get first campaign for owner or create one for auto-discovery."""
        from app.models.campaign import Campaign

        campaign = Campaign.objects(owner_id=owner_id).first()
        if campaign:
            return campaign

        campaign = Campaign(
            owner_id=owner_id,
            title="Auto Discovery Campaign",
            description="Auto-generated campaign for lead discovery",
            content="Automatically discovered prospects",
            target_audience="Potential B2B clients",
            status="active",
        )
        campaign.save()
        return campaign

    async def _discover_and_seed_leads(
        self,
        owner_id: str,
        query: str,
        filters: Optional[Dict[str, Any]],
        company_profile: Optional[CompanyProfile],
        max_results: int = 20,
    ) -> int:
        """Discover lead websites from search and persist as lead records."""
        from app.services.web_scraper import (
            discover_company_websites,
            fetch_company_profile_snapshot,
            fetch_company_website_context,
        )

        industry = filters.get("industry") if filters else None
        raw_location = filters.get("location") if filters else None
        location = (
            _normalize_location_text(str(raw_location).strip())
            if raw_location and str(raw_location).strip()
            else None
        )
        
        # Resolve industry using explicit filter first, then deterministic inference.
        industry = self._resolve_search_industry(industry=industry, query=query)
        service_focus = filters.get("services") if filters else None
        company_sizes = filters.get("company_sizes") if filters else None

        company_services = company_profile.services if company_profile and company_profile.services else []
        company_tech = company_profile.technologies if company_profile and company_profile.technologies else []
        company_expertise = company_profile.expertise_areas if company_profile and company_profile.expertise_areas else []
        target_locations = company_profile.target_locations if company_profile and company_profile.target_locations else []
        location_scope = self._build_location_scope(location, target_locations)
        context_keywords = [*company_services, *company_tech, *company_expertise]

        planner_meta: Dict[str, Any] = {
            "planner": "heuristic",
            "strategy": "Deterministic query templates",
            "model": "heuristic",
            "quality_summary": {},
            "planned_queries_count": 0,
            "retrieved_context_count": 0,
        }
        planned_queries: List[str] = []

        if company_profile:
            company_profile_payload = {
                "company_name": company_profile.company_name,
                "company_description": company_profile.company_description,
                "company_narrative": company_profile.company_narrative,
                "services": company_services,
                "technologies": company_tech,
                "expertise_areas": company_expertise,
                "target_industries": company_profile.target_industries or [],
                "target_locations": target_locations,
            }

            retrieved_context_chunks: List[str] = []
            try:
                from app.services.company_service import CompanyService

                retrieval = await CompanyService.query_company_profile(
                    owner_id=owner_id,
                    query=query,
                    top_k=5,
                )
                retrieved_context_chunks = [
                    str(item.get("chunk", "")).strip()
                    for item in retrieval.get("results", [])
                    if str(item.get("chunk", "")).strip()
                ]
                print(
                    "[LEAD QUERY PLANNER] "
                    f"owner={owner_id} retrieved_context_chunks={len(retrieved_context_chunks)}"
                )
            except Exception as e:
                print(f"Company retrieval for query planner failed: {e}")

            try:
                from app.services.ai_service import ai_service

                planner_output = await ai_service.plan_lead_discovery_queries(
                    user_query=query,
                    filters={
                        "location": location,
                        "industry": industry,
                        "services": service_focus or company_services,
                        "target_locations": target_locations,
                    },
                    company_profile=company_profile_payload,
                    retrieved_context=retrieved_context_chunks,
                    max_queries=10,
                )
                planned_queries = [
                    str(q).strip() for q in planner_output.get("queries", []) if str(q).strip()
                ]
                planner_meta = {
                    "planner": planner_output.get("planner", "heuristic"),
                    "strategy": planner_output.get("strategy", ""),
                    "model": planner_output.get("model", "heuristic"),
                    "quality_summary": planner_output.get("quality_summary", {}),
                    "planned_queries_count": len(planned_queries),
                    "retrieved_context_count": len(retrieved_context_chunks),
                }
                print(
                    "[LEAD QUERY PLANNER] "
                    f"owner={owner_id} planner={planner_meta['planner']} "
                    f"model={planner_meta['model']} "
                    f"planned_queries={len(planned_queries)}"
                )
                quality_summary = planner_meta.get("quality_summary") or {}
                if quality_summary:
                    print(
                        "[LEAD QUERY PLANNER] "
                        f"quality_selected={quality_summary.get('selected_count', 0)} "
                        f"quality_avg_score={quality_summary.get('avg_score', 0.0)}"
                    )
                if planner_meta.get("strategy"):
                    print(f"[LEAD QUERY PLANNER] strategy={str(planner_meta['strategy'])[:220]}")
            except Exception as e:
                print(f"Lead query planning failed: {e}")

        intent_queries = self._build_buyer_intent_serp_queries(
            service_focus=service_focus,
            company_services=company_services,
            location=location,
            target_locations=target_locations,
            query=query,
            max_queries=10,
        )
        if intent_queries:
            planned_queries = intent_queries
            planner_meta.update(
                {
                    "planner": "intent_serp_templates",
                    "model": "deterministic",
                    "strategy": "Buyer-intent SERP patterns with yearly freshness",
                    "planned_queries_count": len(planned_queries),
                }
            )
            print(
                "[LEAD QUERY PLANNER] "
                f"using_intent_templates planned_queries={len(planned_queries)}"
            )
            for idx, candidate in enumerate(planned_queries[:5], 1):
                print(f"[LEAD QUERY PLANNER] intent_query_{idx}: {candidate}")

        if not planned_queries:
            print("[LEAD QUERY PLANNER] Using heuristic query generation fallback.")

        apollo_discovered: List[Dict[str, Any]] = []
        apollo_credit_exhausted = False
        if apollo_service.enabled:
            try:
                apollo_discovered = await apollo_service.search_people(
                    query=query,
                    location=location,
                    industry=industry,
                    service_focus=service_focus or company_services,
                    company_sizes=company_sizes,
                    max_results=max_results,
                )
                apollo_credit_exhausted = bool(getattr(apollo_service, "last_run_credit_exhausted", False))
            except Exception as e:
                print(f"[APOLLO] Discovery failed: {e}")
        else:
            print("[APOLLO] APOLLO_API_KEY missing; skipping Apollo people discovery.")

        web_discovered: List[Dict[str, Any]] = []
        apollo_only_mode = bool(apollo_service.enabled and not apollo_credit_exhausted)
        if apollo_only_mode:
            if apollo_discovered:
                print(
                    "[LEAD DISCOVERY SOURCES] "
                    "Apollo-only mode active. Skipping SerpAPI fallback."
                )
            else:
                print(
                    "[LEAD DISCOVERY SOURCES] "
                    "Apollo-only mode active but Apollo returned 0 results. "
                    "Skipping SerpAPI fallback by request."
                )
        else:
            if apollo_service.enabled and apollo_credit_exhausted:
                print(
                    "[LEAD DISCOVERY SOURCES] "
                    "Apollo credits exhausted. Enabling SerpAPI/web fallback for this search."
                )
            web_limit = max(5, int(max_results))
            web_discovered = await discover_company_websites(
                query=query,
                location=location,
                industry=industry,
                service_focus=service_focus or company_services,
                target_locations=target_locations,
                context_keywords=context_keywords,
                planned_queries=planned_queries,
                max_results=web_limit,
            )

        jobboard_discovered: List[Dict[str, Any]] = []
        try:
            from app.services.jobboard_service import jobboard_service

            jobboard_services = self._extract_service_candidates(
                service_focus=service_focus,
                company_services=company_services,
                query=query,
                limit=2,
            )
            jobboard_locations: List[str] = []
            if location:
                jobboard_locations.append(str(location))
            for loc in target_locations or []:
                normalized = str(loc).strip()
                if normalized and normalized.lower() not in [l.lower() for l in jobboard_locations]:
                    jobboard_locations.append(normalized)
            if not jobboard_locations:
                jobboard_locations = ["India"]

            print(
                "[JOBBOARD] "
                f"starting additive discovery services={len(jobboard_services)} "
                f"locations={len(jobboard_locations[:1])} timeout=25s"
            )

            discovered_jobs: List[Dict[str, Any]] = []
            try:
                discovered_jobs = await asyncio.wait_for(
                    jobboard_service.run_intent_discovery(
                        services=jobboard_services,
                        locations=jobboard_locations[:1],
                    ),
                    timeout=25.0,
                )
            except asyncio.TimeoutError:
                print("[JOBBOARD] Additive discovery timed out after 25s; continuing without job-board results.")
                discovered_jobs = []

            for job in discovered_jobs:
                company_website = str(job.get("company_website") or "").strip()
                domain = self._canonical_domain(company_website)
                company_name = str(job.get("company_name") or "").strip()
                posting_title = str(job.get("job_title") or "").strip()
                posting_location = str(job.get("location") or "").strip()
                if not company_name or not posting_title:
                    continue

                jobboard_discovered.append(
                    {
                        "source": "job_board",
                        "name": company_name,
                        "company": company_name,
                        "email": "",
                        "phone": "",
                        "job_title": posting_title,
                        "industry": industry,
                        "url": company_website,
                        "domain": domain,
                        "title": posting_title,
                        "snippet": f"Active hiring signal: {posting_title} in {posting_location or location or 'target location'}",
                        "location": posting_location,
                        "intent_signal": "hiring",
                        "posted_date": str(job.get("posted_date") or ""),
                        "apollo_person_id": "",
                        "apollo_organization_id": "",
                        "linkedin_url": "",
                        "email_status": "",
                    }
                )
        except Exception as e:
            print(f"[JOBBOARD] Discovery failed: {e}")

        if apollo_only_mode:
            discovered = [*apollo_discovered, *jobboard_discovered]
        else:
            discovered = [*apollo_discovered, *web_discovered, *jobboard_discovered]
        print(
            "[LEAD DISCOVERY SOURCES] "
            f"apollo={len(apollo_discovered)} web={len(web_discovered)} "
            f"jobboard={len(jobboard_discovered)} total_candidates={len(discovered)}"
        )
        if not discovered:
            return 0

        # Signature for this specific search intent (location/industry/services/query)
        search_key = self._build_search_key(
            location=location,
            industry=industry,
            service_focus=service_focus or [],
            query=query,
        )

        campaign = self._get_or_create_default_campaign(owner_id)
        from app.models.campaign import Campaign
        owner_campaign_ids = [str(c.id) for c in Campaign.objects(owner_id=owner_id)]
        existing = Lead.objects(campaign_id__in=owner_campaign_ids)
        existing_domain_keys = set()
        existing_contact_keys = set()
        for lead in existing:
            source_url = (lead.raw_data or {}).get("source_url", "") if lead.raw_data else ""
            domain = self._canonical_domain(source_url)
            if domain:
                existing_domain_keys.add(domain)
            email_key = str(lead.email or "").strip().lower()
            if email_key:
                existing_contact_keys.add(email_key)
            apollo_person_id = str((lead.raw_data or {}).get("apollo_person_id", "") or "").strip()
            if apollo_person_id:
                existing_contact_keys.add(f"apollo:{apollo_person_id}")

        created_count = 0
        skipped_duplicate = 0
        skipped_empty_domain = 0
        skipped_low_quality = 0
        skipped_no_signal = 0
        skipped_location_mismatch = 0
        for item in discovered:
            item_source = str(item.get("source") or "web_discovery").strip().lower()
            domain = self._canonical_domain(item.get("domain") or item.get("url") or item.get("company_website") or "")
            apollo_person_id = str(item.get("apollo_person_id") or "").strip()
            item_email = str(item.get("email") or "").strip().lower()
            contact_key = item_email if item_email else (f"apollo:{apollo_person_id}" if apollo_person_id else "")

            if not domain and not contact_key:
                skipped_empty_domain += 1
                continue

            if domain and domain in existing_domain_keys:
                skipped_duplicate += 1
                continue
            if contact_key and contact_key in existing_contact_keys:
                skipped_duplicate += 1
                continue

            company_name = (
                str(item.get("company") or item.get("name") or (domain.split(".")[0].title() if domain else "Unknown"))
            ).strip()
            lead_name = str(item.get("name") or company_name).strip()
            email = item_email or (f"contact@{domain}" if domain else f"unknown+{apollo_person_id[:8] or 'lead'}@apollo.local")
            phone = str(item.get("phone") or "").strip()
            snippet = (item.get("snippet") or "").lower()

            # Enforce strict location scope (requested location + nearby aliases)
            quick_location_text = " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("snippet", "")),
                    str(item.get("location", "")),
                    str(item.get("company", "")),
                    str(item.get("url", "")),
                ]
            )
            detected_location = self._extract_location_hit(quick_location_text, location_scope)

            # Apollo already applies organization/person location filters at source.
            # If Apollo result omits explicit city fields, retain requested city as inferred match.
            if item_source.startswith("apollo") and location_scope and not detected_location:
                inferred = _normalize_location_text(str(location or "").strip().lower())
                if inferred and inferred in location_scope:
                    detected_location = inferred
            if item_source.startswith("job_board") and location_scope and not detected_location:
                inferred = _normalize_location_text(str(item.get("location") or location or "").strip().lower())
                if inferred and inferred in location_scope:
                    detected_location = inferred

            if item_source.startswith("apollo"):
                snapshot = {
                    "company_name": str(item.get("company") or company_name),
                    "email": item_email,
                    "phone": phone,
                    "summary": str(item.get("snippet") or ""),
                }
            else:
                snapshot = await fetch_company_profile_snapshot(item.get("url", ""))

            if location_scope and not detected_location:
                detailed_location_text = " ".join(
                    [
                        quick_location_text,
                        str(snapshot.get("summary", "")),
                    ]
                )
                detected_location = self._extract_location_hit(detailed_location_text, location_scope)
                # For web-discovered leads, if no explicit location match but location was requested,
                # infer the location from the requested search parameter (user requested London → lead is London-relevant)
                if not detected_location and item_source == "web_discovery" and location:
                    inferred_location = _normalize_location_text(str(location or "").strip().lower())
                    if inferred_location and inferred_location in location_scope:
                        detected_location = inferred_location
                
                if not detected_location:
                    skipped_location_mismatch += 1
                    continue

            if snapshot.get("company_name"):
                company_name = snapshot["company_name"]
            if snapshot.get("email"):
                email = snapshot["email"]
            if snapshot.get("phone"):
                phone = snapshot["phone"]

            summary_text = (snapshot.get("summary") or "").lower()
            combined_quality_text = f"{company_name.lower()} {snippet} {summary_text}"
            if any(
                token in combined_quality_text
                for token in [
                    "top 10", "top 50", "top 100", "list of", "to work for",
                    "salary", "rankings", "directory", "compare",
                ]
            ):
                skipped_low_quality += 1
                continue

            website_text = summary_text
            if not item_source.startswith("apollo") and len(website_text) < 180:
                extra_context = await fetch_company_website_context(item.get("url", ""))
                if extra_context:
                    website_text = f"{website_text} {extra_context}".strip()

            signal_layer = analyze_business_signals(
                snippet=item.get("snippet", ""),
                website_text=website_text,
                service_focus=service_focus,
                search_query=query,
            )
            signal_confidence = float(signal_layer.get("confidence", 0.0) or 0.0)
            signal_keywords = list(signal_layer.get("signals", []))
            signal_reasons = list(signal_layer.get("reason", []))
            tech_relevance = float(signal_layer.get("tech_relevance", 0.0) or 0.0)

            min_signal_gate = 0.12 if item_source.startswith("apollo") else 0.18
            if signal_confidence < min_signal_gate and tech_relevance < min_signal_gate:
                skipped_no_signal += 1
                print(
                    f"Skipping {domain or contact_key}: "
                    f"signal_confidence={signal_confidence:.2f}, tech_relevance={tech_relevance:.2f}, "
                    f"signals={signal_keywords}"
                )
                continue

            # Quality scoring to keep only profile-like company leads
            quality_score = 0.0
            if item_source.startswith("apollo"):
                quality_score += 0.25
            if item_source.startswith("job_board"):
                quality_score += 0.24
            if apollo_person_id:
                quality_score += 0.10
            if str(item.get("job_title") or "").strip():
                quality_score += 0.12
            if str(item.get("intent_signal") or "").strip().lower() == "hiring":
                quality_score += 0.20
            if str(item.get("linkedin_url") or "").strip():
                quality_score += 0.08
            if snapshot.get("company_name") and len(snapshot.get("company_name", "")) > 3:
                quality_score += 0.35
            if snapshot.get("email"):
                quality_score += 0.30
            if snapshot.get("phone"):
                quality_score += 0.15
            if snapshot.get("summary") and len(snapshot.get("summary", "")) > 80:
                quality_score += 0.20

            # Search-result quality signals for cases where homepage blocks scraping (e.g. 403)
            snippet_tokens = [t for t in re.split(r"\W+", snippet) if len(t) >= 3]
            if len(snippet_tokens) >= 8:
                quality_score += 0.12
            if any(tok in snippet for tok in ["services", "solutions", "platform", "software", "consulting", "development"]):
                quality_score += 0.10
            if domain.endswith(".com") or domain.endswith(".in") or domain.endswith(".io"):
                quality_score += 0.08

            low_name_tokens = ["top", "best", "list", "jobs", "companies", "startup", "startups", "based", "2025", "2026"]
            if any(token in company_name.lower() for token in low_name_tokens):
                quality_score -= 0.25
            if re.match(r"^\d+\s", company_name.strip().lower()):
                quality_score -= 0.2

            quality_score = max(0.0, min(1.0, quality_score))
            has_snapshot = bool(snapshot.get("email") or snapshot.get("phone") or snapshot.get("summary"))
            min_quality = 0.40 if has_snapshot else 0.32
            if item_source.startswith("apollo"):
                min_quality = 0.36
            if quality_score < min_quality:
                # Allow only moderate exceptions when strong business signals are present.
                if not has_snapshot and quality_score >= 0.26 and signal_confidence >= 0.45:
                    pass
                else:
                    skipped_low_quality += 1
                    continue

            # Basic relevance gate from service focus + company context keywords
            weighted_keywords = [
                *(service_focus or []),
                *company_services,
                *company_tech,
                *company_expertise,
            ]
            weighted_keywords = [str(k).strip().lower() for k in weighted_keywords if str(k).strip()]
            keyword_hits = [k for k in weighted_keywords if k in snippet]
            relevance_hint = min(1.0, 0.2 + (0.08 * len(set(keyword_hits)))) if weighted_keywords else 0.3

            # Soft service matching: do not hard-skip, only adjust relevance when no service tokens appear.
            if service_focus:
                focus_tokens = []
                for service in service_focus:
                    focus_tokens.extend([t for t in re.split(r"\W+", str(service).lower()) if len(t) >= 2])
                token_hits = [t for t in set(focus_tokens) if t in snippet]
                if token_hits:
                    relevance_hint = min(1.0, relevance_hint + 0.15)
                else:
                    relevance_hint = max(0.15, relevance_hint - 0.05)

            enrichment_payload: Dict[str, Any] = {}
            try:
                from app.services.enrichment_service import enrichment_service

                enrichment_payload = await enrichment_service.enrich_lead(
                    {
                        "company_name": company_name,
                        "company_website": item.get("url", "") or item.get("company_website", ""),
                        "source_url": item.get("url", "") or item.get("company_website", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item_source,
                    }
                )
            except Exception as e:
                print(f"Lead enrichment failed for {company_name}: {e}")

            lead = Lead(
                campaign_id=str(campaign.id),
                name=lead_name,
                email=email,
                company=company_name,
                phone=phone,
                job_title=str(item.get("job_title") or "Hiring Team"),
                industry=(
                    str(item.get("industry") or industry)
                    if (item.get("industry") or (industry and str(industry).lower() != "all"))
                    else None
                ),
                status="new",
                signal_keywords=signal_keywords,
                signal_score=signal_confidence,
                enriched_data={
                    "tech_stack": enrichment_payload.get("tech_stack", {}),
                    "decision_maker": enrichment_payload.get("decision_maker", {}),
                    "company_signals": enrichment_payload.get("company_signals", {}),
                    "enriched_at": enrichment_payload.get("enriched_at", ""),
                },
                raw_data={
                    "source": item_source,
                    "source_url": item.get("url", "") or item.get("company_website", ""),
                    "company_website": item.get("url", "") or item.get("company_website", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "query": query,
                    "location": detected_location or "",
                    "detected_location": detected_location or "",
                    "requested_location": location,
                    "location_scope": location_scope,
                    "search_key": search_key,
                    "service_focus": service_focus or [],
                    "context_keyword_hits": list(set(keyword_hits)),
                    "query_planner": planner_meta,
                    "planned_search_queries": planned_queries,
                    "discovery_relevance_hint": relevance_hint,
                    "company_summary": snapshot.get("summary", ""),
                    "company_email": snapshot.get("email", ""),
                    "company_phone": snapshot.get("phone", ""),
                    "discovery_quality_score": quality_score,
                    "discovery_signals": signal_keywords,
                    "signal_confidence": signal_confidence,
                    "signal_reasons": signal_reasons,
                    "tech_relevance": tech_relevance,
                    "intent_signal": str(item.get("intent_signal") or ""),
                    "job_posted_date": str(item.get("posted_date") or ""),
                    "employee_count": item.get("employee_count"),
                    "tech_stack": enrichment_payload.get("tech_stack", {}),
                    "decision_maker": enrichment_payload.get("decision_maker", {}),
                    "company_signals": enrichment_payload.get("company_signals", {}),
                    "apollo_person_id": apollo_person_id,
                    "apollo_organization_id": str(item.get("apollo_organization_id") or ""),
                    "apollo_email_status": str(item.get("email_status") or ""),
                    "apollo_linkedin_url": str(item.get("linkedin_url") or ""),
                },
            )
            lead.save()

            if company_profile:
                await self.enrich_lead_profile(lead, company_profile)

            if domain:
                existing_domain_keys.add(domain)
            if contact_key:
                existing_contact_keys.add(contact_key)
            created_count += 1

        print(
            f"Lead discovery summary: owner={owner_id} created={created_count} "
            f"skipped_duplicate={skipped_duplicate} skipped_empty_domain={skipped_empty_domain} "
            f"skipped_location_mismatch={skipped_location_mismatch} "
            f"skipped_low_quality={skipped_low_quality} skipped_no_signal={skipped_no_signal}"
        )
        return created_count

    @staticmethod
    def _lead_matches_search_constraints(
        lead: Lead,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check whether lead satisfies current search constraints (location/industry/services/query)."""
        filters = filters or {}
        lead_raw = lead.raw_data or {}
        source = str(lead_raw.get("source", "")).strip().lower()

        location = (filters.get("location") or "").strip().lower()
        industry = (filters.get("industry") or "").strip().lower()
        services = [str(s).strip().lower() for s in (filters.get("services") or []) if str(s).strip()]

        searchable = " ".join(
            [
                str(lead.name or ""),
                str(lead.company or ""),
                str(lead.job_title or ""),
                str(lead.industry or ""),
                str(lead_raw.get("title", "")),
                str(lead_raw.get("snippet", "")),
                str(lead_raw.get("company_summary", "")),
                str(lead_raw.get("detected_location", "")),
                str(lead_raw.get("source_url", "")),
            ]
        ).lower()

        source_url = str(lead_raw.get("source_url", "")).lower()
        quality_score = float(lead_raw.get("discovery_quality_score", 0.0) or 0.0)
        signal_confidence = float(lead_raw.get("signal_confidence", lead.signal_score or 0.0) or 0.0)
        tech_relevance = float(lead_raw.get("tech_relevance", 0.0) or 0.0)
        low_value_domains = [
            "crunchbase", "tracxn", "g2", "clutch", "goodfirms", "infinityjobs",
            "naukri", "indeed", "timesjobs", "monster", "glassdoor", "justdial",
        ]
        if any(d in source_url for d in low_value_domains):
            return False

        # Enforce minimum quality for discovered web leads
        if source == "web_discovery" and quality_score < 0.30:
            return False

        # Enforce high-intent business signal threshold (relaxed to show more leads)
        if source == "web_discovery" and signal_confidence < 0.10:
            return False
        if source == "web_discovery" and tech_relevance < 0.10:
            return False

        # Reject low-value headline/listing style leads
        low_value_tokens = [
            "top 10", "top 50", "top 100", "list of", "to work for", "jobs in",
            "job openings", "salary", "rankings", "directory", "compare",
        ]
        if any(token in searchable for token in low_value_tokens):
            return False

        if industry and industry != "all" and industry not in searchable:
            return False

        if location:
            location_scope = LeadService._build_location_scope(
                requested_location=location,
                target_locations=filters.get("target_locations") or [],
            )
            location_text = " ".join(
                [
                    str(lead_raw.get("detected_location", "")),
                    str(lead_raw.get("snippet", "")),
                    str(lead_raw.get("company_summary", "")),
                    str(lead_raw.get("source_url", "")),
                    str(lead.company or ""),
                ]
            )
            location_hit = LeadService._extract_location_hit(location_text, location_scope)
            if source == "web_discovery" and not location_hit:
                return False
            if source != "web_discovery" and not location_hit and location not in searchable:
                return False

        if services:
            service_tokens = []
            for service in services:
                service_tokens.extend([t for t in re.split(r"\W+", service) if len(t) >= 2])
            if service_tokens and not any(token in searchable for token in set(service_tokens)):
                return False

        # Soft query check: require at least one meaningful query token hit
        query_tokens = [t.strip().lower() for t in re.split(r"\W+", query or "") if len(t.strip()) >= 4]
        if query_tokens:
            hits = sum(1 for token in set(query_tokens[:12]) if token in searchable)
            if hits == 0:
                return False

        return True

    @staticmethod
    def _is_invalid_embedding(vector: Optional[List[float]], expected_dim: Optional[int] = None) -> bool:
        """Detect missing/zero or dimension-mismatched embeddings."""
        if not vector:
            return True
        if expected_dim and len(vector) != expected_dim:
            return True
        magnitude = sum(v * v for v in vector) ** 0.5
        return magnitude == 0.0
    
    @staticmethod
    async def enrich_lead_profile(lead: Lead, company_profile: Optional[CompanyProfile] = None) -> Lead:
        """
        Enrich lead with embedding, company fit score, and signal detection
        Combines lead data with company profile matching for smart scoring
        """
        # === BUILD RICH LEAD PROFILE TEXT FOR EMBEDDING ===
        # Use not just basic fields but also discovery context
        raw_data = lead.raw_data or {}
        lead_components = [
            lead.name or "",
            lead.company or "",
            lead.job_title or "",
            lead.industry or "",
            raw_data.get("company_summary", ""),
            raw_data.get("snippet", ""),
            ", ".join(raw_data.get("discovery_signals", [])) or "",
        ]
        lead_text = " ".join([str(comp).strip() for comp in lead_components if comp]).strip()
        
        # If we have very sparse text, add discovery keywords too
        if len(lead_text.split()) < 10:
            discovery_keywords = raw_data.get("context_keyword_hits", [])
            if discovery_keywords:
                lead_text += " " + " ".join(discovery_keywords[:10])
        
        # Generate lead embedding using the same model family used in company context (768-dim)
        from app.services.ai_service import generate_embeddings
        lead_embedding = await generate_embeddings(lead_text)
        lead.lead_embedding = lead_embedding
        lead.embeddings = lead_embedding
        
        # If company profile provided, calculate fit score
        if company_profile:
            # Build company description for comparison
            company_text = f"""
Company Name: {company_profile.company_name}
Services: {', '.join(company_profile.services or [])}
Expertise: {', '.join(company_profile.expertise_areas or [])}
Technologies: {', '.join(company_profile.technologies or [])}
Target Industries: {', '.join(company_profile.target_industries or [])}
Target Locations: {', '.join(company_profile.target_locations or [])}
Team Expertise: {', '.join(company_profile.team_expertise or [])}
            """.strip()
            
            company_embedding = lead.lead_embedding  # Reuse the company's stored embedding if available
            if company_profile.company_embeddings:
                company_embedding = company_profile.company_embeddings
            else:
                from app.services.ai_service import generate_embeddings
                company_embedding = await generate_embeddings(company_text)
            
            # Calculate company fit score
            similarities = await embedding_service.similarity_search(
                lead_embedding,
                [company_embedding],
                top_k=1
            )
            
            if similarities:
                lead.company_fit_score = min(1.0, max(0.0, similarities[0][1]))
            else:
                lead.company_fit_score = 0.0
            
            # Detect hiring/funding/growth signals
            signals = LeadService._detect_signals(lead, company_profile)
            lead.signal_keywords = signals.get("keywords", [])
            lead.signal_score = signals.get("score", 0.0)
        
        lead.updated_at = datetime.utcnow()
        lead.save()
        return lead
    
    @staticmethod
    def _detect_signals(lead: Lead, company_profile: CompanyProfile) -> Dict[str, Any]:
        """
        Detect hiring, funding, and growth signals from lead data
        Returns dict with keywords and signal_score (0-1)
        """
        keywords = []
        signal_strength = 0.0
        
        # Build searchable text from lead
        lead_text = f"{lead.name} {lead.company} {lead.job_title} {lead.industry} {lead.company}".lower()
        raw_lead_data = str(lead.raw_data or {}).lower() if lead.raw_data else ""
        enriched_data = str(lead.enriched_data or {}).lower() if lead.enriched_data else ""
        searchable = f"{lead_text} {raw_lead_data} {enriched_data}"
        
        # Hiring signals
        hiring_keywords = [
            "hiring", "recruiting", "recruitment", "staffing", "team expansion",
            "hiring manager", "head of engineering", "cto", "tech lead", "developer",
            "engineers", "joined recently", "new role"
        ]
        for kw in hiring_keywords:
            if kw in searchable:
                keywords.append(f"hiring:{kw}")
                signal_strength += 0.15
        
        # Funding signals
        funding_keywords = [
            "funding", "raised", "series a", "series b", "vc", "venture capital",
            "investment", "investor", "seed round", "angel", "financing", "funded"
        ]
        for kw in funding_keywords:
            if kw in searchable:
                keywords.append(f"funding:{kw}")
                signal_strength += 0.12
        
        # Growth signals
        growth_keywords = [
            "growth", "expansion", "scaling", "new product", "launch", "market",
            "revenue", "customers", "users", "acquisition", "partnership",
            "conference", "speaking", "thought leader"
        ]
        for kw in growth_keywords:
            if kw in searchable:
                keywords.append(f"growth:{kw}")
                signal_strength += 0.08
        
        # Tech stack signals - if company specializes in certain tech, boost score if lead has it
        if company_profile.technologies:
            company_tech = " ".join(company_profile.technologies).lower()
            if company_tech and len(company_tech) > 3:
                # Check if lead company mentions these technologies
                for tech in company_profile.technologies:
                    tech_lower = tech.lower()
                    if tech_lower in searchable:
                        keywords.append(f"tech:{tech}")
                        signal_strength += 0.1
        
        # Merge with discovery signal layer when available.
        lead_raw = lead.raw_data or {}
        discovered_signals = lead_raw.get("discovery_signals", []) if lead_raw else []
        discovered_conf = float(lead_raw.get("signal_confidence", 0.0) or 0.0) if lead_raw else 0.0
        for sig in discovered_signals:
            if sig:
                keywords.append(f"intent:{sig}")
        signal_strength = max(signal_strength, discovered_conf)

        # Cap signal score at 1.0
        signal_strength = min(1.0, signal_strength)
        
        return {
            "keywords": list(set(keywords)),  # Remove duplicates
            "score": signal_strength
        }
    
    async def search_leads_by_company_fit(
        self,
        owner_id: str,
        query: str,
        campaign_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20,
        sort_by: str = "combined"  # "combined", "fit_score", "signal_score", "created_at"
    ) -> List[Lead]:
        """
        Search leads using company fit scoring and growth signals
        sort_by: combined (fit + signals), fit_score, signal_score, or created_at
        """
        from app.services.ai_service import generate_embeddings
        owner_id_str = str(owner_id)

        # Get company profile for the user (support both ObjectId and string owner IDs)
        company_profile = None
        try:
            company_profile = CompanyProfile.objects(owner_id=ObjectId(owner_id_str)).first()
        except Exception:
            company_profile = None
        if not company_profile:
            company_profile = CompanyProfile.objects(owner_id=owner_id_str).first()
        
        # Generate query embedding
        query_embedding = await generate_embeddings(query)
        
        # Get all leads (or filter by campaign)
        campaign_ids = []
        if campaign_id:
            campaign_ids = [campaign_id]
            all_leads = Lead.objects(campaign_id=campaign_id)
        else:
            # Get leads from all campaigns owned by this user
            from app.models.campaign import Campaign
            user_campaigns = Campaign.objects(owner_id=owner_id_str)
            campaign_ids = [str(c.id) for c in user_campaigns]
            all_leads = Lead.objects(campaign_id__in=campaign_ids)

        leads_before = all_leads.count()
        print(f"Lead search: owner={owner_id_str} campaigns={len(campaign_ids)} leads_before={leads_before}")

        # Discover on every search so changed filters/query can pull new leads (dedupe prevents duplicates)
        created = await self._discover_and_seed_leads(
            owner_id=owner_id_str,
            query=query,
            filters=filters,
            company_profile=company_profile,
            max_results=max(10, top_k),
        )
        print(f"Lead discovery: owner={owner_id_str} created={created}")
        if campaign_id:
            all_leads = Lead.objects(campaign_id=campaign_id)
        else:
            from app.models.campaign import Campaign
            user_campaigns = Campaign.objects(owner_id=owner_id_str)
            campaign_ids = [str(c.id) for c in user_campaigns]
            all_leads = Lead.objects(campaign_id__in=campaign_ids)
        print(f"Lead search: owner={owner_id_str} leads_after_discovery={all_leads.count()}")

        # Scope candidates to this specific search intent to avoid mixing stale historical leads.
        filter_location_raw = (filters or {}).get("location") if filters else None
        scoped_location = (
            _normalize_location_text(str(filter_location_raw).strip())
            if filter_location_raw and str(filter_location_raw).strip()
            else None
        )
        scoped_industry = self._resolve_search_industry(
            industry=(filters or {}).get("industry") if filters else None,
            query=query,
        )
        scoped_services = self._as_service_list((filters or {}).get("services") or [])
        current_search_key = self._build_search_key(
            location=scoped_location,
            industry=scoped_industry,
            service_focus=scoped_services,
            query=query,
        )

        scoped_leads = all_leads(raw_data__search_key=current_search_key)
        scoped_count = scoped_leads.count()
        if scoped_count > 0:
            all_leads = scoped_leads
            print(
                "[LEAD SEARCH SCOPE] "
                f"mode=search_key search_key={current_search_key} matched={scoped_count}"
            )
        else:
            # Backward-compatible fallback for older leads without search_key.
            recent_cutoff = datetime.utcnow() - timedelta(days=14)
            recent_leads = all_leads(created_at__gte=recent_cutoff)
            if scoped_location:
                recent_leads = recent_leads(raw_data__requested_location=scoped_location)
            all_leads = recent_leads
            print(
                "[LEAD SEARCH SCOPE] "
                f"mode=recent_window days=14 location={scoped_location or '-'} matched={all_leads.count()}"
            )
        
        # Apply status filter if provided
        if filters and "status" in filters:
            all_leads = all_leads(status=filters["status"])
        
        # Score each lead with company fit
        scored_leads: List[Tuple[Lead, float]] = []
        scored_best_by_key: Dict[str, Tuple[Lead, float]] = {}
        skipped_constraints = 0
        skipped_low_score = 0
        skipped_no_signals = 0
        skipped_low_relevance = 0
        collapsed_duplicates = 0

        apollo_only_mode = bool((filters or {}).get("apollo_only"))
        source_mode = str((filters or {}).get("source_mode") or "").strip().lower()
        if source_mode in {"apollo", "apollo_only"}:
            apollo_only_mode = True
        if apollo_only_mode:
            print("[LEAD SCORING] Apollo-only mode active. Filtering out non-Apollo stored leads.")

        filter_location = (filters or {}).get("location") if filters else None
        profile_target_locations = company_profile.target_locations if company_profile and company_profile.target_locations else []
        location_scope = self._build_location_scope(filter_location, profile_target_locations)
        service_hints = self._as_service_list((filters or {}).get("services") or [])

        try:
            from app.services.enrichment_service import enrichment_service
        except Exception:
            enrichment_service = None
        
        for lead in all_leads:
            if not self._lead_matches_search_constraints(lead, query, filters):
                skipped_constraints += 1
                continue

            # Re-enrich when embedding is missing/invalid or from older incompatible dimensions
            if self._is_invalid_embedding(lead.lead_embedding, expected_dim=len(query_embedding)):
                lead = await self.enrich_lead_profile(lead, company_profile)
            
            # Keep compatibility metric: company profile embedding similarity (0-1).
            company_fit_score = 0.0
            if company_profile and company_profile.company_embeddings and lead.lead_embedding:
                try:
                    similarities = await embedding_service.similarity_search(
                        company_profile.company_embeddings,
                        [lead.lead_embedding],
                        top_k=1
                    )
                    company_fit_score = similarities[0][1] if similarities else 0.0
                except Exception as e:
                    print(f"Error calculating company fit for {lead.company}: {e}")
                    company_fit_score = 0.0
            
            # Keep compatibility metric: query-to-lead embedding relevance (0-1).
            query_score = 0.0
            if lead.lead_embedding:
                try:
                    similarities = await embedding_service.similarity_search(
                        query_embedding,
                        [lead.lead_embedding],
                        top_k=1
                    )
                    query_score = similarities[0][1] if similarities else 0.0
                except Exception as e:
                    query_score = 0.0

            lead_raw = lead.raw_data or {}
            source_name = str(lead_raw.get("source", "")).strip().lower()

            if apollo_only_mode and not source_name.startswith("apollo"):
                skipped_constraints += 1
                continue

            if enrichment_service and (
                not isinstance(lead.enriched_data, dict)
                or not lead.enriched_data.get("tech_stack")
                or not lead.enriched_data.get("decision_maker")
                or not lead.enriched_data.get("company_signals")
            ):
                try:
                    enrichment_payload = await enrichment_service.enrich_lead(
                        {
                            "company": lead.company,
                            "name": lead.name,
                            "company_website": lead_raw.get("company_website") or lead_raw.get("source_url"),
                            "source_url": lead_raw.get("source_url"),
                            "snippet": lead_raw.get("snippet", ""),
                            "source": source_name,
                        }
                    )
                    lead.enriched_data = {
                        "tech_stack": enrichment_payload.get("tech_stack", {}),
                        "decision_maker": enrichment_payload.get("decision_maker", {}),
                        "company_signals": enrichment_payload.get("company_signals", {}),
                        "enriched_at": enrichment_payload.get("enriched_at", ""),
                    }
                    lead.raw_data = lead.raw_data or {}
                    lead.raw_data["tech_stack"] = enrichment_payload.get("tech_stack", {})
                    lead.raw_data["decision_maker"] = enrichment_payload.get("decision_maker", {})
                    lead.raw_data["company_signals"] = enrichment_payload.get("company_signals", {})
                    lead_raw = lead.raw_data
                except Exception as e:
                    print(f"[LEAD SCORE] enrichment fallback failed for {lead.company}: {e}")

            signal_strength = float(lead.signal_score or lead_raw.get("signal_confidence", 0.0) or 0.0)
            location_match = 0.0
            if location_scope:
                location_text = " ".join(
                    [
                        str(lead_raw.get("detected_location", "")),
                        str(lead_raw.get("snippet", "")),
                        str(lead_raw.get("company_summary", "")),
                        str(lead_raw.get("source_url", "")),
                        str(lead.company or ""),
                    ]
                )
                if self._extract_location_hit(location_text, location_scope):
                    location_match = 1.0

            score_card = await self.calculate_lead_score(
                lead=lead,
                company_profile=company_profile,
                service_hints=service_hints,
            )
            total_score = int(score_card.get("total_score", 0) or 0)
            combined_score = max(0.0, min(1.0, total_score / 100.0))

            # Use combined score as default fallback for final_score display
            if sort_by == "fit_score":
                final_score = company_fit_score if company_fit_score > 0 else lead.company_fit_score or 0.0
            elif sort_by == "signal_score":
                final_score = signal_strength
            elif sort_by == "created_at":
                # For created_at sort, use combined score as display score but track timestamp separately for sorting
                final_score = combined_score
            else:
                final_score = combined_score

            if sort_by == "combined":
                final_score = combined_score

            reason = []
            if score_card.get("is_hot_lead"):
                reason.append("Hot lead score band")
            if company_fit_score >= 0.60:
                reason.append(f"Strong company profile fit ({company_fit_score:.0%})")
            if location_match >= 1.0:
                reason.append("Matches target location")
            if score_card.get("recommended_action"):
                reason.append(f"Action: {score_card['recommended_action']}")
            if not reason:
                reason.append("Scored by multi-signal lead rubric")

            dedupe_key = self._lead_dedupe_key(lead)
            
            # Determine sort key based on sort_by parameter
            if sort_by == "created_at":
                sort_key = lead.created_at.timestamp() if lead.created_at else 0.0
            else:
                sort_key = final_score
            
            best = scored_best_by_key.get(dedupe_key)
            if best and best[1] >= sort_key:
                collapsed_duplicates += 1
                continue
            if best and best[1] < sort_key:
                collapsed_duplicates += 1

            lead.raw_data = lead.raw_data or {}
            lead.raw_data["final_reason"] = reason
            lead.raw_data["final_score"] = final_score
            lead.raw_data["final_score_100"] = total_score
            lead.raw_data["score_card"] = score_card
            lead.raw_data["company_fit_score_calc"] = company_fit_score
            lead.raw_data["embedding_similarity"] = query_score
            lead.raw_data["location_match"] = location_match
            lead.raw_data["signal_strength"] = signal_strength
            lead.company_fit_score = max(float(lead.company_fit_score or 0.0), float(company_fit_score or 0.0))
            lead.signal_score = max(float(lead.signal_score or 0.0), float(signal_strength or 0.0))
            lead.save()

            if company_fit_score > 0 or query_score > 0:
                print(
                    f"[LEAD SCORING] {lead.company or 'unknown'}: "
                    f"total={total_score} grade={score_card.get('grade')} "
                    f"final={final_score:.2f} company_fit={company_fit_score:.2f} "
                    f"query={query_score:.2f} signal={signal_strength:.2f}"
                )

            scored_best_by_key[dedupe_key] = (lead, sort_key)
        
        scored_leads = list(scored_best_by_key.values())
        scored_leads.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Lead scoring summary: "
              f"total_candidates={all_leads.count()} "
              f"skipped_constraints={skipped_constraints} "
              f"skipped_no_signals={skipped_no_signals} "
              f"skipped_low_relevance={skipped_low_relevance} "
              f"skipped_low_score={skipped_low_score} "
              f"collapsed_duplicates={collapsed_duplicates} "
              f"scored={len(scored_leads)} "
              f"returning_top_k={min(top_k, len(scored_leads))}")
        
        # Return top-k leads
        return [lead for lead, score in scored_leads[:top_k]]

lead_service = LeadService()
