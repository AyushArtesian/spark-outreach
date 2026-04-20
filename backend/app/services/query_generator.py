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
    Create deterministic buyer-intent queries to find companies SEEKING our services.
    Generates prospect-finding queries: companies looking for partners/vendors for these services.
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

    # CRITICAL CHANGE: Generate queries that find BUYERS of services
    # Focus on: "seeking partner", "RFP", "looking for vendor", "implementation partner"
    
    # Pattern 1: Companies seeking implementation partners
    for service in top_services[:2]:
        generated.append(f'{service} "implementation partner" {location}')
        generated.append(f'looking for {service} company "{location}"')
        generated.append(f'{service} "vendor selection" OR "partner" {location}')
    
    # Pattern 2: RFP and procurement signals
    for service in top_services[:2]:
        generated.append(f'{service} "RFP" OR "request for proposal" {location}')
        generated.append(f'{service} consulting "contact us" {location}')
        generated.append(f'hire {service} company OR consultant {location}')
    
    # Pattern 3: Digital transformation (companies buying services for modernization)
    for industry in target_industries[:2]:
        generated.append(f'{industry} "digital transformation" {service_short} {location}')
        generated.append(f'{industry} modernization {service_short} services {location}')
    
    # Pattern 4: Service providers/agencies in target location
    for industry in target_industries[:2]:
        generated.append(f'{industry} {service_short} "agency" OR "firm" {location}')
        generated.append(f'{industry} {service_short} services {location} company')
    
    # Pattern 5: High-growth companies (likely to buy services)
    generated.append(f'high growth {target_industries[0]} startups {location} {service_short}')
    generated.append(f'VC backed {target_industries[0]} {location} hiring tech roles')
    
    # Pattern 6: Companies with recent funding (likely buyers)
    for industry in target_industries[:1]:
        generated.append(f'{industry} "series A" OR "series B" {location} company')
        generated.append(f'{industry} raised funding {location} expansion')
    
    # Pattern 7: Expansion signals (companies scaling = need vendors)
    generated.append(f'{target_industries[0]} companies expanding {location} {service_short}')
    generated.append(f'{target_industries[0]} growth stage {service_short} initiatives {location}')
    
    # Pattern 8: Direct service request patterns
    for service in top_services[:1]:
        generated.append(f'need {service} partner {location}')
        generated.append(f'seeking {service} specialized firm {location}')
        generated.append(f'{service} quote OR proposal {location}')
    
    # Pattern 9: Industry-specific service needs
    if technologies:
        tech_name = technologies[0]
        generated.append(f'{target_industries[0]} {tech_name} migration {location} services')
        generated.append(f'implement {tech_name} {target_industries[0]} {location}')
    
    # Pattern 10: User-provided context with buyer focus
    if user_query:
        generated.insert(0, f'{user_query.strip()} services {location}')
        generated.insert(1, f'{user_query.strip()} partner {location}')

    return sanitize_queries(generated, max_queries=max_queries)
