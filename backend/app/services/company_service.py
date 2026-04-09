"""
Company profile service
Handles company context processing, embeddings, ICP generation
"""
from typing import Optional, List, Dict, Any
from app.models.company import CompanyProfile
from app.services.ai_service import generate_embeddings, generate_completion
from app.services.web_scraper import fetch_all_portfolio_content, combine_portfolio_content
from app.utils.embeddings import embedding_service
from datetime import datetime
from bson import ObjectId
import json

class CompanyService:
    """Service for company profile operations"""
    
    @staticmethod
    def create_or_update_company_profile(owner_id: str, data: dict) -> dict:
        """Create or update company profile"""
        # Check if profile exists
        profile = CompanyProfile.objects(owner_id=owner_id).first()
        
        if not profile:
            # Create new profile
            profile = CompanyProfile(owner_id=owner_id)
        
        # Update fields
        allowed_fields = [
            'company_name', 'company_size', 'company_stage', 'company_description',
            'company_website', 'upwork_id', 'github_url', 'linkedin_url', 'portfolio_urls',
            'services', 'expertise_areas', 'technologies', 'target_industries',
            'target_locations', 'team_size', 'team_expertise', 'projects',
            'min_deal_size', 'max_deal_size', 'preferred_company_stages',
            'setup_step'
        ]
        
        for field, value in data.items():
            if field in allowed_fields and value is not None:
                setattr(profile, field, value)
        
        profile.save()
        return CompanyService.serialize_profile(profile)
    
    @staticmethod
    def get_company_profile(owner_id: str) -> Optional[dict]:
        """Get company profile for owner"""
        profile = CompanyProfile.objects(owner_id=owner_id).first()
        if not profile:
            return None
        return CompanyService.serialize_profile(profile)
    
    @staticmethod
    def serialize_profile(profile: CompanyProfile) -> dict:
        """Serialize company profile to dict"""
        return {
            'id': str(profile.id),
            'owner_id': str(profile.owner_id),
            'company_name': profile.company_name,
            'company_size': profile.company_size,
            'company_stage': profile.company_stage,
            'company_description': profile.company_description,
            'company_website': profile.company_website,
            'upwork_id': profile.upwork_id,
            'github_url': profile.github_url,
            'linkedin_url': profile.linkedin_url,
            'portfolio_urls': profile.portfolio_urls or [],
            'fetched_website_content': profile.fetched_website_content,
            'portfolio_content': profile.portfolio_content or {},
            'company_narrative': profile.company_narrative,
            'services': profile.services or [],
            'expertise_areas': profile.expertise_areas or [],
            'technologies': profile.technologies or [],
            'target_industries': profile.target_industries or [],
            'target_locations': profile.target_locations or [],
            'team_size': profile.team_size,
            'team_expertise': profile.team_expertise or [],
            'projects': profile.projects or [],
            'icp': profile.icp,
            'ideal_customer_profile': profile.ideal_customer_profile,
            'avoid_patterns': profile.avoid_patterns or [],
            'hiring_signal_keywords': profile.hiring_signal_keywords or [],
            'funding_signal_keywords': profile.funding_signal_keywords or [],
            'tech_signal_keywords': profile.tech_signal_keywords or [],
            'min_deal_size': profile.min_deal_size,
            'max_deal_size': profile.max_deal_size,
            'preferred_company_stages': profile.preferred_company_stages or [],
            'is_complete': profile.is_complete,
            'setup_step': profile.setup_step,
            'created_at': profile.created_at,
            'updated_at': profile.updated_at,
            'last_embedding_update': profile.last_embedding_update,
        }
    
    @staticmethod
    async def generate_company_embeddings(owner_id: str) -> dict:
        """
        Generate embeddings for company profile
        This creates semantic representation of the company including website and portfolio content
        """
        profile = CompanyProfile.objects(owner_id=owner_id).first()
        if not profile:
            raise ValueError("Company profile not found")
        
        print(f"Fetching portfolio content for {profile.company_name}...")
        
        # Fetch content from all portfolio sources
        portfolio_content = await fetch_all_portfolio_content(
            company_website=profile.company_website,
            upwork_id=profile.upwork_id,
            github_url=profile.github_url,
            linkedin_url=profile.linkedin_url,
            portfolio_urls=profile.portfolio_urls
        )
        
        # Cache portfolio content
        if portfolio_content:
            profile.portfolio_content = portfolio_content
            portfolio_text = combine_portfolio_content(portfolio_content)
            profile.fetched_website_content = portfolio_text[:2000]  # Store first 2000 chars
        
        # Build comprehensive company description for embedding
        company_text = CompanyService._build_embedding_text(profile, portfolio_content)
        
        # Generate embedding
        embedding = await generate_embeddings(company_text)
        
        # Save embedding
        profile.company_embeddings = embedding
        profile.last_embedding_update = datetime.utcnow()
        profile.save()
        
        print(f"Successfully generated embeddings for {profile.company_name}")
        return CompanyService.serialize_profile(profile)
    
    @staticmethod
    async def query_company_profile(owner_id: str, query: str, top_k: int = 3) -> dict:
        """Query company profile content using embeddings for relevance ranking."""
        owner_id_str = str(owner_id)
        profile = None
        try:
            profile = CompanyProfile.objects(owner_id=ObjectId(owner_id_str)).first()
        except Exception:
            profile = None
        if not profile:
            profile = CompanyProfile.objects(owner_id=owner_id_str).first()
        if not profile:
            raise ValueError("Company profile not found")

        portfolio_content = profile.portfolio_content or {}
        segments = CompanyService._build_company_retrieval_segments(profile, portfolio_content)
        if not segments:
            return {"query": query, "results": []}

        chunks: List[str] = []

        # Add an overall company overview chunk first for broad questions.
        company_text = CompanyService._build_embedding_text(profile, portfolio_content)
        chunks.extend(embedding_service.chunk_text(company_text, chunk_size=250, overlap=60))

        for segment in segments:
            chunks.extend(embedding_service.chunk_text(segment, chunk_size=250, overlap=60))

        # Remove trivial chunks and duplicates
        normalized = []
        seen = set()
        for chunk in chunks:
            cleaned = chunk.strip()
            if CompanyService._is_trivial_chunk(cleaned):
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        chunks = normalized

        if not chunks:
            return {"query": query, "results": []}

        if not chunks:
            return {"query": query, "results": []}

        query_embedding = await generate_embeddings(query)
        chunk_embeddings = [await generate_embeddings(chunk) for chunk in chunks]

        similar = await embedding_service.similarity_search(
            query_embedding,
            chunk_embeddings,
            top_k=min(top_k, len(chunks))
        )

        results = []
        for idx, score in similar:
            chunk_text = chunks[idx]
            boost = CompanyService._boost_exact_keyword_matches(query, chunk_text)
            results.append({
                "index": idx,
                "score": min(1.0, score + boost),
                "chunk": chunk_text
            })

        # Sort again after boosting
        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "query": query,
            "results": results[:top_k]
        }
    
    @staticmethod
    def _build_company_retrieval_segments(profile: CompanyProfile, portfolio_content: Dict[str, str]) -> List[str]:
        """Build smaller retrieval segments from company profile data and fetched content."""
        segments: List[str] = []

        if profile.company_name:
            segments.append(f"Company: {profile.company_name}")

        if profile.company_description:
            segments.append(f"Description: {profile.company_description}")

        if profile.services:
            segments.append(f"Services: {', '.join(profile.services)}")

        if profile.expertise_areas:
            segments.append(f"Expertise: {', '.join(profile.expertise_areas)}")

        if profile.technologies:
            segments.append(f"Technologies: {', '.join(profile.technologies)}")

        if profile.target_industries:
            segments.append(f"Target Industries: {', '.join(profile.target_industries)}")

        if profile.target_locations:
            segments.append(f"Target Locations: {', '.join(profile.target_locations)}")

        if profile.team_expertise:
            segments.append(f"Team Expertise: {', '.join(profile.team_expertise)}")

        if profile.projects:
            for proj in profile.projects:
                proj_text = f"Project: {proj.get('title', 'Untitled')} - {proj.get('description', '')}"
                if proj.get('technologies'):
                    proj_text += f" (Tech: {', '.join(proj.get('technologies'))})"
                segments.append(proj_text)

        if profile.company_website:
            segments.append(f"Website: {profile.company_website}")

        if profile.github_url:
            segments.append(f"GitHub: {profile.github_url}")

        if profile.linkedin_url:
            segments.append(f"LinkedIn: {profile.linkedin_url}")

        if profile.upwork_id:
            segments.append(f"Upwork: {profile.upwork_id}")

        if profile.portfolio_urls:
            segments.append(f"Portfolio URLs: {', '.join(profile.portfolio_urls)}")

        for source, content in portfolio_content.items():
            if content:
                segments.append(f"Source: {source}\n{content}")

        return segments

    @staticmethod
    def _boost_exact_keyword_matches(query: str, segment: str) -> float:
        """Boost score for exact keyword matches on important terms."""
        boost = 0.0
        lowered = query.lower()
        segment_lower = segment.lower()

        keywords = [".net", "dotnet", "microsoft", "asp.net", "c#", "net maui", "maui"]
        for token in keywords:
            if token in lowered and token in segment_lower:
                boost += 0.18

        # Additional boost for exact technology names mentioned in the query
        if "power apps" in lowered and "power apps" in segment_lower:
            boost += 0.15
        if "power platform" in lowered and "power platform" in segment_lower:
            boost += 0.15
        if "azure" in lowered and "azure" in segment_lower:
            boost += 0.1

        return boost

    @staticmethod
    def _is_trivial_chunk(chunk: str) -> bool:
        """Ignore tiny or metadata-only chunks that are not useful for QA."""
        if len(chunk.split()) <= 6:
            return True
        lowered = chunk.lower()
        if lowered.startswith("website:") or lowered.startswith("github:") or lowered.startswith("linkedin:") or lowered.startswith("upwork:"):
            return True
        if lowered.startswith("source:") and len(lowered.split()) < 10:
            return True
        if lowered.startswith("projects:") and len(lowered.split()) <= 6:
            return True
        return False

    @staticmethod
    async def generate_icp_and_signals(owner_id: str) -> dict:
        """
        Generate Ideal Customer Profile and signals using Gemini
        Uses company context to define what ideal leads look like
        """
        profile = CompanyProfile.objects(owner_id=owner_id).first()
        if not profile:
            raise ValueError("Company profile not found")
        
        company_text = CompanyService._build_embedding_text(profile)
        
        # Prompt for ICP generation
        icp_prompt = f"""Based on this company profile, generate an Ideal Customer Profile (ICP) for their lead generation efforts.

Company Profile:
{company_text}

Generate a JSON response with this structure:
{{
  "ideal_customer_profile": {{
    "company_sizes": ["list of ideal company sizes"],
    "industries": ["list of target industries"],
    "growth_indicators": ["hiring", "funding", "expansion", etc],
    "hiring_signals": ["signals that indicate active hiring"],
    "funding_signals": ["signals that indicate recent funding"],
    "tech_stack_signals": ["tech signals relevant to this company"],
    "revenue_range": "estimated ideal revenue range",
    "employee_count_range": "ideal employee count"
  }},
  "avoid_patterns": ["patterns/characteristics to avoid"],
  "company_narrative": "2-3 sentence summary of the company's positioning"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await generate_completion(icp_prompt)
            
            # Check if response is error message
            if response.startswith("Error:") or "Gemini API is not configured" in response:
                print(f"ICP generation skipped: {response}")
                # Set defaults from company data and continue
                profile.company_narrative = company_text[:300]
                profile.ideal_customer_profile = {
                    "company_sizes": [],
                    "industries": profile.target_industries or [],
                    "growth_indicators": ["hiring", "funding"],
                    "hiring_signals": [],
                    "funding_signals": [],
                    "tech_stack_signals": profile.technologies or [],
                }
                profile.avoid_patterns = []
                profile.save()
                return CompanyService.serialize_profile(profile)
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                icp_data = json.loads(json_match.group())
                
                # Extract fields
                icp = icp_data.get('ideal_customer_profile', {})
                avoid_patterns = icp_data.get('avoid_patterns', [])
                narrative = icp_data.get('company_narrative', '')
                
                # Build signal keywords
                hiring_keywords = icp.get('hiring_signals', [])
                funding_keywords = icp.get('funding_signals', [])
                tech_keywords = icp.get('tech_stack_signals', [])
                
                # Update profile
                profile.ideal_customer_profile = icp
                profile.icp = icp
                profile.avoid_patterns = avoid_patterns
                profile.company_narrative = narrative
                profile.hiring_signal_keywords = hiring_keywords
                profile.funding_signal_keywords = funding_keywords
                profile.tech_signal_keywords = tech_keywords
                profile.save()
        except Exception as e:
            print(f"Error generating ICP: {e}")
            # Fallback - set basic defaults from company information
            profile.company_narrative = company_text[:300]
            profile.ideal_customer_profile = {
                "company_sizes": [],
                "industries": profile.target_industries or [],
                "growth_indicators": ["hiring", "funding"],
                "hiring_signals": [],
                "funding_signals": [],
                "tech_stack_signals": profile.technologies or [],
            }
            profile.avoid_patterns = []
            profile.save()
        
        return CompanyService.serialize_profile(profile)
    
    @staticmethod
    def _build_embedding_text(profile: CompanyProfile, portfolio_content: Dict = None) -> str:
        """Build comprehensive text for embedding including portfolio content"""
        parts = [
            f"Company: {profile.company_name}",
            f"Size: {profile.company_size}",
            f"Stage: {profile.company_stage}",
        ]
        
        if profile.company_description:
            parts.append(f"Description: {profile.company_description}")
        
        if profile.services:
            parts.append(f"Services: {', '.join(profile.services)}")
        
        if profile.expertise_areas:
            parts.append(f"Expertise: {', '.join(profile.expertise_areas)}")
        
        if profile.technologies:
            parts.append(f"Technologies: {', '.join(profile.technologies)}")
        
        if profile.target_industries:
            parts.append(f"Target Industries: {', '.join(profile.target_industries)}")
        
        if profile.target_locations:
            parts.append(f"Target Locations: {', '.join(profile.target_locations)}")
        
        if profile.team_expertise:
            parts.append(f"Team Skills: {', '.join(profile.team_expertise)}")

        link_hints = []
        if profile.company_website:
            link_hints.append(f"Website: {profile.company_website}")
        if profile.github_url:
            link_hints.append(f"GitHub: {profile.github_url}")
        if profile.linkedin_url:
            link_hints.append(f"LinkedIn: {profile.linkedin_url}")
        if profile.upwork_id:
            link_hints.append(f"Upwork: {profile.upwork_id}")
        if profile.portfolio_urls:
            link_hints.append(f"Additional Portfolios: {', '.join(profile.portfolio_urls)}")
        if link_hints:
            parts.append("Online Presence: " + " | ".join(link_hints))
        
        if profile.projects:
            project_texts = []
            for proj in profile.projects:
                proj_text = f"{proj.get('title')}: {proj.get('description')}"
                if proj.get('technologies'):
                    proj_text += f" (Tech: {', '.join(proj.get('technologies'))})"
                project_texts.append(proj_text)
            if project_texts:
                parts.append(f"Projects: {'; '.join(project_texts)}")
        
        # Include portfolio content if available
        if portfolio_content:
            combined_portfolio = combine_portfolio_content(portfolio_content)
            if combined_portfolio:
                parts.append(f"\nPortfolio & Web Content:\n{combined_portfolio}")
        
        return "\n".join(parts)
    
    @staticmethod
    def complete_setup(owner_id: str) -> dict:
        """Mark company setup as complete"""
        profile = CompanyProfile.objects(owner_id=owner_id).first()
        if not profile:
            raise ValueError("Company profile not found")
        
        profile.is_complete = True
        profile.setup_step = "complete"
        profile.save()
        
        return CompanyService.serialize_profile(profile)
