"""
Deterministic high-intent query generation for lead discovery fallback
"""
from typing import Optional, List, Dict, Any
from app.utils.json_utils import sanitize_queries


LOCATION_ALIASES = {
    "gurgoan": "gurgaon",
    "gurugram": "gurgaon",
    "banglore": "bangalore",
    "bengalure": "bangalore",
    "new delhi": "delhi",
}


def _normalize_location_text(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    normalized = text
    for src, dst in LOCATION_ALIASES.items():
        normalized = normalized.replace(src, dst)
    return normalized


def build_high_intent_fallback_queries(
    user_query: str,
    filters: Optional[Dict[str, Any]],
    company_profile: Optional[Dict[str, Any]],
    max_queries: int,
) -> List[str]:
    """
    Create deterministic high-intent queries if LLM output quality is weak.
    Generates prospect-finding queries: companies in target industries needing these services.
    """
    filters = filters or {}
    profile = company_profile or {}

    location = str(filters.get("location") or "").strip()
    if not location:
        target_locs = profile.get("target_locations") or []
        if target_locs:
            location = str(target_locs[0]).strip()
    location = _normalize_location_text(location) or location or "india"

    # Get target industries and services from profile
    target_industries = [
        str(ind).strip().lower() 
        for ind in (profile.get("target_industries") or [])
        if str(ind).strip()
    ]
    if not target_industries:
        target_industries = ["software", "technology"]

    services = filters.get("services") or profile.get("services") or []
    top_services = [str(s).strip() for s in services[:3] if str(s).strip()]
    if not top_services:
        top_services = ["development"]

    technologies = [str(t).strip() for t in (profile.get("technologies") or []) if str(t).strip()]

    # Build service keywords for queries
    service_short = " ".join(top_services[0].split()[:2]) if top_services else "development"
    
    generated = []

    # STRATEGY: Generate queries that find prospect companies (companies that NEED these services)
    # not just generic service provider listings
    
    # Pattern 1: Target industry + hiring signal
    for industry in target_industries[:2]:
        generated.append(f'{industry} companies "hiring" {service_short} engineers {location}')
        generated.append(f'{industry} startups recruiting {service_short} developers {location}')
    
    # Pattern 2: Target industry + funding signal
    for industry in target_industries[:2]:
        generated.append(f'{industry} companies "funded" OR "series a" {location} {service_short}')
        generated.append(f'venture backed {industry} startups {location} expanding')
    
    # Pattern 3: Target industry + modernization/digital transformation
    for industry in target_industries[:2]:
        generated.append(f'{industry} "digital transformation" {location} {service_short}')
        generated.append(f'{industry} companies modernizing legacy systems {location}')
    
    # Pattern 4: Target industry + expansion signals
    generated.append(f'{target_industries[0]} companies growing {location} hiring technical talent')
    generated.append(f'scale {target_industries[0]} platforms {location} development')
    
    # Pattern 5: Service-specific prospect queries
    for service in top_services[:2]:
        generated.append(f'{service} "implementation partner" {location} OR remote')
        generated.append(f'{service} consulting services {location} companies')
    
    # Pattern 6: Technology + industry combinations (if tech stack available)
    if technologies and target_industries:
        tech_name = technologies[0]
        industry_name = target_industries[0]
        generated.append(f'{industry_name} companies using {tech_name} {location} hiring')
        generated.append(f'{tech_name} projects {industry_name} sector {location} recruitment')
    
    # Pattern 7: RFP and procurement signals in target industries
    for industry in target_industries[:1]:
        generated.append(f'{industry} "RFP" OR "vendor selection" {location} {service_short}')
        generated.append(f'{industry} procurement {service_short} solutions {location}')
    
    # Pattern 8: Job board and hiring page signals
    for industry in target_industries[:1]:
        generated.append(f'{industry} company careers page {service_short} {location}')
        generated.append(f'{industry} tech jobs {location} companies hiring')
    
    # Pattern 9: Growth stage signals with industry focus
    generated.append(f'post-series-a {target_industries[0]} companies {location}')
    generated.append(f'high growth {target_industries[0]} startups {location} {service_short}')
    
    # Pattern 10: Primary user query with enhanced context
    if user_query:
        generated.insert(0, f'{user_query.strip()} {location} companies OR startups')

    return sanitize_queries(generated, max_queries=max_queries)
