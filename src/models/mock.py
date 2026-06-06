"""Mock LLM provider — keyword matching and templates, no external calls."""

from __future__ import annotations

import hashlib
import math
import random
from typing import Optional

from src.config import EMBED_DIM
from src.models.base import LLMProvider

# ---------------------------------------------------------------------------
# Keyword banks for category classification
# ---------------------------------------------------------------------------
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Roads and Highways": [
        "pothole", "road", "highway", "tarmac", "asphalt", "crack", "road surface",
        "drain", "flooding", "bollard", "barrier", "road marking", "debris",
        "roadworks", "carriageway", "manhole", "speed bump", "kerb",
    ],
    "Waste and Fly-Tipping": [
        "fly-tip", "flytip", "fly tip", "dumped", "rubbish", "waste", "mattress",
        "furniture", "bin bag", "litter", "bin", "refuse", "recycling", "garbage",
        "dumping", "cardboard", "commercial waste", "overflowing bin",
    ],
    "Street Cleanliness": [
        "graffiti", "dog foul", "dog poo", "litter", "dirty", "clean", "fouling",
        "chewing gum", "stain", "glass", "broken glass", "needle", "syringe",
    ],
    "Street Lighting and Traffic": [
        "streetlight", "street light", "lamp", "light not working", "dark",
        "traffic light", "traffic signal", "pedestrian crossing", "beacon",
        "light out", "lamp post",
    ],
    "Pavements and Footways": [
        "pavement", "footpath", "footway", "slab", "paving", "trip hazard",
        "uneven", "raised slab", "cracked pavement", "sidewalk",
    ],
    "Vehicles": [
        "abandoned vehicle", "abandoned car", "untaxed", "parking",
        "car park", "vehicle", "motorbike", "scooter", "parked",
    ],
    "Trees and Vegetation": [
        "tree", "branch", "hedge", "overgrown", "vegetation", "bush",
        "fallen tree", "root", "leaf", "pruning",
    ],
    "Parks and Public Spaces": [
        "park", "playground", "bench", "public space", "recreation",
        "swing", "slide", "fence", "open space", "garden",
    ],
    "Noise and Nuisance": [
        "noise", "loud", "music", "party", "construction noise", "alarm",
        "barking", "nuisance", "antisocial noise",
    ],
    "Pollution": [
        "pollution", "smell", "odour", "chemical", "smoke", "fumes",
        "air quality", "gas leak", "oil", "spill", "contamination",
    ],
    "Antisocial Behaviour": [
        "antisocial", "anti-social", "vandalism", "harassment", "intimidation",
        "rowdy", "threatening",
    ],
    "Housing": [
        "housing", "damp", "mould", "disrepair", "tenant", "landlord",
        "leak", "council house", "estate",
    ],
    "Planning and Building": [
        "planning", "building work", "scaffolding", "construction",
        "planning permission", "building site",
    ],
    "Pest Control": [
        "rat", "mice", "mouse", "cockroach", "pest", "wasp", "pigeon",
        "fox", "bed bug", "infestation",
    ],
    "Food and Business": [
        "food", "restaurant", "hygiene", "takeaway", "cafe", "shop",
        "business", "food safety",
    ],
    "Dead Animals": [
        "dead animal", "dead bird", "dead fox", "dead cat", "carcass",
        "dead pigeon", "roadkill",
    ],
    "Utilities": [
        "water", "gas", "electric", "power", "cable", "manhole",
        "utility", "telecoms", "sewer",
    ],
    "Fraud and Misuse": [
        "fraud", "scam", "misuse", "benefit fraud",
    ],
}


class MockProvider(LLMProvider):
    """Works entirely offline with keyword matching and templates."""

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Return a template-based response by scanning the prompt for intent."""
        lower = prompt.lower()

        if "title" in lower or "summarise" in lower or "summarize" in lower:
            # Extract a short snippet from the prompt as a pseudo-title
            words = prompt.split()
            snippet = " ".join(words[:10]) if len(words) > 10 else prompt
            return f"Civic issue: {snippet}"

        if "severity" in lower or "score" in lower:
            return (
                "Severity: 5/10. This issue poses moderate risk to public safety. "
                "Factors considered: category base score, location context, and "
                "potential for escalation."
            )

        if "submission" in lower or "report" in lower or "formal" in lower:
            return (
                "Dear Council,\n\n"
                "I am writing to report a civic issue in your borough. "
                "Please see the details below and take appropriate action.\n\n"
                "Kind regards,\nLondon Civic Agent (automated report)"
            )

        if "department" in lower or "route" in lower or "council" in lower:
            return "Highways and Transport Department"

        return f"[MockProvider] Processed prompt ({len(prompt)} chars)."

    def classify(self, text: str, categories: list[str]) -> str:
        """Keyword-match *text* against category keyword banks."""
        lower = text.lower()
        scores: dict[str, int] = {}

        for cat, keywords in _CATEGORY_KEYWORDS.items():
            if cat not in categories:
                continue
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[cat] = score

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]

        # Fallback: return first category or "Uncategorised"
        return categories[0] if categories else "Uncategorised"

    def embed(self, text: str) -> list[float]:
        """Deterministic pseudo-random vector seeded from text content."""
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        vec = [rng.gauss(0, 1) for _ in range(EMBED_DIM)]
        # L2-normalise
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec
