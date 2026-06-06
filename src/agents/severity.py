"""SeverityAgent — score civic issues 1-10 using a rule-based matrix."""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path
from typing import Optional

from src.config import DATA_DIR, SCRAPER_DB, SEVERITY_FACTORS_JSON, CATEGORY_MAPPING_JSON, PROJECT_ROOT
from src.models.base import CivicIssue, LLMProvider

logger = logging.getLogger(__name__)

RAG_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index.json"

# ---------------------------------------------------------------------------
# Hardcoded fallback — used only if severity_factors.json is missing
# ---------------------------------------------------------------------------
_CATEGORY_BASE_SCORE_FALLBACK: dict[str, int] = {
    "Roads and Highways": 5,
    "Waste and Fly-Tipping": 4,
    "Street Cleanliness": 2,
    "Street Lighting and Traffic": 2,
    "Pavements and Footways": 4,
    "Vehicles": 3,
    "Trees and Vegetation": 4,
    "Parks and Public Spaces": 3,
    "Noise and Nuisance": 3,
    "Pollution": 6,
    "Antisocial Behaviour": 4,
    "Housing": 5,
    "Planning and Building": 2,
    "Pest Control": 4,
    "Food and Business": 4,
    "Dead Animals": 3,
    "Utilities": 7,
    "Fraud and Misuse": 2,
    "Uncategorised": 3,
}

# Subcategory adjustments (additive)
_SUBCATEGORY_ADJUST: dict[str, int] = {
    "Pothole": 0,
    "Blocked Drain": 1,        # flooding risk
    "Debris": 1,               # immediate hazard
    "Fly-Tipping": 0,
    "Needles": 2,              # health hazard
    "Graffiti": -1,
    "Streetlight Out": 0,
    "Traffic Signal Fault": 1,
    "Trip Hazard": 1,
}

# Hazard keywords that bump severity
_HAZARD_KEYWORDS: dict[str, int] = {
    "gas leak": 4,
    "asbestos": 4,
    "chemical": 3,
    "electrical": 3,
    "sinkhole": 3,
    "collapse": 3,
    "flood": 2,
    "fire": 3,
    "needle": 2,
    "syringe": 2,
    "dangerous": 2,
    "urgent": 1,
    "emergency": 2,
    "child": 1,
    "elderly": 1,
    "wheelchair": 1,
    "blind": 1,
    "school": 1,
    "hospital": 1,
    "busy road": 1,
    "main road": 1,
    "a-road": 1,
}

