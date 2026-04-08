"""
Service for lead operations using MongoDB
"""
from typing import List, Optional, Dict, Any
from app.models.lead import Lead
from app.models.company import CompanyProfile
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.embeddings import embedding_service
from app.services.web_scraper import _normalize_location_text, analyze_business_signals
from datetime import datetime
from bson import ObjectId
from urllib.parse import urlparse
import re
import hashlib

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
        location = filters.get("location") if filters else None
        
        # === AUTO-EXTRACT INDUSTRY FROM SEARCH QUERY ===
        # If no industry filter, extract from query for richer context
        if not industry or str(industry).lower() == "all":
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
                if any(kw in query_lower for kw in keywords):
                    industry = industry_name
                    break
        service_focus = filters.get("services") if filters else None

        company_services = company_profile.services if company_profile and company_profile.services else []
        company_tech = company_profile.technologies if company_profile and company_profile.technologies else []
        company_expertise = company_profile.expertise_areas if company_profile and company_profile.expertise_areas else []
        target_locations = company_profile.target_locations if company_profile and company_profile.target_locations else []
        context_keywords = [*company_services, *company_tech, *company_expertise]

        discovered = await discover_company_websites(
            query=query,
            location=location,
            industry=industry,
            service_focus=service_focus or company_services,
            target_locations=target_locations,
            context_keywords=context_keywords,
            max_results=max_results,
        )
        if not discovered:
            return 0

        # Signature for this specific search intent (location/industry/services/query)
        services_key = "|".join(sorted([str(s).strip().lower() for s in (service_focus or []) if str(s).strip()]))
        search_seed = f"{str(location or '').strip().lower()}|{str(industry or '').strip().lower()}|{services_key}|{str(query or '').strip().lower()}"
        search_key = hashlib.md5(search_seed.encode("utf-8")).hexdigest()[:12]

        campaign = self._get_or_create_default_campaign(owner_id)
        existing = Lead.objects(campaign_id=str(campaign.id))
        existing_domain_keys = set()
        for lead in existing:
            source_url = (lead.raw_data or {}).get("source_url", "") if lead.raw_data else ""
            existing_search_key = (lead.raw_data or {}).get("search_key", "") if lead.raw_data else ""
            parsed = urlparse(source_url)
            domain = (parsed.netloc or "").lower().replace("www.", "")
            if domain:
                key = f"{domain}|{existing_search_key or 'legacy'}"
                existing_domain_keys.add(key)

        created_count = 0
        skipped_duplicate = 0
        skipped_empty_domain = 0
        skipped_low_quality = 0
        skipped_no_signal = 0
        for item in discovered:
            domain = (item.get("domain") or "").strip().lower().replace("www.", "")
            if not domain:
                skipped_empty_domain += 1
                continue

            domain_search_key = f"{domain}|{search_key}"
            if domain_search_key in existing_domain_keys:
                skipped_duplicate += 1
                continue

            company_name = (item.get("name") or domain.split(".")[0].title()).strip()
            email = f"contact@{domain}"
            phone = ""
            snippet = (item.get("snippet") or "").lower()

            snapshot = await fetch_company_profile_snapshot(item.get("url", ""))
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
                    "top 10", "top 50", "top 100", "list of", "to work for", "job",
                    "salary", "rankings", "directory", "compare",
                ]
            ):
                skipped_low_quality += 1
                continue

            website_text = summary_text
            if len(website_text) < 180:
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

            if signal_confidence < 0.18 and tech_relevance < 0.18:
                skipped_no_signal += 1
                print(f"Skipping {domain}: signal_confidence={signal_confidence:.2f}, tech_relevance={tech_relevance:.2f}, signals={signal_keywords}")
                continue

            # Quality scoring to keep only profile-like company leads
            quality_score = 0.0
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
            min_quality = 0.45 if has_snapshot else 0.35
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

            lead = Lead(
                campaign_id=str(campaign.id),
                name=company_name,
                email=email,
                company=company_name,
                phone=phone,
                job_title="Hiring Team",
                industry=industry if industry and str(industry).lower() != "all" else None,
                status="new",
                signal_keywords=signal_keywords,
                signal_score=signal_confidence,
                raw_data={
                    "source": "web_discovery",
                    "source_url": item.get("url", ""),
                    "company_website": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "query": query,
                    "location": location,
                    "search_key": search_key,
                    "service_focus": service_focus or [],
                    "context_keyword_hits": list(set(keyword_hits)),
                    "discovery_relevance_hint": relevance_hint,
                    "company_summary": snapshot.get("summary", ""),
                    "company_email": snapshot.get("email", ""),
                    "company_phone": snapshot.get("phone", ""),
                    "discovery_quality_score": quality_score,
                    "discovery_signals": signal_keywords,
                    "signal_confidence": signal_confidence,
                    "signal_reasons": signal_reasons,
                    "tech_relevance": tech_relevance,
                },
            )
            lead.save()

            if company_profile:
                await self.enrich_lead_profile(lead, company_profile)

            existing_domain_keys.add(domain_search_key)
            created_count += 1

        print(
            f"Lead discovery summary: owner={owner_id} created={created_count} "
            f"skipped_duplicate={skipped_duplicate} skipped_empty_domain={skipped_empty_domain} "
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

        location = (filters.get("location") or "").strip().lower()
        industry = (filters.get("industry") or "").strip().lower()
        services = [str(s).strip().lower() for s in (filters.get("services") or []) if str(s).strip()]

        searchable = " ".join(
            [
                str(lead.name or ""),
                str(lead.company or ""),
                str(lead.job_title or ""),
                str(lead.industry or ""),
                str(lead_raw.get("snippet", "")),
                str(lead_raw.get("query", "")),
                str(lead_raw.get("location", "")),
                str(lead_raw.get("source_url", "")),
            ]
        ).lower()
        normalized_location = _normalize_location_text(location) if location else ""

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
        if str(lead_raw.get("source", "")) == "web_discovery" and quality_score < 0.30:
            return False

        # Enforce high-intent business signal threshold (relaxed to show more leads)
        if str(lead_raw.get("source", "")) == "web_discovery" and signal_confidence < 0.10:
            return False
        if str(lead_raw.get("source", "")) == "web_discovery" and tech_relevance < 0.10:
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
            if location not in searchable and normalized_location and normalized_location not in searchable:
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
        
        # Apply status filter if provided
        if filters and "status" in filters:
            all_leads = all_leads(status=filters["status"])
        
        # Score each lead with company fit
        scored_leads = []
        skipped_constraints = 0
        skipped_low_score = 0
        skipped_no_signals = 0
        
        for lead in all_leads:
            if not self._lead_matches_search_constraints(lead, query, filters):
                skipped_constraints += 1
                continue

            # Re-enrich when embedding is missing/invalid or from older incompatible dimensions
            if self._is_invalid_embedding(lead.lead_embedding, expected_dim=len(query_embedding)):
                lead = await self.enrich_lead_profile(lead, company_profile)
            
            # === PRIMARY SCORING: Use company profile embeddings ===
            # Company profile fit is the main scoring factor
            company_fit_score = 0.0
            if company_profile and company_profile.company_embeddings and lead.lead_embedding:
                try:
                    similarities = await embedding_service.similarity_search(
                        company_profile.company_embeddings,  # Use company profile as primary context
                        [lead.lead_embedding],
                        top_k=1
                    )
                    company_fit_score = similarities[0][1] if similarities else 0.0
                except Exception as e:
                    print(f"Error calculating company fit for {lead.company}: {e}")
                    company_fit_score = 0.0
            
            # === SECONDARY SCORING: Query relevance ===
            # Query score is secondary, supports company fit
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
            signal_strength = float(lead.signal_score or lead_raw.get("signal_confidence", 0.0) or 0.0)
            location_match = 0.0
            filter_location = (filters or {}).get("location") if filters else None
            if filter_location:
                loc = str(filter_location).strip().lower()
                loc_norm = _normalize_location_text(loc)
                searchable = " ".join([
                    str(lead.company or ""),
                    str(lead_raw.get("snippet", "")),
                    str(lead_raw.get("location", "")),
                    str(lead_raw.get("source_url", "")),
                ]).lower()
                if loc in searchable or (loc_norm and loc_norm in searchable):
                    location_match = 1.0
            
            # Combined score: company fit + signal score + location
            # NEW WEIGHTS: company fit is primary (60%), signals secondary (30%), location (10%)
            if sort_by == "fit_score":
                final_score = company_fit_score if company_fit_score > 0 else lead.company_fit_score or 0.0
            elif sort_by == "signal_score":
                final_score = signal_strength
            elif sort_by == "created_at":
                final_score = lead.created_at.timestamp() if lead.created_at else 0.0
            elif sort_by == "combined":
                # NEW FORMULA: Prioritize company profile fit over query match
                # company_fit (60%) > signal_strength (30%) > location (10%)
                if company_fit_score > 0:
                    # Use company profile embeddings as primary
                    final_score = (
                        company_fit_score * 0.60 +
                        signal_strength * 0.30 +
                        location_match * 0.10
                    )
                else:
                    # Fallback if company profile embeddings not available
                    final_score = (
                        query_score * 0.40 +
                        signal_strength * 0.50 +
                        location_match * 0.10
                    )
            else:
                final_score = 0.0

            signal_keywords = lead.signal_keywords or lead_raw.get("discovery_signals", []) or []
            # Relaxed thresholds to show more discovered leads
            if sort_by == "combined" and signal_strength < 0.18 and len(signal_keywords) == 0:
                skipped_no_signals += 1
                continue

            # Drop very low-confidence results (minimum 0.35 for acceptable company fit or signals)
            if sort_by == "combined" and final_score < 0.35:
                skipped_low_score += 1
                continue

            reason = []
            if company_fit_score >= 0.60:
                reason.append(f"Strong company profile fit ({company_fit_score:.0%})")
            elif company_fit_score >= 0.45:
                reason.append(f"Good company profile alignment ({company_fit_score:.0%})")
            if signal_strength >= 0.40:
                reason.append(f"Strong growth signals ({signal_strength:.0%})")
            if location_match >= 1.0:
                reason.append("Matches target location")
            if query_score >= 0.50:
                reason.append(f"Relevant to search query ({query_score:.0%})")
            if not reason:
                reason.append("Qualified by company profile matching")

            lead.raw_data = lead.raw_data or {}
            lead.raw_data["final_reason"] = reason
            lead.raw_data["final_score"] = final_score
            lead.raw_data["company_fit_score_calc"] = company_fit_score
            lead.raw_data["embedding_similarity"] = query_score
            lead.raw_data["location_match"] = location_match
            lead.raw_data["signal_strength"] = signal_strength
            lead.save()
            
            # Debug logging to see what scores are being calculated
            if company_fit_score > 0 or query_score > 0:
                print(f"[LEAD SCORING] {lead.company or 'unknown'}: final={final_score:.2f} | company_fit={company_fit_score:.2f} | query={query_score:.2f} | signal={signal_strength:.2f}")
            
            scored_leads.append((lead, final_score))
        
        # Sort by score descending
        scored_leads.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Lead scoring summary: "
              f"total_candidates={all_leads.count()} "
              f"skipped_constraints={skipped_constraints} "
              f"skipped_no_signals={skipped_no_signals} "
              f"skipped_low_score={skipped_low_score} "
              f"scored={len(scored_leads)} "
              f"returning_top_k={min(top_k, len(scored_leads))}")
        
        # Return top-k leads
        return [lead for lead, score in scored_leads[:top_k]]

lead_service = LeadService()
