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
    
    All templates enforce 2+ signal combinations per service:
    - Hiring + Growth Stage
    - Funding + Expansion
    - Migration + RFP
    - Growth + Modernization
    - Procurement + Scaling
    - Acquisition + Technical
    
    Generates queries for TOP 2-3 SERVICES to maximize lead discovery.
    """
    filters = filters or {}
    profile = company_profile or {}

    location = str(filters.get("location") or "").strip()
    if not location:
        target_locs = profile.get("target_locations") or []
        if target_locs:
            location = str(target_locs[0]).strip()
    location = _normalize_location_text(location) or location

    industry = str(filters.get("industry") or "").strip()
    if not industry or industry.lower() == "all":
        industries = profile.get("target_industries") or []
        industry = str(industries[0]).strip() if industries else "software"

    services = filters.get("services") or profile.get("services") or []
    # Use top 2-3 services instead of just the first one
    top_services = [str(s).strip() for s in services[:3] if str(s).strip()]
    if not top_services:
        top_services = ["web development"]

    parts_base = {
        "loc": location or "india",
        "industry": industry,
    }

    templates = [
        # Multi-signal: Hiring + Growth Stage
        'intitle:careers "{industry}" "{loc}" "series a" OR "series b" "hiring engineer" "{service}"',
        '"{industry}" "{loc}" "hiring engineers" "technical stack" "{service}"',
        # Multi-signal: Funding + Expansion
        '"{industry}" "{loc}" "series a" "hiring engineers" "{service}"',
        '"{industry}" "{loc}" "series b" "scaling platform" "{service}"',
        # Multi-signal: Migration + RFP
        '"{industry}" "{loc}" "migration to" OR "replatform" "legacy" "vendor selection" "{service}"',
        '"{industry}" "{loc}" "technical migration" OR "platform upgrade" "RFP" "{service}"',
        # Multi-signal: Growth + Modernization
        '"{industry}" "{loc}" "expanding" "modernizing" OR "digital transformation" "{service}"',
        '"{industry}" "{loc}" "growing team" "tech upgrade" "{service}"',
        # Multi-signal: Procurement + Scaling
        '"{industry}" "{loc}" "vendor evaluation" OR "procurement" "scaling" "{service}"',
        # Multi-signal: Acquisition + Technical
        '"{industry}" "{loc}" "acquired company" OR "post-acquisition" "technology integration" "{service}"',
    ]

    generated = []
    for service in top_services:
        parts = {**parts_base, "service": service}
        for template in templates[:5]:  # Use 5 templates per service for variety
            try:
                generated.append(template.format(**parts))
            except (KeyError, TypeError):
                continue
    
    # Add primary user query with location
    generated.insert(0, f'"{user_query.strip()}" "{parts_base["loc"]}"')
    
    return sanitize_queries(generated, max_queries=max_queries)
