"""Deterministic buyer-intent query generation for lead discovery fallback."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.utils.json_utils import sanitize_queries


LOCATION_ALIASES = {
    "gurgoan": "gurgaon",
    "gurugram": "gurgaon",
    "banglore": "bangalore",
    "bengalure": "bangalore",
    "new delhi": "delhi",
}

PRIORITY_BUYER_INDUSTRIES = [
    "manufacturing",
    "retail",
    "healthcare",
    "finance",
    "logistics",
    "real estate",
    "hospitality",
]


def _service_category(service: str) -> str:
    text = (service or "").strip().lower()
    if not text:
        return "digital services"
    if "dynamics" in text or "erp" in text or "power" in text:
        return "ERP implementation"
    if "web" in text or "website" in text:
        return "web development"
    if "mobile" in text:
        return "mobile app development"
    return service


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
    Create deterministic buyer-intent queries to find COMPANIES WHO BUY services.

    Query families:
    - Type A: buyer-intent web queries (companies looking for vendors/partners)
    - Type B: company-discovery queries (target accounts likely to buy)
    """
    filters = filters or {}
    profile = company_profile or {}

    location = str(filters.get("location") or "").strip()
    if not location:
        target_locs = profile.get("target_locations") or []
        if target_locs:
            location = str(target_locs[0]).strip()
    location = _normalize_location_text(location) or location or "india"

    industry_hint = str(filters.get("industry") or "").strip().lower()
    target_industries = [str(ind).strip().lower() for ind in (profile.get("target_industries") or []) if str(ind).strip()]
    if industry_hint and industry_hint != "all":
        target_industries.insert(0, industry_hint)
    target_industries = [ind for ind in target_industries if ind and ind != "software"]
    if not target_industries:
        target_industries = PRIORITY_BUYER_INDUSTRIES[:3]

    services = filters.get("services") or profile.get("services") or []
    top_services = [str(s).strip() for s in services[:3] if str(s).strip()]
    if not top_services:
        top_services = ["web development"]

    current_year = datetime.utcnow().year
    generated: List[str] = []

    # Type A: Buyer-intent queries (procurement/need/vendor-search behavior).
    for service in top_services[:2]:
        category = _service_category(service)
        generated.extend(
            [
                f"companies in {location} need {category}",
                f"{location} startups looking for {category} agency",
                f"{category} outsourcing {location}",
                f"{location} company web application vendor selection",
                f"site:linkedin.com/company \"{location}\" \"looking for\" \"{category}\"",
                f"site:clutch.co \"{location}\" \"{category}\"",
                f"{location} digital transformation projects {current_year} {category}",
            ]
        )
        if "dynamics" in service.lower() or "erp" in service.lower():
            generated.extend(
                [
                    f"{location} companies using SAP OR Oracle ERP modernization",
                    f"{location} ERP implementation partner requirement",
                    f"{location} manufacturing company IT requirements dynamics 365",
                ]
            )

    # Type B: Company-discovery queries (target accounts to approach).
    for industry in target_industries[:3]:
        generated.extend(
            [
                f"top {industry} companies in {location}",
                f"funded {industry} startups {location} {current_year}",
                f"{industry} companies {location} digital transformation",
                f"{industry} companies {location} IT manager OR CTO",
                f"site:linkedin.com/company \"{location}\" \"{industry}\" \"IT Manager\"",
            ]
        )

    # Keep user wording while forcing buyer intent + location fence.
    if user_query:
        query_seed = " ".join(str(user_query).split())
        generated.insert(0, f"{query_seed} companies in {location} looking for implementation partner")
        generated.insert(1, f"{query_seed} buyer intent {location}")

    return sanitize_queries(generated, max_queries=max_queries)
