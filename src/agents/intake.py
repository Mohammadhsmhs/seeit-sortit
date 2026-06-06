"""IntakeAgent — parse raw text into a structured CivicIssue."""

from __future__ import annotations

import logging
import re
from datetime import datetime

from src.models.base import CivicIssue, IssueCategory, IssueStatus, LLMProvider
from src.models.mock import MockProvider
from src.models.parser import parse_category
from src.prompts import load_prompt

logger = logging.getLogger(__name__)


# Subcategory keywords per category
_SUBCATEGORY_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "Roads and Highways": {
        "Pothole": ["pothole", "hole in road", "road surface"],
        "Blocked Drain": ["drain", "flooding", "flooded"],
        "Road Markings": ["road marking", "white line", "faded line"],
        "Debris": ["debris", "spillage", "spill"],
        "Damaged Barrier": ["barrier", "railing", "bollard"],
    },
    "Waste and Fly-Tipping": {
        "Fly-Tipping": ["fly-tip", "flytip", "fly tip", "dumped", "dumping", "mattress", "furniture"],
        "Overflowing Bin": ["overflowing", "full bin", "bin full"],
        "Missed Collection": ["missed", "not collected", "collection"],
        "Litter": ["litter", "rubbish", "garbage"],
    },
    "Street Cleanliness": {
        "Graffiti": ["graffiti", "spray paint", "tagged"],
        "Dog Fouling": ["dog foul", "dog poo", "dog mess"],
        "Needles": ["needle", "syringe", "sharps"],
    },
    "Street Lighting and Traffic": {
        "Streetlight Out": ["streetlight", "street light", "lamp", "light out", "not working"],
        "Traffic Signal Fault": ["traffic light", "traffic signal", "signal fault"],
    },
    "Pavements and Footways": {
        "Trip Hazard": ["trip", "uneven", "raised slab"],
        "Cracked Pavement": ["crack", "broken", "damaged"],
    },
}

# London location patterns
_LONDON_LOCATION_PATTERNS = [
    # Postcodes
    r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})\b",
    # Road/Street mentions
    r"(?:on|at|near|outside|opposite)\s+(.{5,40}?(?:road|street|lane|avenue|close|way|drive|crescent|terrace|hill|grove|place|square|gardens|mews|court|walk|rise|row))",
]


def _validate_category(raw: str) -> str:
    """Match an LLM-returned category string to the closest IssueCategory value.

    Delegates to the robust parser in src.models.parser which handles exact
    match, case-insensitive, contains, JSON extraction, numbered lists, and
    fuzzy word-overlap matching.
    """
    return parse_category(raw)


class IntakeAgent:
    """Parses raw user text into a structured CivicIssue."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self._classify_prompt_tpl = load_prompt("intake_classify")
        self._generate_prompt_tpl = load_prompt("intake_generate")

    def process(
        self,
        text: str,
        *,
        photo_description: str | None = None,
        photos: list[str] | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> CivicIssue:
        """Create a CivicIssue from raw user input."""
        combined = text
        if photo_description:
            combined = f"{text}\n[Photo shows: {photo_description}]"

        # Classify category
        categories = [c.value for c in IssueCategory if c != IssueCategory.UNCATEGORISED]
        category = self.llm.classify(combined, categories)

        # Log raw LLM response before parsing (for debugging prompt issues)
        logger.debug("Raw classify response: %r", category)

        # Validate LLM output against known categories (fuzzy match for real LLMs)
        if not isinstance(self.llm, MockProvider):
            category = _validate_category(category)

        # Determine subcategory
        subcategory = self._extract_subcategory(combined, category)

        # Generate title
        title = self._generate_title(combined, category, subcategory)

        # Extract location hints
        address = self._extract_address(text)

        issue = CivicIssue(
            title=title,
            category=category,
            subcategory=subcategory,
            description=text,
            latitude=latitude,
            longitude=longitude,
            address=address,
            photos=photos or [],
            reported_at=datetime.now(),
            status=IssueStatus.TRIAGED.value,
        )
        return issue

    def _extract_subcategory(self, text: str, category: str) -> str:
        """Keyword-match for subcategory within the detected category."""
        lower = text.lower()
        subs = _SUBCATEGORY_KEYWORDS.get(category, {})
        best, best_score = "", 0
        for sub_name, keywords in subs.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > best_score:
                best, best_score = sub_name, score
        return best

    def _generate_title(self, text: str, category: str, subcategory: str) -> str:
        """Produce a short, descriptive title."""
        address = self._extract_address(text)

        if subcategory:
            if address:
                return f"{subcategory} — {address[:50]}"
            return f"{subcategory} reported"

        # In mock mode, build a deterministic title from category + address
        if isinstance(self.llm, MockProvider):
            if address:
                return f"{category} issue — {address[:50]}"
            # Use first ~8 meaningful words from description
            words = [w for w in text.split()[:12] if len(w) > 2]
            snippet = " ".join(words[:8])
            return f"{category}: {snippet}"

        prompt = self._generate_prompt_tpl.format(
            category=category,
            description=text[:200],
        )
        raw = self.llm.generate(prompt)
        logger.debug("Raw title generation response: %r", raw)
        title = raw.strip().strip('"').split("\n")[0][:80]
        return title if title else f"{category} issue reported"

    def _extract_address(self, text: str) -> str:
        """Pull location hints from the text using regex patterns."""
        for pattern in _LONDON_LOCATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.lastindex else match.group(0).strip()
        return ""
