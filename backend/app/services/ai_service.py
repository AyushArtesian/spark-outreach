"""
Service for AI-related operations including embeddings and message generation
"""
import asyncio
import json
from typing import Optional, List, Dict, Any
import warnings
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.embedding import Embedding
from app.utils.embeddings import embedding_service
from app.utils.json_utils import extract_json_object, sanitize_queries
from app.config import settings
from app.services.query_scorer import (
    extract_intent_signals,
    score_query_intent,
    rank_high_intent_queries,
    estimate_search_effectiveness,
)
from app.services.query_generator import build_high_intent_fallback_queries
from app.services.llm_provider import groq_provider

try:
    from google import genai
    _GEMINI_MODE = "new"
except ImportError:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai  # type: ignore
    _GEMINI_MODE = "legacy"

class AIService:
    """Service for AI operations including embeddings, RAG, and content generation"""
    
    def __init__(self):
        """Initialize AI service with configured provider"""
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
        context: Optional[str] = None
    ) -> str:
        """
        Generate a personalized message for a lead using AI
        Supports both Gemini and Groq APIs
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
                    return response.text
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

            # Placeholder for OpenAI implementation
            return "Generated message placeholder (configure OpenAI API key)"
        except Exception as e:
            print(f"Error generating message: {e}")
            return "Error generating personalized message. Please try again."
    
    async def analyze_lead_relevance(
        self,
        lead: Lead,
        campaign: Campaign
    ) -> float:
        """
        Analyze how relevant a lead is to the campaign using embeddings
        Returns a relevance score from 0 to 1
        """
        # Get or create embeddings for lead profile
        lead_text = f"{lead.name} {lead.company} {lead.job_title} {lead.industry}".strip()
        
        # Get or create embeddings for campaign target
        campaign_text = f"{campaign.title} {campaign.content} {campaign.target_audience}"
        
        lead_embedding = await embedding_service.create_embedding(lead_text)
        campaign_embedding = await embedding_service.create_embedding(campaign_text)
        
        # Calculate similarity
        similarities = await embedding_service.similarity_search(
            campaign_embedding, 
            [lead_embedding], 
            top_k=1
        )
        
        if similarities:
            relevance_score = min(1.0, max(0.0, similarities[0][1]))
        else:
            relevance_score = 0.0
        
        return relevance_score
    
    async def retrieve_relevant_context(
        self,
        query: str,
        campaign_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from campaign embeddings using RAG
        """
        # Create embedding for query
        query_embedding = await embedding_service.create_embedding(query)
        
        # Get all embeddings for this campaign from MongoDB
        embeddings = Embedding.objects(campaign_id=campaign_id)
        
        if not embeddings:
            return []
        
        # Find similar embeddings
        similar = await embedding_service.similarity_search(
            query_embedding,
            [emb.embedding_vector for emb in embeddings],
            top_k=top_k
        )
        
        results = []
        embeddings_list = list(embeddings)
        for idx, score in similar:
            if idx < len(embeddings_list):
                results.append({
                    "content": embeddings_list[idx].content,
                    "metadata": embeddings_list[idx].embedding_metadata,
                    "score": score
                })
        
        return results
    
    async def create_campaign_embeddings(
        self,
        campaign: Campaign
    ) -> int:
        """
        Create embeddings for campaign content for RAG
        Returns number of embeddings created
        """
        # Chunk the campaign content
        chunks = embedding_service.chunk_text(campaign.content)
        
        embeddings_created = 0
        
        for chunk_idx, chunk in enumerate(chunks):
            # Create embedding
            embedding_vector = await embedding_service.create_embedding(chunk)
            
            # Store in database
            embedding = Embedding(
                campaign_id=str(campaign.id),
                content=chunk,
                embedding_vector=embedding_vector,  # Native list in MongoDB
                embedding_model=embedding_service.embedding_model,
                chunk_index=chunk_idx,
                embedding_metadata={
                    "chunk_count": len(chunks),
                    "chunk_size": len(chunk)
                }
            )
            embedding.save()  # MongoDB save
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
        Uses modularized query_scorer, query_generator, and llm_provider components.
        Returns structured metadata and query list. Falls back gracefully on any failure.
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
        top_context = [str(chunk).strip() for chunk in (retrieved_context or []) if str(chunk).strip()][:6]

        profile_brief = {
            "company_name": profile.get("company_name"),
            "services": profile.get("services") or [],
            "expertise_areas": profile.get("expertise_areas") or [],
            "technologies": profile.get("technologies") or [],
            "target_industries": profile.get("target_industries") or [],
            "target_locations": profile.get("target_locations") or [],
            "company_narrative": profile.get("company_narrative") or profile.get("company_description") or "",
        }

        location_hint = str(active_filters.get("location") or "").strip()

        system_prompt = (
            "You are a principal outbound strategist focused on high-ticket B2B opportunities. "
            "Your job is to generate non-generic, high-intent Google queries that surface in-market buyers "
            "likely to purchase within 30-120 days. Return ONLY valid JSON."
        )

        user_prompt = (
            "Create HIGH-SPECIFICITY web search queries that find EXACT buyer profiles.\n"
            "Focus on precision: narrow down to ICP matches, NOT broad market sweeps.\n\n"
            f"USER_SEARCH_REQUEST:\n{user_query}\n\n"
            f"ACTIVE_FILTERS_JSON:\n{json.dumps(active_filters, ensure_ascii=True)}\n\n"
            f"COMPANY_PROFILE_BRIEF_JSON:\n{json.dumps(profile_brief, ensure_ascii=True)}\n\n"
            f"RETRIEVED_COMPANY_CONTEXT_CHUNKS_JSON:\n{json.dumps(top_context, ensure_ascii=True)}\n\n"
            "QUERY GENERATION STRATEGY (CRITICAL):\n"
            "1. **Specificity First**: Every query MUST narrow results to <100 companies, NOT thousands.\n"
            "2. **Use Company Context**: Force inclusion of YOUR company's technologies/services in query.\n"
            "3. **Multiple Angles**: Create queries targeting different buyer pain points:\n"
            "   - Angle 1: By technology + hiring + location (find tech stacks matching yours)\n"
            "   - Angle 2: By problem domain + RFP + location (find pain point matches)\n"
            "   - Angle 3: By growth stage + funding + your service fit\n"
            "   - Angle 4: By migration/modernization need + your expertise\n"
            "4. **Location Precision**: Always include specific city/region, NOT country-level.\n"
            "5. **Buying Signals**: Mix 2-3 signals per query (hiring + funding + migration, etc).\n\n"
            "MANDATORY QUERY COMPONENTS:\n"
            f"- Location: {location_hint or 'target location from filters'}\n"
            "- GEO FENCE: Every query must include the target city; do NOT mix unrelated cities.\n"
            "- Nearby allowed only when meaningful (e.g., neighboring metro areas), never random regions.\n"
            f"- Industry: {active_filters.get('industry') or 'from context'}\n"
            f"- Your Services: MUST include >=1 of {profile_brief.get('services', [])[:3]}\n"
            f"- Your Tech: MUST include >=1 of {profile_brief.get('technologies', [])[:3]}\n"
            "- Buying Signal: hiring OR funding OR migration OR RFP (mandatory)\n\n"
            "REALISTIC OPERATOR RULES (NO HALLUCINATION):\n"
            "✓ ALLOWED: intitle:careers intitle:jobs intitle:hiring intitle:rfp intitle:about\n"
            "✓ ALLOWED: inurl:careers inurl:jobs inurl:hiring inurl:about\n"
            "✓ ALLOWED: Phrase quotes like \"Series A\" \"technical migration\" \"power platform\"\n"
            "✗ BANNED: intitle:technical intitle:vendor intitle:seriesc intitle:ipo\n"
            "✗ BANNED: inurl:technical-debt inurl:engineering-manager (these don't exist)\n\n"
            "QUERY QUALITY CHECKLIST:\n"
            f"- Length: 10-15 words (longer = more specific)\n"
            "- Specificity: Should surface <200 results in Google (NOT thousands)\n"
            "- Context Match: Query must reflect YOUR services/tech precisely\n"
            "- Realism: Every query must be searchable today (test mentally)\n"
            "- Diversity: Vary angles - don't repeat same signals 3x\n\n"
            "EXAMPLE GOOD QUERIES (Your Service = Power Platform Migration):\n"
            "1. Power Platform migration hiring developers Gurgaon growing SaaS\n"
            "2. SharePoint to Power Apps modernization technical debt RFP Bangalore\n"
            "3. Legacy system transformation Microsoft ecosystem funding Fintech Delhi\n"
            "4. Business process automation expansion intitle:careers Azure Fintech\n\n"
            "EXAMPLE BAD QUERIES (TOO BROAD - AVOID):\n"
            "✗ Series A funding hiring engineers (100k results, wrong companies)\n"
            "✗ Cloud migration companies (generic, not your service)\n"
            "✗ Technical consulting (too vague, no context)\n\n"
            f"Generate exactly {limit} unique, highly specific queries.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            "  \"strategy\": \"How these queries narrow to exact ICP\",\n"
            "  \"queries\": [\n"
            "    {\"query\": \"specific contextual query\", \"signals\": [\"hiring\", \"funding\"], \"angle\": \"tech match\", \"why\": \"precise reason\"}\n"
            "  ]\n"
            "}"
        )

        try:
            print(
                "[LEAD QUERY PLANNER] "
                f"provider=groq model={settings.GROQ_MODEL} "
                f"filters_keys={list(active_filters.keys())} "
                f"context_chunks={len(top_context)}"
            )
            # Call Groq via the modularized provider
            raw_response = await groq_provider.call_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.25,
                max_tokens=950,
                require_json=True,
            )
            parsed = extract_json_object(raw_response)
            if not parsed:
                print(
                    "[LEAD QUERY PLANNER] Groq returned non-JSON output. "
                    f"response_preview={str(raw_response)[:220]}"
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
                    "strategy": "Groq returned non-JSON output; using deterministic high-intent fallback.",
                    "model": settings.GROQ_MODEL,
                    "quality_summary": {
                        "selected_count": len(selected_fallback),
                        "avg_score": round(
                            sum(item.score for item in fallback_ranked) / len(fallback_ranked),
                            3,
                        ) if fallback_ranked else 0.0,
                    },
                }

            raw_queries = parsed.get("queries")
            if not isinstance(raw_queries, list):
                raw_queries = []

            cleaned_queries = sanitize_queries(raw_queries, max_queries=limit)
            ranked_queries = rank_high_intent_queries(
                cleaned_queries,
                location_hint=location_hint,
                max_queries=limit,
                min_score=0.50,
            )

            # Calculate average score of first-pass results
            avg_score_first = sum(q.score for q in ranked_queries) / len(ranked_queries) if ranked_queries else 0.0
            
            # Check searchability - if queries won't work in Google, trigger refinement
            search_effectiveness = estimate_search_effectiveness([q.query for q in ranked_queries])
            print(
                f"[LEAD QUERY PLANNER] First pass: avg_score={avg_score_first:.2f} "
                f"search_effectiveness={search_effectiveness:.2f}"
            )
            
            # If first pass yields poor quality, low searchability, OR too few queries, trigger refinement
            if (avg_score_first < 0.55 or search_effectiveness < 0.6 or 
                len(ranked_queries) < max(6, min(8, limit))):
                print(
                    f"[LEAD QUERY PLANNER] Triggering refinement: "
                    f"avg_score={avg_score_first:.2f} effectiveness={search_effectiveness:.2f} count={len(ranked_queries)}"
                )
                refinement_prompt = (
                    "REFINEMENT MISSION: Make queries highly specific and searchable.\n"
                    "Current issue: queries are too broad OR have fake operators.\n\n"
                    "SPECIFICITY TARGETS (rewrite to narrow down results):\n"
                    "- Add 3-5 more words per query (aim for 12-15 total words)\n"
                    "- Include company context: technologies, services, domains\n"
                    "- Combine constraints: location + vertical + signal + your service\n"
                    "- GEO FENCE: keep only target city/nearby variants; never include unrelated cities\n"
                    "- Example: 'Power Platform migration hiring Gurgaon SaaS' (15 words, specific)\n"
                    "- Bad: 'Series A funding hiring' (5 words, too broad)\n\n"
                    "REALISTIC OPERATORS ONLY:\n"
                    "✓ GOOD: intitle:careers intitle:jobs intitle:rfp inurl:careers inurl:jobs \"phrases\"\n"
                    "✗ BAD: intitle:seriesc intitle:vendor intitle:technical inurl:engineering-manager\n\n"
                    "MULTI-SIGNAL REQUIREMENT:\n"
                    "- MUST combine 2+ signals: hiring + funding, migration + RFP, etc.\n"
                    "- Don't repeat same signal multiple times\n\n"
                    f"CONTEXT TO USE:\n"
                    f"- Location: {location_hint}\n"
                    f"- Industry: {active_filters.get('industry', 'all')}\n"
                    f"- Company services: {profile_brief.get('services', [])[:3]}\n"
                    f"- Technologies: {profile_brief.get('technologies', [])[:3]}\n"
                    f"- User need: {user_query}\n\n"
                    f"Current queries to fix: {json.dumps(cleaned_queries, ensure_ascii=True)}\n\n"
                    "Rewrite ALL queries to be specific + searchable + 12+ words.\n\n"
                    "Return ONLY JSON:\n"
                    "{\n"
                    "  \"queries\": [{\"query\": \"highly specific 12-15 word query\"}]\n"
                    "}"
                )
                refined_raw = await groq_provider.call_chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=refinement_prompt,
                    temperature=0.15,
                    max_tokens=850,
                    require_json=True,
                )
                refined_parsed = extract_json_object(refined_raw) or {}
                refined_candidates = refined_parsed.get("queries") if isinstance(refined_parsed, dict) else []
                refined_clean = sanitize_queries(refined_candidates or [], max_queries=limit)
                combined_clean = sanitize_queries(cleaned_queries + refined_clean, max_queries=limit * 2)
                ranked_queries = rank_high_intent_queries(
                    combined_clean,
                    location_hint=location_hint,
                    max_queries=limit,
                    min_score=0.50,
                )

            if len(ranked_queries) < max(6, min(8, limit)):
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
                    item for item in fallback_ranked
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
                "strategy": str(parsed.get("strategy") or ""),
                "model": settings.GROQ_MODEL,
                "quality_summary": {
                    "selected_count": len(selected_queries),
                    "avg_score": round(
                        sum(item.score for item in ranked_queries) / len(ranked_queries),
                        3,
                    ) if ranked_queries else 0.0,
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

def _get_embeddings_model():
    """Lazy load the SentenceTransformer model"""
    global _embeddings_model
    if _embeddings_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading SentenceTransformer model (paraphrase-mpnet-base-v2)...")
            _embeddings_model = SentenceTransformer('paraphrase-mpnet-base-v2')
            print("SentenceTransformer model loaded successfully!")
        except Exception as e:
            print(f"Error loading SentenceTransformer model: {e}")
            return None
    return _embeddings_model

# Standalone helper functions for company service
async def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for text using local SentenceTransformers
    Model: paraphrase-mpnet-base-v2 (768-dimensional vectors)
    Optimized for semantic similarity and richer context understanding
    Runs completely offline after first download - no API key needed
    Returns a vector of floats
    """
    try:
        import asyncio
        
        # Get or load the model
        model = _get_embeddings_model()
        if model is None:
            print("SentenceTransformer model not available, using zero vector fallback")
            return [0.0] * 768
        
        # Run encoding in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_tensor=False)
        )
        
        # Convert to list of floats
        return [float(x) for x in embedding]
    
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return [0.0] * 768

async def generate_completion(prompt: str) -> str:
    """
    Generate provider-aware completion text for secondary workflows like ICP.
    """
    try:
        return await ai_service.generate_completion_text(prompt=prompt, max_tokens=1200, temperature=0.2)
    except Exception as e:
        print(f"Error generating completion: {e}")
        return "Error: ICP generation not available. Using default ICP from company profile."
