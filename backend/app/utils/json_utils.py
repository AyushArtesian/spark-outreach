"""
Utility functions for JSON parsing and query sanitization
"""
import re
import json
from typing import Optional, Dict, Any, List


BAD_QUERY_FRAGMENTS = {
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
}


def _normalize_query_syntax(query: str) -> str:
    """Normalize malformed LLM query strings into executable search syntax."""
    text = str(query or "").strip()
    if not text:
        return ""

    # Normalize quote characters and casing around operators.
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bor\b", "OR", text, flags=re.IGNORECASE)

    # Repair frequent malformed funding phrase from LLM outputs.
    text = re.sub(
        r'"series\s*a"\s*b"',
        '"series a" OR "series b"',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'"series\s*a"\s+OR\s+"series\s*b"?',
        '"series a" OR "series b"',
        text,
        flags=re.IGNORECASE,
    )

    # If quote count is odd, remove quotes to avoid broken engine parsing.
    if text.count('"') % 2 != 0:
        text = text.replace('"', "")

    # Remove duplicate operators introduced by model drift.
    text = re.sub(r"\bOR\s+OR\b", "OR", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -")

    return text


def extract_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract first JSON object from text, stripping Qwen think-traces.
    Handles: {...json...}, {"queries":[...]}, markdown code blocks.
    """
    if not raw_text:
        return None

    text = str(raw_text).strip()

    # Strip <think>...</think> blocks (Qwen reasoning traces)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.strip()

    # Try markdown code block: ```json...```
    json_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_block_match:
        text = json_block_match.group(1).strip()

    # Try to find {...} or [...] object
    start_idx = -1
    for i, char in enumerate(text):
        if char in ['{', '[']:
            start_idx = i
            break

    if start_idx == -1:
        return None

    # Parse from start_idx to end, finding matching bracket
    open_char = text[start_idx]
    close_char = '}' if open_char == '{' else ']'
    depth = 0
    end_idx = -1

    for i in range(start_idx, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    if end_idx == -1:
        return None

    json_str = text[start_idx : end_idx + 1]

    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def sanitize_queries(candidates: List[Any], max_queries: int) -> List[str]:
    """
    Convert query candidates to clean list of strings.
    Handles list of strings, dicts with 'query' key, or mixed.
    """
    result = []
    seen = set()
    for item in (candidates or []):
        if isinstance(item, str):
            cleaned = item.strip()
        elif isinstance(item, dict):
            cleaned = (item.get("query") or item.get("q") or "").strip()
        else:
            cleaned = str(item).strip()

        cleaned = _normalize_query_syntax(cleaned)
        lowered = cleaned.lower()

        if any(fragment in lowered for fragment in BAD_QUERY_FRAGMENTS):
            continue

        if len(cleaned.split()) < 4:
            continue

        if lowered in seen:
            continue

        if cleaned:
            result.append(cleaned)
            seen.add(lowered)

        if len(result) >= max_queries:
            break

    return result
