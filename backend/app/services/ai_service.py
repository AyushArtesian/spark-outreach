"""
Service for AI-related operations including embeddings and message generation.
"""

import asyncio
import importlib
import json
import re
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.models.campaign import Campaign
from app.models.embedding import Embedding
from app.models.lead import Lead
from app.services.llm_provider import groq_provider
from app.services.query_generator import build_high_intent_fallback_queries
from app.services.query_scorer import (
    estimate_search_effectiveness,
    extract_intent_signals,
    is_instructional_query,
    rank_high_intent_queries,
    score_query_intent,
)
from app.utils.embeddings import embedding_service
from app.utils.json_utils import extract_json_object, sanitize_queries

try:
    from google import genai

    _GEMINI_MODE = "new"
except ImportError:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai  # type: ignore

    _GEMINI_MODE = "legacy"


class AIService:
    """Service for AI operations including embeddings, RAG, and content generation."""

    def __init__(self):
        """Initialize AI service with configured provider."""
        self.model = None
        self.client = None

        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            if _GEMINI_MODE == "new":
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            else:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.provider = settings.LLM_PROVIDER
        print(
            "[AI INIT] "
            f"provider={self.provider} "
            f"groq_available={'yes' if groq_provider.client else 'no'} "
            f"gemini_available={'yes' if (self.client or self.model) else 'no'} "
            f"groq_model={settings.GROQ_MODEL}"
        )

    async def generate_completion_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """Provider-aware plain text completion helper."""
        if self.provider == "gemini":
            if _GEMINI_MODE == "new" and self.client:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                return response.text or ""
            if self.model:
                response = self.model.generate_content(prompt)
                return response.text or ""
            return "Gemini is not configured. Please set GEMINI_API_KEY in .env"

        if self.provider == "groq":
            if not groq_provider.client:
                return "Groq is not configured. Please set GROQ_API_KEY in .env"
            return await groq_provider.call_chat_completion(
                system_prompt="You are a precise assistant for B2B outreach workflows.",
                user_prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return "Generated message placeholder (configure OpenAI API key)"

    async def generate_lead_message(
        self,
        lead: Lead,
        campaign: Campaign,
        context: Optional[str] = None,
    ) -> str:
        """
        Generate a personalized message for a lead using AI.
        Supports both Gemini and Groq APIs.
        """
        prompt = f"""
You are a professional outreach specialist. Generate a personalized email message for the following lead:

Lead Information:
- Name: {lead.name}
- Company: {lead.company}
- Job Title: {lead.job_title}
- Industry: {lead.industry}

Campaign Information:
- Title: {campaign.title}
- Content: {campaign.content}
- Target Audience: {campaign.target_audience}

Custom Instructions:
{campaign.custom_instructions or 'None'}

Additional Context:
{context or 'None'}

Generate a personalized, professional email message that:
1. Addresses the lead by name
2. References their company/industry when relevant
3. Is concise and compelling
4. Has a clear call-to-action
5. Respects the character limit of {campaign.max_tokens} tokens

Message:
"""

        try:
            if self.provider == "gemini":
                if _GEMINI_MODE == "new" and self.client:
                    response = self.client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=prompt,
                    )
                    return response.text or ""
                if self.model:
                    response = self.model.generate_content(prompt)
                    return response.text or ""
                return "Gemini is not configured. Please set GEMINI_API_KEY in .env"

            if self.provider == "groq":
                if not groq_provider.client:
                    return "Groq is not configured. Please set GROQ_API_KEY in .env"
                content = await groq_provider.call_chat_completion(
                    system_prompt="You write concise, personalized, high-conversion outreach emails.",
                    user_prompt=prompt,
                    temperature=0.35,
                    max_tokens=max(256, min(1024, int(campaign.max_tokens or 512))),
                )
                return content or ""

            return "Generated message placeholder (configure OpenAI API key)"
        except Exception as e:
            print(f"Error generating message: {e}")
            return "Error generating personalized message. Please try again."

    async def analyze_lead_relevance(
        self,
        lead: Lead,
        campaign: Campaign,
    ) -> float:
        """
        Analyze how relevant a lead is to the campaign using embeddings.
        Returns a relevance score from 0 to 1.
        """
        lead_text = f"{lead.name} {lead.company} {lead.job_title} {lead.industry}".strip()
        campaign_text = f"{campaign.title} {campaign.content} {campaign.target_audience}"

        lead_embedding = await embedding_service.create_embedding(lead_text)
        campaign_embedding = await embedding_service.create_embedding(campaign_text)

        similarities = await embedding_service.similarity_search(
            campaign_embedding,
            [lead_embedding],
            top_k=1,
        )

        if similarities:
            return min(1.0, max(0.0, similarities[0][1]))
        return 0.0

    async def retrieve_relevant_context(
        self,
        query: str,
        campaign_id: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant information from campaign embeddings using RAG."""
        query_embedding = await embedding_service.create_embedding(query)
        embeddings = Embedding.objects(campaign_id=campaign_id)

        if not embeddings:
            return []

        similar = await embedding_service.similarity_search(
            query_embedding,
            [emb.embedding_vector for emb in embeddings],
            top_k=top_k,
        )

        results: List[Dict[str, Any]] = []
        embeddings_list = list(embeddings)
        for idx, score in similar:
            if idx < len(embeddings_list):
                results.append(
                    {
                        "content": embeddings_list[idx].content,
                        "metadata": embeddings_list[idx].embedding_metadata,
                        "score": score,
                    }
                )

        return results

    async def create_campaign_embeddings(self, campaign: Campaign) -> int:
        """
        Create embeddings for campaign content for RAG.
        Returns number of embeddings created.
        """
        chunks = embedding_service.chunk_text(campaign.content)
        embeddings_created = 0

        for chunk_idx, chunk in enumerate(chunks):
            embedding_vector = await embedding_service.create_embedding(chunk)
            embedding = Embedding(
                campaign_id=str(campaign.id),
                content=chunk,
                embedding_vector=embedding_vector,
                embedding_model=embedding_service.embedding_model,
                chunk_index=chunk_idx,
                embedding_metadata={
                    "chunk_count": len(chunks),
                    "chunk_size": len(chunk),
                },
            )
            embedding.save()
            embeddings_created += 1

        return embeddings_created

    async def plan_lead_discovery_queries(
        self,
        user_query: str,
        filters: Optional[Dict[str, Any]] = None,
        company_profile: Optional[Dict[str, Any]] = None,
        retrieved_context: Optional[List[str]] = None,
        max_queries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate high-intent web search queries from user intent + company context.
        Returns structured metadata and query list. Falls back gracefully on failure.
        """
        limit = max_queries or settings.LEAD_QUERY_PLANNER_MAX_QUERIES
        limit = max(4, min(15, int(limit or 10)))

        if not settings.LEAD_QUERY_PLANNER_ENABLED:
            print("[LEAD QUERY PLANNER] Disabled by LEAD_QUERY_PLANNER_ENABLED")
            return {
                "planner": "disabled",
                "queries": [],
                "strategy": "Planner disabled by LEAD_QUERY_PLANNER_ENABLED",
                "model": settings.GROQ_MODEL,
            }

        if not groq_provider.client:
            print(
                "[LEAD QUERY PLANNER] Groq client unavailable. "
                "Set GROQ_API_KEY to enable Qwen query planning."
            )
            return {
                "planner": "fallback",
                "queries": [],
                "strategy": "Groq planner unavailable (set GROQ_API_KEY).",
                "model": settings.GROQ_MODEL,
            }

        profile = company_profile or {}
        active_filters = filters or {}
        top_context = [
            str(chunk).strip()[:220]
            for chunk in (retrieved_context or [])
            if str(chunk).strip()
        ][:3]

        profile_brief = {
            "company_name": profile.get("company_name"),
            "services": (profile.get("services") or [])[:5],
            "expertise_areas": (profile.get("expertise_areas") or [])[:5],
            "technologies": (profile.get("technologies") or [])[:6],
            "target_industries": (profile.get("target_industries") or [])[:4],
            "target_locations": (profile.get("target_locations") or [])[:4],
            "company_narrative": str(
                profile.get("company_narrative") or profile.get("company_description") or ""
            )[:320],
        }

        location_hint = str(active_filters.get("location") or "").strip()
        if not location_hint:
            hinted_locations = [str(loc).strip() for loc in (profile_brief.get("target_locations") or []) if str(loc).strip()]
            if hinted_locations:
                location_hint = hinted_locations[0]

        normalized_location_hint = re.sub(r"\s+", " ", location_hint.strip().lower())
        location_tokens = [tok for tok in re.split(r"\W+", normalized_location_hint) if len(tok) >= 3]

        other_city_tokens = {
            "toronto", "vancouver", "montreal", "london", "newyork", "singapore", "francisco",
            "sydney", "melbourne", "dubai",
            "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", "delhi", "gurgaon",
            "gurugram", "chennai", "kolkata", "noida", "ahmedabad", "jaipur", "lucknow",
        }
        if location_tokens:
            for token in location_tokens:
                if token in other_city_tokens:
                    other_city_tokens.discard(token)

        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        current_year = datetime.utcnow().year

        def _normalize_candidate(candidate: str) -> str:
            cleaned = re.sub(r"^[\-\*\d\)\.\:]+\s*", "", str(candidate or "").strip())
            cleaned = re.sub(r"\s+", " ", cleaned).strip('"\'` ')
            cleaned = cleaned.replace('"', "").strip()
            if ". " in cleaned:
                head = cleaned.split(". ", 1)[0].strip()
                if len(head.split()) >= 5:
                    cleaned = head
            return cleaned.rstrip(".")

        def _extract_queries_from_text(raw_text: str, max_items: int) -> List[str]:
            """Best-effort extraction when model returns bullets/prose instead of strict JSON."""
            text = str(raw_text or "").strip()
            if not text:
                return []

            # Strip reasoning/think tags FIRST
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = text.replace("```json", "").replace("```", "")

            candidates: List[str] = []
            seen = set()

            # Strategy 1: Look for quoted strings in the response
            for quoted in re.findall(r'"([^"\n]{12,260})"', text):
                cleaned = _normalize_candidate(quoted)
                if len(cleaned.split()) < 4:  # Reduced from 5 to 4
                    continue
                lowered = cleaned.lower()
                if any(token in lowered for token in ["strategy", "json", "schema", "rules"]):
                    continue
                if lowered in seen:
                    continue
                seen.add(lowered)
                candidates.append(cleaned)
                if len(candidates) >= max_items:
                    return candidates

            # Strategy 2: Look for numbered lists or bullets
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # Remove list markers
                cleaned = re.sub(r"^[\d\.\)\-\*\s]+", "", line).strip()
                cleaned = _normalize_candidate(cleaned)
                
                if not cleaned:
                    continue
                if ":" in cleaned:
                    parts = cleaned.split(":", 1)
                    if len(parts) > 1:
                        cleaned = _normalize_candidate(parts[1].strip())
                
                if len(cleaned.split()) < 4:
                    continue

                lowered = cleaned.lower()
                if any(token in lowered for token in ["strategy", "query", "json", "schema", "rules", "note", "important"]):
                    continue
                if lowered in seen:
                    continue
                seen.add(lowered)
                candidates.append(cleaned)
                if len(candidates) >= max_items:
                    break

            return candidates

        def _looks_live_market_query(candidate: str) -> bool:
            """Accept only executable, buyer-intent, location-fenced market queries."""
            cleaned = _normalize_candidate(candidate)
            lowered = cleaned.lower()

            if not cleaned or len(cleaned.split()) < 5:
                return False
            if is_instructional_query(cleaned):
                return False
            if cleaned.count('"') % 2 != 0:
                return False

            blocked_fragments = {
                "original queries mention",
                "things like",
                "etc",
                "return only json",
                "json schema",
                "query_text",
                "rules:",
                "example good",
                "example bad",
            }
            if any(fragment in lowered for fragment in blocked_fragments):
                return False

            seller_disallowed = [
                "software development company",
                "web development company",
                "top app development",
                "best web development",
                "hire dedicated developers",
                "outsourcing company",
                "training institute",
                "course",
                "freelancer",
            ]
            if any(fragment in lowered for fragment in seller_disallowed):
                return False

            if location_tokens and not any(token in lowered for token in location_tokens):
                return False

            if any(f" {token} " in f" {lowered} " for token in other_city_tokens):
                return False

            # Require at least one live buying/market trigger.
            live_triggers = [
                "funded",
                "series",
                "rfp",
                "request for proposal",
                "procurement",
                "migration",
                "modernization",
                "implementation",
                "partner",
                "expansion",
                "growth",
                "looking for",
                "seeking",
                "vendor",
                "digital transformation",
                "it manager",
                "cto",
                "manufacturing companies",
                "retail companies",
                str(current_year),
                "this year",
                "now",
                "recent",
            ]
            if not any(trigger in lowered for trigger in live_triggers):
                return False

            return True

        def _filter_live_queries(candidates: List[str], max_items: int) -> List[str]:
            accepted: List[str] = []
            seen = set()

            for candidate in candidates:
                normalized = _normalize_candidate(str(candidate or ""))
                if not normalized:
                    continue
                key = normalized.lower()
                if key in seen:
                    continue
                if not _looks_live_market_query(normalized):
                    continue

                seen.add(key)
                accepted.append(normalized)
                if len(accepted) >= max_items:
                    break

            return accepted

        system_prompt = (
            "You are a B2B lead generation specialist. Generate Google search queries ONLY. "
            "Output valid JSON immediately. Do NOT use thinking tags, reasoning, or explanations. "
            "Every response MUST be valid JSON starting with { and ending with }. "
            f"CRITICAL: ALL queries MUST target this location: {location_hint or target_locations_str}. "
            "NEVER generate queries for other cities or countries. "
            "NEVER generate queries that would find vendors/agencies selling services. "
            "ONLY generate queries that find COMPANIES WHO WANT TO BUY services."
        )

        # Build company context for LLM
        company_narrative = profile_brief.get("company_narrative", "")
        target_industries_str = ", ".join(profile_brief.get("target_industries", []) or []) or "various industries"
        target_locations_str = ", ".join(profile_brief.get("target_locations", []) or []) or location_hint or "various locations"
        services_str = ", ".join(profile_brief.get("services", []) or [])
        technologies_str = ", ".join(profile_brief.get("technologies", []) or [])
        expertise_str = ", ".join(profile_brief.get("expertise_areas", []) or [])

        # Build rich context for LLM
        context_summary = f"""
COMPANY_PROFILE:
- Offers: {services_str or 'various services'}
- Expertise: {expertise_str or 'N/A'}
- Technologies: {technologies_str or 'N/A'}
- Target Industries: {target_industries_str}
- Service Regions: {target_locations_str}
- Focus: {company_narrative[:300] if company_narrative else 'Custom development and consulting'}

RETRIEVED_COMPANY_CONTEXT:
{chr(10).join(top_context) if top_context else 'Standard market context'}
"""

        user_prompt = (
            f"Generate {limit} DIFFERENT Google search queries to find COMPANIES THAT BUY {services_str or 'these services'}.\n\n"
            f"Target location (strict): {location_hint or target_locations_str}\n"
            f"Target industries: {target_industries_str}\n"
            f"Services sold: {services_str or 'custom software services'}\n"
            f"Current date: {current_date}\n\n"
            "Create both query types:\n"
            "Type A - Buyer Intent signals:\n"
            "- companies needing implementation/vendor partner\n"
            "- RFP/procurement/request-for-proposal signals\n"
            "- digital transformation and ERP modernization initiatives\n"
            "Type B - Company Discovery:\n"
            "- industry company lists in target location\n"
            "- funded/growth-stage startups in target location\n"
            "- LinkedIn company footprint with IT/CTO titles in target location\n\n"
            "Rules:\n"
            "- 7-13 words per query\n"
            "- MUST include the target location in EVERY query\n"
            "- MUST NOT include any other city/country\n"
            "- MUST find BUYERS, not service vendors/agencies\n"
            "- Avoid training institute, freelancer platform, and job portal intent\n"
            "- Use realistic Google syntax and minimal quotes\n"
            "- Generate at least 8 materially different queries\n\n"
            "Return ONLY valid JSON with no explanations:\n"
            "{\"queries\":[\"query_1\",\"query_2\",\"query_3\",\"query_4\",\"query_5\",\"query_6\",\"query_7\",\"query_8\",\"query_9\",\"query_10\"]}"
        )

        try:
            print(
                "[LEAD QUERY PLANNER] "
                f"provider=groq model={settings.GROQ_MODEL} "
                f"filters_keys={list(active_filters.keys())} "
                f"context_chunks={len(top_context)}"
            )
            print(
                "[LEAD QUERY PLANNER CONTEXT] "
                f"target_industries={','.join(profile_brief.get('target_industries', [])[:2])} "
                f"services={','.join(profile_brief.get('services', [])[:2])} "
                f"location={location_hint or 'not_specified'}"
            )
            raw_response = await groq_provider.call_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,  # Slightly higher for query variety
                max_tokens=1024,   # Increased to allow 10+ queries
                require_json=False,  # More lenient JSON parsing
            )

            # Strip reasoning traces FIRST before JSON parsing
            cleaned_response = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL | re.IGNORECASE)
            cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            
            parsed = extract_json_object(cleaned_response)
            raw_queries = []
            if isinstance(parsed, dict):
                raw_queries = (
                    parsed.get("queries")
                    or parsed.get("search_queries")
                    or parsed.get("planned_queries")
                    or parsed.get("google_queries")
                    or []
                )
            if not isinstance(raw_queries, list):
                raw_queries = []
            
            # Handle both query formats: strings and objects with {"query": "..."} 
            normalized_queries = []
            for q in raw_queries:
                if isinstance(q, str):
                    normalized_queries.append(q)
                elif isinstance(q, dict) and "query" in q:
                    normalized_queries.append(q["query"])
            raw_queries = _filter_live_queries(normalized_queries, max_items=limit)

            if not raw_queries:
                extracted_queries = _extract_queries_from_text(raw_response, limit)
                if extracted_queries:
                    cleaned_from_text = sanitize_queries(extracted_queries, max_queries=limit * 2)
                    cleaned_from_text = _filter_live_queries(cleaned_from_text, max_items=limit)
                    ranked_from_text = rank_high_intent_queries(
                        cleaned_from_text,
                        location_hint=location_hint,
                        max_queries=limit,
                        min_score=0.50,
                    )
                    selected_from_text = [item.query for item in ranked_from_text]
                    print(
                        "[LEAD QUERY PLANNER] "
                        f"Recovered queries from non-JSON output. selected={len(selected_from_text)}"
                    )
                    if selected_from_text:
                        return {
                            "planner": "groq",
                            "queries": selected_from_text,
                            "strategy": "Groq returned non-JSON; recovered query candidates from model text.",
                            "model": settings.GROQ_MODEL,
                            "quality_summary": {
                                "selected_count": len(selected_from_text),
                                "avg_score": round(
                                    sum(item.score for item in ranked_from_text) / len(ranked_from_text),
                                    3,
                                )
                                if ranked_from_text
                                else 0.0,
                            },
                        }

                print(
                    "[LEAD QUERY PLANNER] Groq returned empty/non-JSON output; using deterministic fallback. "
                    f"response_preview={str(raw_response)[:150]}"
                )
                fallback_queries = build_high_intent_fallback_queries(
                    user_query=user_query,
                    filters=active_filters,
                    company_profile=profile_brief,
                    max_queries=limit,
                )
                fallback_ranked = rank_high_intent_queries(
                    fallback_queries,
                    location_hint=location_hint,
                    max_queries=limit,
                    min_score=0.20,
                )
                selected_fallback = [item.query for item in fallback_ranked]
                return {
                    "planner": "groq",
                    "queries": selected_fallback,
                    "strategy": "Groq output unavailable; using deterministic fallback.",
                    "model": settings.GROQ_MODEL,
                    "quality_summary": {
                        "selected_count": len(selected_fallback),
                        "avg_score": round(
                            sum(item.score for item in fallback_ranked) / len(fallback_ranked),
                            3,
                        )
                        if fallback_ranked
                        else 0.0,
                    },
                }

            cleaned_queries = sanitize_queries(raw_queries, max_queries=limit * 2)
            cleaned_queries = _filter_live_queries(cleaned_queries, max_items=limit)
            ranked_queries = rank_high_intent_queries(
                cleaned_queries,
                location_hint=location_hint,
                max_queries=limit,
                min_score=0.50,
            )

            avg_score_first = (
                sum(q.score for q in ranked_queries) / len(ranked_queries)
                if ranked_queries
                else 0.0
            )
            search_effectiveness = estimate_search_effectiveness([q.query for q in ranked_queries])
            print(
                f"[LEAD QUERY PLANNER] First pass: avg_score={avg_score_first:.2f} "
                f"search_effectiveness={search_effectiveness:.2f}"
            )

            if (
                avg_score_first < 0.55
                or search_effectiveness < 0.6
                or len(ranked_queries) < 4  # Lower threshold: accept 4+ queries, don't always require 6-8
            ):
                print(
                    f"[LEAD QUERY PLANNER] Triggering refinement: "
                    f"avg_score={avg_score_first:.2f} effectiveness={search_effectiveness:.2f} "
                    f"count={len(ranked_queries)}"
                )
                refinement_prompt = (
                    f"Rewrite these queries to strict JSON for location {location_hint or active_filters.get('location') or ''}.\n"
                    "CRITICAL: Every query MUST contain ONLY this location and no other city/country.\n"
                    "Rules: 8-13 words, include location in each query, different buying situations across the set.\n"
                    "Avoid repetitive templates. Keep quote usage minimal and realistic.\n"
                    "Do not generate vendor/agency finder queries; generate buyer-company finder queries only.\n"
                    f"Industry: {active_filters.get('industry', 'all')}; "
                    f"services: {json.dumps(profile_brief.get('services', [])[:3], ensure_ascii=True)}; "
                    f"tech: {json.dumps(profile_brief.get('technologies', [])[:3], ensure_ascii=True)}.\n"
                    f"Current queries: {json.dumps(cleaned_queries, ensure_ascii=True)}\n"
                    "Return ONLY JSON: {\"queries\":[{\"query\":\"text\"}]}"
                )
                refined_raw = await groq_provider.call_chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=refinement_prompt,
                    temperature=0.0,  # Reduced from 0.12
                    max_tokens=320,   # Reduced from 420
                    require_json=True,  # Require JSON output
                )
                refined_parsed = extract_json_object(refined_raw) or {}
                refined_candidates = []
                if isinstance(refined_parsed, dict):
                    refined_candidates = (
                        refined_parsed.get("queries")
                        or refined_parsed.get("search_queries")
                        or refined_parsed.get("planned_queries")
                        or []
                    )
                if not isinstance(refined_candidates, list):
                    refined_candidates = []
                if not refined_candidates:
                    refined_candidates = [
                        {"query": q}
                        for q in _extract_queries_from_text(refined_raw, limit)
                    ]

                refined_clean = sanitize_queries(refined_candidates or [], max_queries=limit * 2)
                refined_clean = _filter_live_queries(refined_clean, max_items=limit)
                combined_clean = sanitize_queries(
                    cleaned_queries + refined_clean,
                    max_queries=limit * 2,
                )
                combined_clean = _filter_live_queries(combined_clean, max_items=limit * 2)
                ranked_queries = rank_high_intent_queries(
                    combined_clean,
                    location_hint=location_hint,
                    max_queries=limit,
                    min_score=0.50,
                )

            # Always ensure we have enough queries - add fallback if needed
            minimum_queries_needed = max(6, min(8, limit))  # Ensure at least 6-8 queries final
            if len(ranked_queries) < minimum_queries_needed:
                fallback_queries = build_high_intent_fallback_queries(
                    user_query=user_query,
                    filters=active_filters,
                    company_profile=profile_brief,
                    max_queries=limit,
                )
                fallback_ranked = rank_high_intent_queries(
                    fallback_queries,
                    location_hint=location_hint,
                    max_queries=limit,
                    min_score=0.45,
                )
                ranked_queries = ranked_queries + [
                    item
                    for item in fallback_ranked
                    if item.query.lower() not in {q.query.lower() for q in ranked_queries}
                ]
                ranked_queries = ranked_queries[:limit]

            selected_queries = [item.query for item in ranked_queries]
            print(
                "[LEAD QUERY PLANNER] "
                f"model={settings.GROQ_MODEL} raw_queries={len(raw_queries)} "
                f"cleaned_queries={len(cleaned_queries)} "
                f"selected_queries={len(selected_queries)}"
            )
            for idx, item in enumerate(ranked_queries[:8], 1):
                print(
                    "[LEAD QUERY PLANNER] "
                    f"Query {idx}: score={item.score:.2f} "
                    f"signals={','.join(item.signals) or 'none'} | {item.query}"
                )

            return {
                "planner": "groq",
                "queries": selected_queries,
                "strategy": str(parsed.get("strategy") if isinstance(parsed, dict) else "") or "",
                "model": settings.GROQ_MODEL,
                "quality_summary": {
                    "selected_count": len(selected_queries),
                    "avg_score": round(
                        sum(item.score for item in ranked_queries) / len(ranked_queries),
                        3,
                    )
                    if ranked_queries
                    else 0.0,
                },
            }
        except Exception as e:
            print(f"Error generating Groq lead discovery queries: {e}")
            return {
                "planner": "groq",
                "queries": [],
                "strategy": "Groq planner failed; using deterministic fallback.",
                "model": settings.GROQ_MODEL,
            }


