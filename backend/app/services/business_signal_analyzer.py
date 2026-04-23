"""Business signal analysis for buyer-intent discovery."""

from typing import Dict, Optional
import re


def analyze_business_signals(
    snippet: str,
    website_text: str,
    service_focus: Optional[list] = None,
    search_query: Optional[str] = None,
) -> Dict[str, object]:
    """Detect hiring/scaling/SaaS/tech intent signals using rule + semantic heuristics.

    Returns dict with:
    - signals: list of detected signals (hiring, scaling, saas_platform, tech_heavy, funding)
    - confidence: 0-1 composite score from signal strength + semantic hints
    - tech_relevance: 0-1 score for technical relevance to service focus
    - seller_marketing_score: 0-1 score for vendor/seller marketing language
    - is_seller_intent: True when text strongly indicates provider-side marketing copy
    - reason: list of reason strings explaining the signals
    """
    snippet_text = (snippet or "").lower()
    website_summary = (website_text or "").lower()
    content_text = f"{snippet_text} {website_summary}".strip()
    searchable = content_text

    rule_map = {
        "hiring": [
            "hiring", "we are hiring", "join our team", "open positions", "open roles",
            "careers page", "engineering careers", "careers at", "now hiring",
            "career opportunities", "hiring engineers", "hiring developers",
        ],
        "scaling": [
            "scaling", "hypergrowth", "rapid growth", "expanding", "growth stage",
            "scale platform", "scaling infrastructure", "growing team",
        ],
        "saas_platform": [
            "saas", "platform", "subscription", "multi-tenant", "product-led",
            "b2b software", "cloud-based", "software-as-a-service", "software platform",
        ],
        "tech_heavy": [
            "api", "backend", "microservices", "cloud", "devops",
            "data platform", "engineering infrastructure", "technology stack",
        ],
        "funding": [
            "series a", "series b", "funded startup", "venture capital",
            "raised funding", "investor backed", "vc funded", "angel investors",
        ],
    }

    weights = {
        "hiring": 0.30,
        "scaling": 0.25,
        "saas_platform": 0.22,
        "tech_heavy": 0.18,
        "funding": 0.15,
    }

    detected = []
    reasons = []
    strength = 0.0

    for signal, tokens in rule_map.items():
        matched = [token for token in tokens if token in searchable]
        if not matched:
            continue
        detected.append(signal)
        strength += weights.get(signal, 0.0)
        reasons.append(f"{signal} signal via: {', '.join(matched[:2])}")

    service_terms = [str(s).lower() for s in (service_focus or []) if str(s).strip()]
    service_hits = []
    for service in service_terms:
        for token in [t for t in re.split(r"\W+", service) if len(t) > 2]:
            if token in searchable:
                service_hits.append(token)

    tech_relevance = 0.0
    if service_terms:
        tech_relevance = min(1.0, 0.25 + 0.15 * len(set(service_hits)))
    else:
        tech_relevance = 0.45 if "tech_heavy" in detected else 0.25

    if service_hits:
        reasons.append(f"service relevance via: {', '.join(sorted(set(service_hits))[:4])}")

    semantic_hint = 0.0

    product_indicators = [
        "product company", "platform company", "startup", "b2b saas",
        "product-led growth", "venture backed", "series a startup", "series b startup",
    ]
    if any(t in searchable for t in product_indicators):
        semantic_hint += 0.18

    if any(t in searchable for t in ["saas", "subscription", "platform", "cloud product"]):
        semantic_hint += 0.10

    anti_indicators = [
        "staff augmentation", "outsourcing partner", "hire our developers",
        "it consulting firm", "agency model", "freelance marketplace",
    ]
    if any(t in searchable for t in anti_indicators):
        semantic_hint -= 0.20

    seller_marketing_phrases = [
        "we provide",
        "we offer",
        "our services",
        "our solutions",
        "hire us",
        "contact us",
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
    seller_service_phrases = [
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

    seller_marketing_hits = [phrase for phrase in seller_marketing_phrases if phrase in searchable]
    seller_service_hits = [phrase for phrase in seller_service_phrases if phrase in searchable]

    seller_marketing_score = 0.0
    if seller_marketing_hits:
        seller_marketing_score += 0.30
    if seller_service_hits:
        seller_marketing_score += min(0.30, 0.12 * len(set(seller_service_hits)))

    if re.search(r"\b(if|when)\s+you\s+(need|require|are looking for|looking for)\b", searchable):
        seller_marketing_score += 0.20
    if re.search(r"\b(we|our team)\s+(offer|provide|deliver)\b", searchable):
        seller_marketing_score += 0.18

    strict_procurement_tokens = [
        "invites bids",
        "issued by",
        "bid submission",
        "tender notice",
        "expression of interest",
        "proposal due",
        "request for quotation",
        "rfq",
        "request for information",
        "rfi",
    ]
    if any(token in searchable for token in strict_procurement_tokens):
        seller_marketing_score = max(0.0, seller_marketing_score - 0.20)

    if seller_marketing_score > 0.0:
        semantic_hint -= min(0.45, seller_marketing_score)
        reasons.append(
            f"seller intent markers via: {', '.join((seller_marketing_hits + seller_service_hits)[:3])}"
        )

    confidence = max(0.0, min(1.0, strength + semantic_hint))

    return {
        "signals": sorted(set(detected)),
        "confidence": confidence,
        "tech_relevance": max(0.0, min(1.0, tech_relevance)),
        "seller_marketing_score": max(0.0, min(1.0, seller_marketing_score)),
        "is_seller_intent": seller_marketing_score >= 0.45,
        "reason": reasons,
    }
