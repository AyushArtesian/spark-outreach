"""
Query intent scoring and signal extraction for lead discovery
"""
import re
from typing import Optional, List, Dict, Any
from app.schemas.query_schemas import QueryScore


# Realistic operator patterns that actually work in Google search
REALISTIC_OPERATORS = {
    "intitle:": ["intitle:hiring", "intitle:careers", "intitle:rfp", "intitle:jobs"],
    "inurl:": ["inurl:careers", "inurl:jobs", "inurl:hiring", "inurl:about"],
}

UNREALISTIC_PATTERNS = [
    "intitle:seriesc",
    "intitle:seriesb", 
    "intitle:series a",
    "intitle:vendor-evaluation",
    "intitle:ipo-prep",
    "intitle:acquisition",
    "intitle:technical",
    "intitle:engineering",
    "intitle:technical-",
    "intitle:engineering-",
    "inurl:hiring-technical-lead",
    "inurl:engineering-manager",
    "inurl:technical-debt",
    "inurl:engineering-lead",
    "inurl:engineering-careers",
]

# Whitelist of actually realistic operators
WHITELIST_INTITLE = ["hiring", "careers", "jobs", "rfp", "about"]
WHITELIST_INURL = ["careers", "jobs", "hiring", "about"]

INSTRUCTIONAL_QUERY_FRAGMENTS = [
    "original queries mention",
    "queries mention things like",
    "things like",
    "return only json",
    "output only json",
    "json schema",
    "query_text",
    "rules:",
    "example good",
    "example bad",
    "rewrite these queries",
    "current queries:",
]


def is_instructional_query(query: str) -> bool:
    """Detect model-meta/instructional text that should never be used as a web search query."""
    text = re.sub(r"\s+", " ", str(query or "").strip().lower())
    if not text:
        return True

    if any(fragment in text for fragment in INSTRUCTIONAL_QUERY_FRAGMENTS):
        return True

    if re.match(r"^(generate|return|rewrite|create|provide)\b", text):
        return True

    # Catch generic prose outputs like "original queries mention ... etc"
    if "queries" in text and "etc" in text:
        return True

    return False


def extract_intent_signals(query: str) -> List[str]:
    """Extract intent signals from query text."""
    text = (query or "").lower()
    signal_map = {
        "hiring": [
            "hiring",
            "we are hiring",
            "engineering manager",
            "careers",
            "inurl:careers",
            "intitle:careers",
            "hiring engineers",
            "hiring talent",
        ],
        "funding": [
            "series a",
            "series b",
            "series c",
            "series",
            "funded",
            "venture backed",
            "raised",
            "funding",
            "ipo",
            "acquisition",
            "acquired",
        ],
        "expansion": [
            "expanding",
            "scale",
            "scaling",
            "new market",
            "growth stage",
            "partnership",
            "partner",
        ],
        "modernization": [
            "replatform",
            "migration",
            "to migrate",
            "legacy",
            "modernization",
            "headless",
            "technical debt",
            "upgrade",
            "transform",
        ],
        "buying_intent": [
            "looking for",
            "seeking",
            "vendor",
            "outsource",
            "agency partner",
            "rfp",
            "request for proposal",
            "rfi",
            "procurement",
        ],
    }

    matched = []
    for signal, tokens in signal_map.items():
        if any(token in text for token in tokens):
            matched.append(signal)
    return matched


def has_unrealistic_operators(query: str) -> bool:
    """Check if query has hallucinated/unrealistic operators that won't work in Google."""
    text = (query or "").lower()
    
    # Check for known unrealistic patterns
    for pattern in UNREALISTIC_PATTERNS:
        if pattern in text:
            return True
    
    # Strict whitelist check: only allow specific intitle: values
    if "intitle:" in text:
        parts = text.split("intitle:")
        for part in parts[1:]:
            # Extract what comes after intitle: (up to next space or end)
            op_value = part.split()[0].strip('"\'')
            # Only allow whitelisted values
            if op_value not in WHITELIST_INTITLE:
                return True
    
    # Strict whitelist check: only allow specific inurl: values
    if "inurl:" in text:
        parts = text.split("inurl:")
        for part in parts[1:]:
            op_value = part.split()[0].strip('"\'')
            # Only allow whitelisted values
            if op_value not in WHITELIST_INURL:
                return True
    
    return False


def score_query_intent(query: str, location_hint: Optional[str] = None) -> float:
    """
    Score a query for lead-buying intent and maturity signals (0-1 scale).
    
    Scoring factors:
    - Single signal: +0.20
    - Multi-signal (2+): +0.25 per signal + 0.20 bonus
    - Operators (intitle:, inurl:, phrases): +0.12 each
    - Location match: +0.10
    - Generic penalties: -0.15 each
    - Unrealistic operators: -0.50 (CRITICAL)
    - Too short: -0.12
    """
    text = (query or "").lower()
    if not text:
        return 0.0

    if is_instructional_query(query):
        return 0.0

    score = 0.0
    signals = extract_intent_signals(text)

    # CRITICAL: Penalize unrealistic operators heavily
    if has_unrealistic_operators(query):
        return 0.15  # Very low score, won't pass filtering

    # Signal scoring: weight each signal, but boost multi-signal queries
    signal_count = len(signals)
    if signal_count == 0:
        score += 0.0
    elif signal_count == 1:
        score += 0.20  # Single signal gets 0.20
    else:
        # Multi-signal bonus: 0.25 per signal + 0.20 bonus for combinations
        score += 0.25 * signal_count + 0.20

    # Operator bonus (intitle:, inurl:, phrase quotes) - but only realistic ones
    operator_count = sum(1 for op in ["intitle:", "inurl:"] if op in text)
    phrase_count = text.count('"') // 2  # Count phrase quotes
    total_operators = min(operator_count + phrase_count, 3)  # Cap at 3
    score += 0.12 * total_operators

    # Location bonus
    if location_hint and str(location_hint).strip().lower() in text:
        score += 0.10

    # Generic pattern penalties (apply for each found)
    generic_penalties = [
        "best ",
        "top ",
        "list of",
        "companies in",
        "website design",
        "web development companies",  # Too generic
    ]
    for token in generic_penalties:
        if token in text:
            score -= 0.15

    # Length penalty for too-short queries
    if len(text.split()) < 5:
        score -= 0.12

    return max(0.0, min(1.0, score))


