"""
Deterministic high-intent query generation for lead discovery fallback
"""
from typing import Optional, List, Dict, Any
from app.utils.json_utils import sanitize_queries


def build_high_intent_fallback_queries(
    user_query: str,
    filters: Optional[Dict[str, Any]],
    company_profile: Optional[Dict[str, Any]],
    max_queries: int,
) -> List[str]:
    """
    Create deterministic high-intent queries if LLM output quality is weak.
    
    All templates enforce 2+ signal combinations:
    - Hiring + Growth Stage
    - Funding + Expansion
    - Migration + RFP
    - Growth + Modernization
    - Procurement + Scaling
    - Acquisition + Technical
    """
    filters = filters or {}
    profile = company_profile or {}

    location = str(filters.get("location") or "").strip()
    if not location:
        target_locs = profile.get("target_locations") or []
        if target_locs:
            location = str(target_locs[0]).strip()

    industry = str(filters.get("industry") or "").strip()
    if not industry or industry.lower() == "all":
        industries = profile.get("target_industries") or []
        industry = str(industries[0]).strip() if industries else "software"

    services = filters.get("services") or profile.get("services") or []
    primary_service = str(services[0]).strip() if services else "web development"

    parts = {
        "loc": location or "india",
        "industry": industry,
        "service": primary_service,
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

    generated = [template.format(**parts) for template in templates]
    generated.insert(0, f'"{user_query.strip()}" "{parts["loc"]}"')
    return sanitize_queries(generated, max_queries=max_queries)
