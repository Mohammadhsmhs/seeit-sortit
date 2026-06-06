"""Robust LLM response parsers for real model output.

Handles the messy reality of freeform LLM responses: extra whitespace,
markdown code blocks, numbered lists, preamble text, case mismatches, etc.
"""

from __future__ import annotations

import json
import logging
import re

from src.models.base import IssueCategory

logger = logging.getLogger(__name__)

# Pre-compute the valid category values (excluding Uncategorised)
_VALID_CATEGORIES: list[str] = [
    c.value for c in IssueCategory if c != IssueCategory.UNCATEGORISED
]
_CATEGORY_LOWER_MAP: dict[str, str] = {c.lower(): c for c in _VALID_CATEGORIES}


def parse_category(raw_response: str) -> str:
    """Parse an LLM response into a valid IssueCategory value.

    Tries these strategies in order:
      1. Exact match (case-insensitive)
      2. Strip common LLM prefixes ("Category: ", "1. ", etc.)
      3. Contains match (category name inside response, or vice versa)
      4. JSON extraction (if response is JSON with a "category" key)
      5. Numbered list extraction ("1. Waste and Fly-Tipping")
      6. Word-overlap fuzzy match (threshold 0.4)

    Returns IssueCategory.UNCATEGORISED.value if nothing matches.
    """
    if not raw_response or not raw_response.strip():
        logger.warning("Empty LLM response for category classification")
        return IssueCategory.UNCATEGORISED.value

    cleaned = raw_response.strip()

    # Strip markdown bold/italic
    cleaned = re.sub(r"[*_]{1,3}", "", cleaned)

    # Take only the first line (models sometimes add explanations after)
    first_line = cleaned.split("\n")[0].strip()

    # 1. Exact match (case-insensitive)
    if first_line.lower() in _CATEGORY_LOWER_MAP:
        return _CATEGORY_LOWER_MAP[first_line.lower()]

    # 2. Strip common LLM prefixes
    stripped = first_line
    for prefix in ("category:", "answer:", "classification:", "result:", "output:"):
        if stripped.lower().startswith(prefix):
            stripped = stripped[len(prefix):].strip()
            break
    # Strip leading numbering: "1. ", "1) ", "- "
    stripped = re.sub(r"^(?:\d+[.)]\s*|-\s*)", "", stripped).strip()
    # Strip surrounding quotes
    stripped = stripped.strip("\"'`")

    if stripped.lower() in _CATEGORY_LOWER_MAP:
        return _CATEGORY_LOWER_MAP[stripped.lower()]

    # 3. Contains match -- check if any valid category appears in the response
    response_lower = cleaned.lower()
    # Try longest categories first to avoid partial matches
    for cat in sorted(_VALID_CATEGORIES, key=len, reverse=True):
        if cat.lower() in response_lower:
            logger.info(
                "Parsed category via contains-match: %r -> %r", raw_response[:80], cat
            )
            return cat

    # 4. JSON extraction
    json_data = parse_json_response(cleaned)
    if json_data:
        for key in ("category", "Category", "CATEGORY", "classification", "class"):
            if key in json_data:
                cat_val = str(json_data[key]).strip()
                if cat_val.lower() in _CATEGORY_LOWER_MAP:
                    return _CATEGORY_LOWER_MAP[cat_val.lower()]
                # Try contains match on the extracted value
                for cat in sorted(_VALID_CATEGORIES, key=len, reverse=True):
                    if cat.lower() in cat_val.lower():
                        return cat

    # 5. Numbered list extraction -- "1. Waste and Fly-Tipping" on any line
    for line in cleaned.split("\n"):
        match = re.match(r"^\s*\d+[.)]\s*(.+)$", line.strip())
        if match:
            candidate = match.group(1).strip().strip("\"'`")
            if candidate.lower() in _CATEGORY_LOWER_MAP:
                return _CATEGORY_LOWER_MAP[candidate.lower()]

    # 6. Word-overlap fuzzy match
    raw_words = set(stripped.lower().split())
    best, best_score = "", 0.0
    for cat in _VALID_CATEGORIES:
        cat_words = set(cat.lower().split())
        if not raw_words or not cat_words:
            continue
        overlap = len(raw_words & cat_words)
        score = overlap / max(len(raw_words), len(cat_words))
        if score > best_score:
            best, best_score = cat, score

    if best_score >= 0.4:
        logger.info(
            "Parsed category via fuzzy match: %r -> %r (score=%.2f)",
            raw_response[:80], best, best_score,
        )
        return best

    logger.warning(
        "Could not parse category from LLM response: %r -- falling back to Uncategorised",
        raw_response[:120],
    )
    return IssueCategory.UNCATEGORISED.value


def parse_json_response(raw: str) -> dict | None:
    """Extract a JSON object from an LLM response.

    Handles:
      - Clean JSON
      - Markdown code blocks (```json ... ``` or ``` ... ```)
      - Preamble/postamble text around a JSON object
      - Nested braces

    Returns None if no valid JSON object can be extracted.
    """
    if not raw or not raw.strip():
        return None

    cleaned = raw.strip()

    # 1. Try direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Extract from markdown code blocks
    code_block_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL
    )
    if code_block_match:
        try:
            result = json.loads(code_block_match.group(1).strip())
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. Find the first { ... } block (handling nested braces)
    brace_start = cleaned.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[brace_start : i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, dict):
                            return result
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break

    return None


def parse_severity_score(raw: str) -> int:
    """Extract a severity score (1-10) from freeform LLM text.

    Handles:
      - Plain number: "7"
      - Score format: "7/10", "Score: 7"
      - JSON: {"score": 7}
      - Embedded in text: "I would rate this a 7 out of 10"

    Returns the clamped integer (1-10), or 5 as a fallback.
    """
    if not raw or not raw.strip():
        logger.warning("Empty LLM response for severity score -- defaulting to 5")
        return 5

    cleaned = raw.strip()

    # 1. Try plain integer
    try:
        val = int(cleaned)
        return max(1, min(10, val))
    except ValueError:
        pass

    # 2. Try JSON extraction
    json_data = parse_json_response(cleaned)
    if json_data:
        for key in ("score", "severity", "severity_score", "rating"):
            if key in json_data:
                try:
                    val = int(json_data[key])
                    return max(1, min(10, val))
                except (ValueError, TypeError):
                    pass

    # 3. Pattern: "N/10" or "N out of 10"
    match = re.search(r"(\d{1,2})\s*/\s*10", cleaned)
    if match:
        return max(1, min(10, int(match.group(1))))

    match = re.search(r"(\d{1,2})\s+out\s+of\s+10", cleaned, re.IGNORECASE)
    if match:
        return max(1, min(10, int(match.group(1))))

    # 4. Pattern: "Score: N" or "Severity: N"
    match = re.search(
        r"(?:score|severity|rating)\s*[:=]\s*(\d{1,2})", cleaned, re.IGNORECASE
    )
    if match:
        return max(1, min(10, int(match.group(1))))

    # 5. First standalone number in 1-10 range
    for match in re.finditer(r"\b(\d{1,2})\b", cleaned):
        val = int(match.group(1))
        if 1 <= val <= 10:
            return val

    logger.warning(
        "Could not parse severity score from: %r -- defaulting to 5",
        cleaned[:120],
    )
    return 5
