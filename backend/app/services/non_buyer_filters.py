"""Shared non-buyer and seller-marketing filters for lead discovery."""

import re


SERVICE_PROVIDER_PHRASES = [
    "web designing company",
    "web development company",
    "software development company",
    "digital agency",
    "design agency",
    "ui ux studio",
    "consulting services",
    "outsourcing services",
    "it services company",
    "app development company",
]

SELLER_MARKETING_PHRASES = [
    "we provide",
    "we offer",
    "our services",
    "our solutions",
    "hire us",
    "contact us today",
    "request a quote",
    "get quote",
    "book a demo",
    "schedule a call",
    "if you're looking for",
    "if you are looking for",
    "you are at the right place",
    "at the right place",
    "submit rfp",
    "attach your rfp",
]

SELLER_SERVICE_TERMS = [
    "web development",
    "software development",
    "app development",
    "mobile app development",
    "development services",
    "it consulting",
    "digital transformation consulting",
    "staff augmentation",
    "outsourcing",
    "dynamics 365",
    "power apps",
    "erp implementation",
]

DIRECTORY_PHRASES = [
    "top 10",
    "top 50",
    "top 100",
    "list of",
    "directory",
    "best companies",
    "company rankings",
]

JOB_PORTAL_PHRASES = [
    "job portal",
    "find jobs",
    "freelance jobs",
    "hiring platform",
]

GOVERNMENT_EDU_PHRASES = [
    "government",
    "department",
    "ministry",
    "university",
    "college",
    "school",
    "institute",
]

STRICT_PROCUREMENT_TOKENS = [
    "invites bids",
    "issued by",
    "tender notice",
    "proposal due",
    "bid submission",
    "request for quotation",
    "rfq",
    "request for information",
    "rfi",
]


def has_strict_procurement_signal(text: str) -> bool:
    """Return True when text has explicit procurement/tender indicators."""
    lowered = str(text or "").lower()
    return any(token in lowered for token in STRICT_PROCUREMENT_TOKENS)


def detect_non_buyer_reason(company_name: str, text_blob: str) -> str:
    """Detect non-buyer/service-provider entities and return reason string."""
    text = f"{str(company_name or '').lower()} {str(text_blob or '').lower()}"

    for phrase in SERVICE_PROVIDER_PHRASES:
        if phrase in text:
            return f"service_provider:{phrase}"

    has_marketing_phrase = any(phrase in text for phrase in SELLER_MARKETING_PHRASES)
    has_seller_service_term = any(term in text for term in SELLER_SERVICE_TERMS)
    if has_marketing_phrase and has_seller_service_term:
        return "service_provider:seller_marketing_copy"

    if re.search(r"\b(if|when)\s+you\s+(need|require|are looking for|looking for)\b", text) and has_seller_service_term:
        return "service_provider:second_person_service_pitch"

    for phrase in DIRECTORY_PHRASES:
        if phrase in text:
            return f"directory:{phrase}"

    for phrase in JOB_PORTAL_PHRASES:
        if phrase in text:
            return f"job_portal:{phrase}"

    for phrase in GOVERNMENT_EDU_PHRASES:
        if phrase in text:
            return f"non_buyer:{phrase}"

    return ""