def score_query_specificity(query: str) -> float:
    """
    Score query for narrowness/specificity (0-1 scale).
    More specific queries = fewer results = better ICP match.
    
    Factors:
    - Length: 10-15 words = specific, <5 words = generic
    - Location included: +0.15
    - Multiple constraints (operator + phrases): +0.10 each
    - Industry/vertical keywords: +0.10 per keyword
    - Company-context keywords (e.g., "power platform", "cloud", "modern"): +0.10 per keyword
    """
    text = (query or "").lower()
    if not text:
        return 0.0
    
    score = 0.0
    word_count = len(text.split())
    
    # Length score: 10-15 words is optimal, penalize too short/long
    if 10 <= word_count <= 15:
        score += 0.30  # Perfect specificity range
    elif 8 <= word_count < 10:
        score += 0.20  # Good
    elif 5 <= word_count < 8:
        score += 0.10  # Acceptable
    elif word_count < 5:
        score -= 0.20  # Too vague
    else:  # >15 words
        score += 0.15  # More specific but maybe too wordy
    
    # Constraint count (more constraints = narrower results)
    constraint_count = 0
    if "intitle:" in text or "inurl:" in text:
        constraint_count += 1
    if '"' in text:  # Phrase search
        constraint_count += 1
    if "site:" in text:
        constraint_count += 1
    
    score += 0.10 * min(constraint_count, 3)  # Cap at 3
    
    # Industry/vertical keywords (shows context awareness)
    verticals = [
        "saas", "fintech", "ecommerce", "healthtech", "insurtech",
        "edtech", "real estate", "logistics", "manufacturing",
        "microsoft", "azure", "power platform", "sharepoint",
        "cloud", "legacy", "modernization", "migration",
    ]
    vertical_count = sum(1 for v in verticals if v in text)
    score += 0.05 * min(vertical_count, 3)  # Cap at 3
    
    # Growth stage keywords (early signal)
    growth_signals = ["series a", "series b", "series c", "seed", "growth stage", "scaling"]
    growth_count = sum(1 for g in growth_signals if g in text)
    score += 0.05 * min(growth_count, 2)
    
    return max(0.0, min(1.0, score))


def rank_high_intent_queries(
    queries: List[str],
    location_hint: Optional[str],
    max_queries: int,
    min_score: float = 0.50,
) -> List[QueryScore]:
    """
    Rank queries by COMBINED intent + specificity scores.
    Preference: Specific + high-intent queries over broad generic ones.
    
    Scoring: 70% intent + 30% specificity
    - Intent: Does it have buying signals?
    - Specificity: Is it narrow/contextual enough to find exact ICPs?
    
    Returns list of QueryScore objects sorted by combined score descending.
    """
    ranked = []
    for query in queries:
        if is_instructional_query(query):
            continue

        intent_score = score_query_intent(query, location_hint=location_hint)
        specificity_score = score_query_specificity(query)
        
        # Combine: Intent (70%) weighted higher than specificity (30%)
        # But both must contribute - don't want generic intent or overly narrow vague queries
        combined_score = (intent_score * 0.70) + (specificity_score * 0.30)
        
        signals = extract_intent_signals(query)
        
        # Higher threshold than before: need both quality AND specificity
        if combined_score < min_score:
            continue
        
        ranked.append(
            QueryScore(
                query=query,
                score=round(combined_score, 3),
                signals=signals,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:max_queries]


def estimate_search_effectiveness(queries: List[str]) -> float:
    """
    Estimate what % of queries are likely to return results (0-1 scale).
    
    Returns average effectiveness score. If < 0.5, queries are too unrealistic.
    
    Factors:
    - Unrealistic operators: 0.0 (will return 0 results)
    - Good operators (intitle:careers, inurl:jobs): 0.8+
    - Phrase searches: 0.6+
    - Plain text searches: 0.4
    """
    if not queries:
        return 0.0
    
    scores = []
    for query in queries:
        text = query.lower()
        score = 0.5  # Default baseline
        
        # Unrealistic = no results
        if has_unrealistic_operators(query):
            score = 0.0
        # Good realistic operators = high chance
        elif "intitle:careers" in text or "intitle:jobs" in text:
            score = 0.85
        elif "inurl:careers" in text or "inurl:jobs" in text:
            score = 0.80
        elif "intitle:" in text or "inurl:" in text:
            score = 0.65
        elif '"' in text:  # Phrase search
            score = 0.60
        else:  # Plain text
            score = 0.40
        
        scores.append(score)
    
    return sum(scores) / len(scores)