# Sample sensitive locations in London (schools, hospitals) for proximity check
_SENSITIVE_LOCATIONS: list[dict] = [
    {"name": "Great Ormond Street Hospital", "lat": 51.5224, "lon": -0.1200, "type": "hospital"},
    {"name": "St Thomas' Hospital", "lat": 51.4987, "lon": -0.1175, "type": "hospital"},
    {"name": "Royal London Hospital", "lat": 51.5186, "lon": -0.0590, "type": "hospital"},
    {"name": "King's College Hospital", "lat": 51.4684, "lon": -0.0943, "type": "hospital"},
    {"name": "City of London Academy", "lat": 51.4940, "lon": -0.0635, "type": "school"},
    {"name": "Westminster Academy", "lat": 51.5225, "lon": -0.1757, "type": "school"},
    {"name": "Hackney Free School", "lat": 51.5470, "lon": -0.0555, "type": "school"},
    {"name": "Bow Primary School", "lat": 51.5285, "lon": -0.0200, "type": "school"},
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class SeverityAgent:
    """Scores a CivicIssue on a 1-10 scale with justification."""

    # Regex to find A-road references like "A205", "A1", "A406" in text
    _ROAD_ID_RE = re.compile(r"\b(A\d{1,4})\b", re.IGNORECASE)

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self._severity_factors = self._load_severity_factors()
        self._base_scores = self._build_base_scores()
        self._proximity_modifiers = self._build_proximity_modifiers()
        self._repeat_modifiers = self._build_repeat_modifiers()
        self._category_mapping = self._load_category_mapping()
        self._reverse_mapping = self._build_reverse_mapping()
        self._proximity_index = self._load_proximity_index()
        self._rag_corpus = self._load_rag_corpus()
        self._tfl_client = self._init_tfl_client()

    # -- Loading helpers ----------------------------------------------------

    def _load_severity_factors(self) -> dict | None:
        """Load severity_factors.json if available."""
        if SEVERITY_FACTORS_JSON.exists():
            try:
                with open(SEVERITY_FACTORS_JSON) as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    def _build_base_scores(self) -> dict[str, int]:
        """Build base severity lookup from JSON file, falling back to hardcoded."""
        if self._severity_factors and "base_severity" in self._severity_factors:
            return {k: int(v) for k, v in self._severity_factors["base_severity"].items()}
        return _CATEGORY_BASE_SCORE_FALLBACK

    def _build_proximity_modifiers(self) -> dict:
        """Extract proximity modifiers from severity_factors.json."""
        if self._severity_factors and "proximity_modifiers" in self._severity_factors:
            return self._severity_factors["proximity_modifiers"]
        return {}

    def _build_repeat_modifiers(self) -> dict:
        """Extract repeat report modifiers from severity_factors.json."""
        if self._severity_factors and "repeat_report_modifier" in self._severity_factors:
            return self._severity_factors["repeat_report_modifier"]
        return {}

    def _load_category_mapping(self) -> dict[str, str]:
        """Load raw-category -> parent-category mapping."""
        if CATEGORY_MAPPING_JSON.exists():
            try:
                with open(CATEGORY_MAPPING_JSON) as f:
                    data = json.load(f)
                return data.get("mapping", {})
            except (json.JSONDecodeError, KeyError):
                pass
        return {}

    def _build_reverse_mapping(self) -> dict[str, list[str]]:
        """Build parent-category -> [raw categories] reverse lookup."""
        reverse: dict[str, list[str]] = {}
        for raw_cat, parent_cat in self._category_mapping.items():
            reverse.setdefault(parent_cat, []).append(raw_cat)
        return reverse

    def _load_proximity_index(self):
        """Load the real geospatial ProximityIndex; return None on failure."""
        try:
            from src.data.proximity_index import ProximityIndex
            idx = ProximityIndex()
            if idx.school_count > 0 or idx.hospital_count > 0:
                logger.info(
                    "ProximityIndex ready: %d schools, %d hospitals, "
                    "%d care homes, %d collisions, %d LSOAs",
                    idx.school_count, idx.hospital_count, idx.care_home_count,
                    idx.collision_count, idx.lsoa_count,
                )
                return idx
            logger.warning("ProximityIndex loaded but empty — falling back to hardcoded locations")
        except Exception:
            logger.warning(
                "Could not load ProximityIndex (data files missing?) "
                "— falling back to hardcoded locations",
                exc_info=True,
            )
        return None

    def _load_rag_corpus(self):
        """Load the pre-built RAG corpus index for context enrichment."""
        try:
            from src.rag.corpus import CorpusManager
            corpus = CorpusManager()
            count = corpus.load(RAG_INDEX_PATH)
            if count > 0:
                logger.info("RAG corpus loaded: %d chunks", count)
                return corpus
            logger.info("RAG index file empty or not found -- RAG context disabled")
        except Exception:
            logger.warning(
                "Could not load RAG corpus -- RAG context enrichment disabled",
                exc_info=True,
            )
        return None

    def _init_tfl_client(self):
        """Initialise the TfL API client.

        Returns None when running in mock mode (offline tests) or on
        import failure.
        """
        from src.models.mock import MockProvider
        if isinstance(self.llm, MockProvider):
            logger.debug("Mock mode — TfL live API disabled")
            return None
        try:
            from src.integrations.tfl import TfLClient
            client = TfLClient()
            logger.info("TfL live API client initialised")
            return client
        except Exception:
            logger.warning("Could not initialise TfL client — live road data disabled", exc_info=True)
            return None

    def _extract_road_ids(self, text: str) -> list[str]:
        """Extract A-road identifiers (e.g. 'A205', 'A1') from text."""
        matches = self._ROAD_ID_RE.findall(text)
        # Deduplicate, preserve order, normalise to uppercase
        seen: set[str] = set()
        result: list[str] = []
        for m in matches:
            upper = m.upper()
            if upper not in seen:
                seen.add(upper)
                result.append(upper)
        return result

    def _tfl_disruption_notes(self, issue: CivicIssue) -> list[str]:
        """Check TfL API for live disruptions on roads mentioned in the issue.

        Returns human-readable notes for the severity justification.
        Does NOT affect the numeric score — this is informational context
        showing live London data in the demo.
        """
        if self._tfl_client is None:
            return []

        road_ids = self._extract_road_ids(issue.description)
        if not road_ids:
            return []

        notes: list[str] = []
        for road_id in road_ids[:3]:  # Cap at 3 roads to avoid slow API calls
            try:
                summary = self._tfl_client.get_road_status_summary(road_id)
                if summary:
                    notes.append(f"TfL live data: {summary}")
                else:
                    # Still useful to show we checked and road is clear
                    status = self._tfl_client.get_road_status(road_id)
                    if status:
                        name = status.get("displayName", road_id)
                        notes.append(f"TfL live data: {name} — No current disruptions")
            except Exception:
                logger.debug("TfL API call failed for road %s", road_id, exc_info=True)
        return notes

    # -- Main scoring -------------------------------------------------------

    def process(self, issue: CivicIssue) -> CivicIssue:
        """Mutate *issue* in-place with severity_score and severity_justification."""
        score, reasons = self._rule_score(issue)
        issue.severity_score = max(1, min(10, score))

        # Enrich justification with RAG context (nearby real data)
        if self._rag_corpus and issue.latitude and issue.longitude:
            rag_notes = self._rag_context_notes(issue.latitude, issue.longitude)
            if rag_notes:
                reasons.append("RAG context: " + "; ".join(rag_notes))

        # Enrich justification with live TfL road disruption data
        tfl_notes = self._tfl_disruption_notes(issue)
        if tfl_notes:
            reasons.extend(tfl_notes)

        issue.severity_justification = "; ".join(reasons)
        return issue

    # -- RAG context enrichment ---------------------------------------------

    def _rag_context_notes(self, lat: float, lon: float) -> list[str]:
        """Generate human-readable notes from nearby RAG chunks.

        This does NOT affect the numeric score (that's handled by the
        ProximityIndex). It adds descriptive context to the justification
        string for richer explanations in the demo.
        """
        notes: list[str] = []
        corpus = self._rag_corpus

        # Collisions within 500m
        collisions = corpus.search_nearby(lat, lon, radius_km=0.5, dataset_name="collisions")
        if len(collisions) >= 3:
            serious = sum(
                1 for c in collisions
                if c.get("metadata", {}).get("severity") in (1, 2)
            )
            fatal = sum(
                1 for c in collisions
                if c.get("metadata", {}).get("severity") == 1
            )
            parts = [f"{len(collisions)} road collisions recorded within 500m"]
            if fatal:
                parts.append(f"including {fatal} fatal")
            if serious:
                parts.append(f"{serious} serious injury" if serious == 1 else f"{serious} serious injuries")
            notes.append(", ".join(parts))

        # Schools within 200m
        schools = corpus.search_nearby(lat, lon, radius_km=0.2, dataset_name="schools")
        for s in schools[:2]:
            name = s.get("metadata", {}).get("name", "a school")
            dist_m = int(s.get("_distance_km", 0) * 1000)
            notes.append(f"{name} is {dist_m}m from this location")

        # Hospitals within 500m
        hospitals = corpus.search_nearby(lat, lon, radius_km=0.5, dataset_name="hospitals")
        for h in hospitals[:1]:
            name = h.get("metadata", {}).get("name", "a hospital")
            dist_m = int(h.get("_distance_km", 0) * 1000)
            notes.append(f"{name} is {dist_m}m away")

        # Care homes within 200m
        care_homes = corpus.search_nearby(lat, lon, radius_km=0.2, dataset_name="care_homes")
        if care_homes:
            count = len(care_homes)
            first_name = care_homes[0].get("metadata", {}).get("name", "a care home")
            if count == 1:
                dist_m = int(care_homes[0].get("_distance_km", 0) * 1000)
                notes.append(f"{first_name} (care home) is {dist_m}m away")
            else:
                notes.append(f"{count} care homes within 200m including {first_name}")

        return notes

    # Maximum bonus from proximity modifiers (schools, hospitals, etc.)
    _MAX_PROXIMITY_BOOST = 2
    # Maximum bonus from hazard keyword matches
    _MAX_KEYWORD_BOOST = 1

    def _rule_score(self, issue: CivicIssue) -> tuple[int, list[str]]:
        reasons: list[str] = []

        # 1. Category base — try detailed subcategory first, then parent
        base = self._get_base_score(issue, reasons)

        # 2. Subcategory adjustment
        sub_adj = _SUBCATEGORY_ADJUST.get(issue.subcategory, 0)
        if sub_adj:
            base += sub_adj
            reasons.append(f"Subcategory adjust ({issue.subcategory}): {sub_adj:+d}")

        # 3. Hazard keyword scan (capped at _MAX_KEYWORD_BOOST)
        lower_desc = issue.description.lower()
        keyword_reasons: list[str] = []
        hazard_raw = 0
        for keyword, boost in _HAZARD_KEYWORDS.items():
            if keyword in lower_desc:
                hazard_raw += boost
                keyword_reasons.append(f"Hazard keyword '{keyword}': +{boost}")
        hazard_total = min(hazard_raw, self._MAX_KEYWORD_BOOST)
        if keyword_reasons:
            reasons.extend(keyword_reasons)
            if hazard_raw > hazard_total:
                reasons.append(
                    f"Keyword boost capped: {hazard_raw} -> {hazard_total}"
                )
        base += hazard_total

        # 4. Proximity to sensitive locations (capped at _MAX_PROXIMITY_BOOST)
        if issue.latitude and issue.longitude:
            proximity_reasons: list[str] = []
            proximity_raw = self._proximity_boost(
                issue.latitude, issue.longitude, proximity_reasons
            )
            proximity_capped = min(proximity_raw, self._MAX_PROXIMITY_BOOST)
            reasons.extend(proximity_reasons)
            if proximity_raw > proximity_capped:
                reasons.append(
                    f"Proximity boost capped: {proximity_raw} -> {proximity_capped}"
                )
            base += proximity_capped

        # 5. Repeat-area check (via scraper DB if available)
        repeat_boost = self._repeat_area_boost(issue, reasons)
        base += repeat_boost

        return base, reasons

    def _get_base_score(self, issue: CivicIssue, reasons: list[str]) -> int:
        """Look up base severity: try the detailed 56-category JSON first, then parent."""
        # Try exact subcategory match against severity_factors base_severity
        if issue.subcategory and issue.subcategory in self._base_scores:
            score = self._base_scores[issue.subcategory]
            reasons.append(f"Base severity ({issue.subcategory}): {score}")
            return score

        # Try parent category match against severity_factors
        if issue.category in self._base_scores:
            score = self._base_scores[issue.category]
            reasons.append(f"Base severity ({issue.category}): {score}")
            return score

        # Fall back to hardcoded parent category scores
        score = _CATEGORY_BASE_SCORE_FALLBACK.get(issue.category, 3)
        reasons.append(f"Category base ({issue.category}): {score}")
        return score

    def _proximity_boost(
        self, lat: float, lon: float, reasons: list[str]
    ) -> int:
        """Check proximity to schools, hospitals, care homes, collision
        hotspots, and population density using real geospatial data.

        Falls back to the hardcoded _SENSITIVE_LOCATIONS list when the
        ProximityIndex is not available.
        """
        if self._proximity_index is not None:
            return self._proximity_boost_real(lat, lon, reasons)
        return self._proximity_boost_fallback(lat, lon, reasons)

    def _proximity_boost_real(
        self, lat: float, lon: float, reasons: list[str]
    ) -> int:
        """Score proximity using real data from ProximityIndex."""
        idx = self._proximity_index
        boost = 0

        # Schools within 200m -> +2
        nearby_schools = idx.schools_within(lat, lon, 0.2)
        if nearby_schools:
            boost += 2
            names = ", ".join(s.name for s in nearby_schools[:3])
            suffix = f" (+{len(nearby_schools) - 3} more)" if len(nearby_schools) > 3 else ""
            reasons.append(
                f"School within 200m ({len(nearby_schools)} nearby: {names}{suffix}): +2"
            )

        # Hospitals within 300m -> +2
        nearby_hospitals = idx.hospitals_within(lat, lon, 0.3)
        if nearby_hospitals:
            boost += 2
            names = ", ".join(h.name for h in nearby_hospitals[:3])
            suffix = f" (+{len(nearby_hospitals) - 3} more)" if len(nearby_hospitals) > 3 else ""
            reasons.append(
                f"Hospital within 300m ({len(nearby_hospitals)} nearby: {names}{suffix}): +2"
            )

        # Care homes within 200m -> +1
        nearby_care = idx.care_homes_within(lat, lon, 0.2)
        if nearby_care:
            boost += 1
            names = ", ".join(c.name for c in nearby_care[:3])
            suffix = f" (+{len(nearby_care) - 3} more)" if len(nearby_care) > 3 else ""
            reasons.append(
                f"Care home within 200m ({len(nearby_care)} nearby: {names}{suffix}): +1"
            )

        # 3+ collisions within 500m -> +1
        nearby_collisions = idx.collisions_within(lat, lon, 0.5, years_back=3)
        if len(nearby_collisions) >= 3:
            boost += 1
            fatal = sum(1 for c in nearby_collisions if c.severity == 1)
            serious = sum(1 for c in nearby_collisions if c.severity == 2)
            reasons.append(
                f"Collision hotspot ({len(nearby_collisions)} collisions within 500m, "
                f"{fatal} fatal, {serious} serious): +1"
            )

        # High population density -> +1 (above 15,000 people per sq km)
        density = idx.population_density_at(lat, lon)
        if density > 15000:
            boost += 1
            reasons.append(
                f"High population density ({density:,.0f} people/sq km): +1"
            )

        # Traffic flow (DfT AADF) within 400m
        #  busy road  (>10,000 vehicles/day) -> +1
        #  very busy  (>20,000 vehicles/day) -> +1 more (so total +2)
        # We use 400m here rather than the method's 200m default because DfT
        # count points are typically spaced every 300-500m on London A-roads,
        # so a 200m radius misses ~half of them. The total proximity bonus is
        # still capped at _MAX_PROXIMITY_BOOST in the caller.
        traffic = idx.traffic_flow_at(lat, lon, radius_m=400)
        if traffic is not None and traffic.aadf > 10000:
            boost += 1
            label = "very busy road" if traffic.aadf > 20000 else "busy road"
            reasons.append(
                f"On a {label} carrying ~{traffic.aadf:,} vehicles/day "
                f"({traffic.road_name}, DfT AADF): +1"
            )
            if traffic.aadf > 20000:
                boost += 1
                reasons.append(
                    f"Very busy road (>20,000 AADF on {traffic.road_name}): +1"
                )

        return boost

    def _proximity_boost_fallback(
        self, lat: float, lon: float, reasons: list[str]
    ) -> int:
        """Fallback scoring using hardcoded _SENSITIVE_LOCATIONS."""
        school_mod = self._proximity_modifiers.get("school_within_100m", {})
        hospital_mod = self._proximity_modifiers.get("hospital_within_200m", {})

        school_boost_val = school_mod.get("modifier", 2)
        hospital_boost_val = hospital_mod.get("modifier", 2)

        boost = 0
        for loc in _SENSITIVE_LOCATIONS:
            dist = _haversine_km(lat, lon, loc["lat"], loc["lon"])
            if loc["type"] == "hospital":
                if dist < 0.2:
                    boost += hospital_boost_val
                    reasons.append(
                        f"Within 200m of {loc['name']} ({loc['type']}): +{hospital_boost_val}"
                    )
                    break
                elif dist < 0.8:
                    boost += 1
                    reasons.append(
                        f"Within 800m of {loc['name']} ({loc['type']}): +1"
                    )
                    break
            elif loc["type"] == "school":
                if dist < 0.1:
                    boost += school_boost_val
                    reasons.append(
                        f"Within 100m of {loc['name']} ({loc['type']}): +{school_boost_val}"
                    )
                    break
                elif dist < 0.5:
                    boost += 1
                    reasons.append(
                        f"Within 500m of {loc['name']} ({loc['type']}): +1"
                    )
                    break
        return boost

    def _repeat_area_boost(
        self, issue: CivicIssue, reasons: list[str]
    ) -> int:
        """Check for repeated reports in same area using scraper DB.

        Uses category_mapping.json to query ALL raw FixMyStreet category
        variants that map to the same parent category, and applies the
        repeat_report_modifier thresholds from severity_factors.json.
        """
        if not issue.latitude or not issue.longitude:
            return 0
        if not SCRAPER_DB.exists():
            return 0

        try:
            import sqlite3

            db = sqlite3.connect(str(SCRAPER_DB))

            # Collect all raw DB category names that map to the same parent
            raw_variants = self._reverse_mapping.get(issue.category, [])
            # Also include the parent category itself (in case the DB uses it)
            all_cats = list(set(raw_variants + [issue.category]))

            # Rough bounding box: ~200m in each direction
            delta = 0.002  # ~200m in London latitude
            placeholders = ",".join("?" for _ in all_cats)
            rows = db.execute(
                f"""SELECT COUNT(*) FROM reports
                   WHERE latitude BETWEEN ? AND ?
                   AND longitude BETWEEN ? AND ?
                   AND category IN ({placeholders})""",
                (
                    issue.latitude - delta,
                    issue.latitude + delta,
                    issue.longitude - delta,
                    issue.longitude + delta,
                    *all_cats,
                ),
            ).fetchone()
            db.close()

            count = rows[0] if rows else 0

            # Apply repeat_report_modifier thresholds from severity_factors.json
            mod_5 = self._repeat_modifiers.get("5_reports_same_area_30_days", {})
            mod_3 = self._repeat_modifiers.get("3_reports_same_area_30_days", {})
            mod_2 = self._repeat_modifiers.get("2_reports_same_location_30_days", {})

            if count >= 5:
                boost = mod_5.get("modifier", 2)
                reasons.append(f"Repeat hotspot ({count} prior reports nearby): +{boost}")
                return boost
            elif count >= 3:
                boost = mod_3.get("modifier", 1)
                reasons.append(f"Cluster of reports nearby ({count}): +{boost}")
                return boost
            elif count >= 2:
                boost = mod_2.get("modifier", 1)
                reasons.append(f"Some prior reports nearby ({count}): +{boost}")
                return boost
        except Exception:
            pass  # DB unavailable — no boost
        return 0
