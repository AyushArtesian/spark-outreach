"""
Utility functions for JSON parsing and query sanitization
"""
import re
import json
from typing import Optional, Dict, Any, List


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
    for item in (candidates or []):
        if isinstance(item, str):
            cleaned = item.strip()
        elif isinstance(item, dict):
            cleaned = (item.get("query") or item.get("q") or "").strip()
        else:
            cleaned = str(item).strip()

        if cleaned and cleaned not in result:
            result.append(cleaned)

        if len(result) >= max_queries:
            break

    return result