# Initialize AI service singleton
ai_service = AIService()

# Global model cache for embeddings
_embeddings_model = None
_embeddings_model_load_failed = False


def _get_embeddings_model():
    """Lazy load the SentenceTransformer model."""
    global _embeddings_model, _embeddings_model_load_failed
    if _embeddings_model_load_failed:
        return None

    if _embeddings_model is None:
        try:
            module = importlib.import_module("sentence_transformers")
            sentence_transformer_cls = getattr(module, "SentenceTransformer", None)
            if sentence_transformer_cls is None:
                raise ImportError("SentenceTransformer class not found in sentence_transformers module")

            print("Loading SentenceTransformer model (paraphrase-mpnet-base-v2)...")
            _embeddings_model = sentence_transformer_cls("paraphrase-mpnet-base-v2")
            print("SentenceTransformer model loaded successfully!")
        except ImportError:
            _embeddings_model_load_failed = True
            print("sentence-transformers package not installed; using zero vector fallback")
            return None
        except Exception as e:
            _embeddings_model_load_failed = True
            print(f"Error loading SentenceTransformer model: {e}")
            return None
    return _embeddings_model


async def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for text using local SentenceTransformers.
    Model: paraphrase-mpnet-base-v2 (768-dimensional vectors)
    """
    try:
        model = _get_embeddings_model()
        if model is None:
            print("SentenceTransformer model not available, using zero vector fallback")
            return [0.0] * 768

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_tensor=False),
        )
        return [float(x) for x in embedding]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return [0.0] * 768


async def generate_completion(prompt: str) -> str:
    """Generate provider-aware completion text for secondary workflows like ICP."""
    try:
        return await ai_service.generate_completion_text(
            prompt=prompt,
            max_tokens=1200,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Error generating completion: {e}")
        return "Error: ICP generation not available. Using default ICP from company profile."
