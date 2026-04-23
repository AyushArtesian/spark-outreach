"""Shared helpers for enforcing service-scope constraints in discovery queries."""

from typing import Any, List, Sequence, Set, Tuple
import re


SERVICE_ALIASES = {
    "web development": [
        "web app development",
        "website development",
        "website redesign",
        "website revamp",
        "frontend development",
        "backend development",
    ],
    "software development": [
        "custom software",
        "application development",
        "product engineering",
        "software engineering",
    ],
    "mobile app": [
        "app development",
        "mobile application",
        "android app",
        "ios app",
    ],
}

SERVICE_STOPWORDS = {
    "and",
    "for",
    "with",
    "from",
    "the",
    "services",
    "service",
    "solutions",
    "solution",
    "company",
    "development",
}

BLOCKED_OFFSCOPE_SERVICE_TERMS = {
    "microsoft dynamics",
    "dynamics 365",
    "power apps",
    "power automate",
    "sap",
    "oracle erp",
    "erp",
    "crm",
    "salesforce",
    "servicenow",
}


def normalize_service_list(value: Any) -> List[str]:
    """Normalize raw service values to a deduplicated lowercase list."""
    if not value:
        return []

    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = [str(item) for item in value]
    else:
        raw_items = [str(value)]

    cleaned: List[str] = []
    seen: Set[str] = set()
    for item in raw_items:
        normalized = re.sub(r"\s+", " ", str(item or "").strip().lower())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


def _build_allowed_terms(requested_services: Sequence[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    allowed_phrases: Set[str] = set()
    allowed_tokens: Set[str] = set()

    for service in requested_services:
        phrases = [service, *(SERVICE_ALIASES.get(service, []))]
        for phrase in phrases:
            normalized_phrase = re.sub(r"\s+", " ", phrase.strip().lower())
            if not normalized_phrase:
                continue
            allowed_phrases.add(normalized_phrase)
            for token in re.split(r"\W+", normalized_phrase):
                token = token.strip()
                if len(token) < 4 or token in SERVICE_STOPWORDS:
                    continue
                allowed_tokens.add(token)

    permitted_blocked_terms = {
        term
        for term in BLOCKED_OFFSCOPE_SERVICE_TERMS
        if any(term in phrase for phrase in allowed_phrases)
    }
    return allowed_phrases, allowed_tokens, permitted_blocked_terms


def is_query_in_service_scope(query: str, requested_services: Sequence[str]) -> bool:
    """Return True when query appears aligned with requested service scope."""
    requested = normalize_service_list(list(requested_services or []))
    if not requested:
        return True

    lowered = re.sub(r"\s+", " ", str(query or "").lower()).strip()
    if not lowered:
        return False

    allowed_phrases, allowed_tokens, permitted_blocked_terms = _build_allowed_terms(requested)

    for term in BLOCKED_OFFSCOPE_SERVICE_TERMS:
        if term in lowered and term not in permitted_blocked_terms:
            return False

    if any(phrase in lowered for phrase in allowed_phrases if len(phrase) >= 4):
        return True

    matched_tokens = 0
    for token in allowed_tokens:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            matched_tokens += 1
        if matched_tokens >= 2:
            return True
    return False
