"""RoutingAgent — determine which council and department handles the issue."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Optional

from src.config import BOROUGHS_JSON
from src.models.base import CivicIssue, LLMProvider

# ---------------------------------------------------------------------------
# Category -> department mapping
# ---------------------------------------------------------------------------
_CATEGORY_DEPARTMENT: dict[str, str] = {
    "Roads and Highways": "Highways and Transport",
    "Waste and Fly-Tipping": "Waste and Environmental Services",
    "Street Cleanliness": "Waste and Environmental Services",
    "Street Lighting and Traffic": "Highways and Transport",
    "Pavements and Footways": "Highways and Transport",
    "Vehicles": "Parking and Transport",
    "Trees and Vegetation": "Parks and Green Spaces",
    "Parks and Public Spaces": "Parks and Green Spaces",
    "Noise and Nuisance": "Environmental Health",
    "Pollution": "Environmental Health",
    "Antisocial Behaviour": "Community Safety",
    "Housing": "Housing Services",
    "Planning and Building": "Planning and Development",
    "Pest Control": "Environmental Health",
    "Food and Business": "Environmental Health",
    "Dead Animals": "Waste and Environmental Services",
    "Utilities": "Highways and Transport",
    "Fraud and Misuse": "Community Safety",
    "Uncategorised": "General Enquiries",
}

# ---------------------------------------------------------------------------
# London boroughs with approximate centre coordinates
# (used when boroughs.json is not available)
# ---------------------------------------------------------------------------
_BOROUGHS_FALLBACK: list[dict] = [
    {"name": "City of London", "council": "City of London Corporation", "lat": 51.5155, "lon": -0.0922},
    {"name": "Westminster", "council": "Westminster City Council", "lat": 51.4975, "lon": -0.1357},
    {"name": "Camden", "council": "London Borough of Camden", "lat": 51.5517, "lon": -0.1588},
    {"name": "Islington", "council": "London Borough of Islington", "lat": 51.5465, "lon": -0.1058},
    {"name": "Hackney", "council": "London Borough of Hackney", "lat": 51.5450, "lon": -0.0553},
    {"name": "Tower Hamlets", "council": "London Borough of Tower Hamlets", "lat": 51.5099, "lon": -0.0271},
    {"name": "Southwark", "council": "London Borough of Southwark", "lat": 51.4733, "lon": -0.0759},
    {"name": "Lambeth", "council": "London Borough of Lambeth", "lat": 51.4571, "lon": -0.1231},
    {"name": "Wandsworth", "council": "London Borough of Wandsworth", "lat": 51.4567, "lon": -0.1910},
    {"name": "Hammersmith and Fulham", "council": "London Borough of Hammersmith and Fulham", "lat": 51.4927, "lon": -0.2339},
    {"name": "Kensington and Chelsea", "council": "Royal Borough of Kensington and Chelsea", "lat": 51.5020, "lon": -0.1947},
    {"name": "Lewisham", "council": "London Borough of Lewisham", "lat": 51.4415, "lon": -0.0117},
    {"name": "Greenwich", "council": "Royal Borough of Greenwich", "lat": 51.4892, "lon": 0.0648},
    {"name": "Bexley", "council": "London Borough of Bexley", "lat": 51.4549, "lon": 0.1505},
    {"name": "Bromley", "council": "London Borough of Bromley", "lat": 51.4039, "lon": 0.0198},
    {"name": "Croydon", "council": "London Borough of Croydon", "lat": 51.3762, "lon": -0.0982},
    {"name": "Merton", "council": "London Borough of Merton", "lat": 51.4014, "lon": -0.1958},
    {"name": "Sutton", "council": "London Borough of Sutton", "lat": 51.3618, "lon": -0.1945},
    {"name": "Kingston upon Thames", "council": "Royal Borough of Kingston upon Thames", "lat": 51.4085, "lon": -0.3064},
    {"name": "Richmond upon Thames", "council": "London Borough of Richmond upon Thames", "lat": 51.4613, "lon": -0.3037},
    {"name": "Hounslow", "council": "London Borough of Hounslow", "lat": 51.4746, "lon": -0.3680},
    {"name": "Ealing", "council": "London Borough of Ealing", "lat": 51.5130, "lon": -0.3089},
    {"name": "Hillingdon", "council": "London Borough of Hillingdon", "lat": 51.5441, "lon": -0.4760},
    {"name": "Harrow", "council": "London Borough of Harrow", "lat": 51.5898, "lon": -0.3346},
    {"name": "Brent", "council": "London Borough of Brent", "lat": 51.5588, "lon": -0.2817},
    {"name": "Barnet", "council": "London Borough of Barnet", "lat": 51.6252, "lon": -0.1517},
    {"name": "Haringey", "council": "London Borough of Haringey", "lat": 51.5906, "lon": -0.1110},
    {"name": "Enfield", "council": "London Borough of Enfield", "lat": 51.6538, "lon": -0.0799},
    {"name": "Waltham Forest", "council": "London Borough of Waltham Forest", "lat": 51.5886, "lon": -0.0118},
    {"name": "Redbridge", "council": "London Borough of Redbridge", "lat": 51.5590, "lon": 0.0741},
    {"name": "Havering", "council": "London Borough of Havering", "lat": 51.5812, "lon": 0.2183},
    {"name": "Barking and Dagenham", "council": "London Borough of Barking and Dagenham", "lat": 51.5607, "lon": 0.1557},
    {"name": "Newham", "council": "London Borough of Newham", "lat": 51.5077, "lon": 0.0469},
]

# TfL-managed roads (red routes) — major A-roads
_TFL_ROAD_KEYWORDS = [
    "a1", "a2", "a3", "a4", "a5", "a10", "a11", "a12", "a13",
    "a20", "a23", "a24", "a40", "a41", "a102", "a200", "a202",
    "a205", "a206", "a316", "a406", "north circular", "south circular",
    "red route", "tfl road",
]

# ---------------------------------------------------------------------------
# Postcode district -> primary borough mapping
# Maps ~120 London postcode districts to their primary borough.
# Used as first-pass lookup before falling back to centroid distance.
# ---------------------------------------------------------------------------
_POSTCODE_TO_BOROUGH: dict[str, str] = {
    # E — East London
    "E1": "Tower Hamlets", "E1W": "Tower Hamlets", "E2": "Tower Hamlets",
    "E3": "Tower Hamlets", "E14": "Tower Hamlets",
    "E4": "Waltham Forest", "E5": "Hackney", "E6": "Newham",
    "E7": "Newham", "E8": "Hackney", "E9": "Hackney",
    "E10": "Waltham Forest", "E11": "Waltham Forest", "E12": "Newham",
    "E13": "Newham", "E15": "Newham", "E16": "Newham",
    "E17": "Waltham Forest", "E18": "Redbridge", "E20": "Newham",
    # EC — City
    "EC1": "Islington", "EC2": "City of London", "EC3": "City of London",
    "EC4": "City of London",
    # N — North London
    "N1": "Islington", "N1C": "Camden", "N2": "Barnet",
    "N3": "Barnet", "N4": "Haringey", "N5": "Islington",
    "N6": "Camden", "N7": "Islington", "N8": "Haringey",
    "N9": "Enfield", "N10": "Haringey", "N11": "Barnet",
    "N12": "Barnet", "N13": "Enfield", "N14": "Enfield",
    "N15": "Haringey", "N16": "Hackney", "N17": "Haringey",
    "N18": "Enfield", "N19": "Islington", "N20": "Barnet",
    "N21": "Enfield", "N22": "Haringey",
    # NW — North West London
    "NW1": "Camden", "NW2": "Brent", "NW3": "Camden",
    "NW4": "Barnet", "NW5": "Camden", "NW6": "Camden",
    "NW7": "Barnet", "NW8": "Westminster", "NW9": "Brent",
    "NW10": "Brent", "NW11": "Barnet",
    # SE — South East London
    "SE1": "Lambeth", "SE2": "Greenwich", "SE3": "Greenwich",
    "SE4": "Lewisham", "SE5": "Southwark", "SE6": "Lewisham",
    "SE7": "Greenwich", "SE8": "Lewisham", "SE9": "Greenwich",
    "SE10": "Greenwich", "SE11": "Lambeth", "SE12": "Lewisham",
    "SE13": "Lewisham", "SE14": "Lewisham", "SE15": "Southwark",
    "SE16": "Southwark", "SE17": "Southwark", "SE18": "Greenwich",
    "SE19": "Croydon", "SE20": "Bromley", "SE21": "Southwark",
    "SE22": "Southwark", "SE23": "Lewisham", "SE24": "Lambeth",
    "SE25": "Croydon", "SE26": "Lewisham", "SE27": "Lambeth",
    "SE28": "Greenwich",
    # SW — South West London
    "SW1": "Westminster", "SW1A": "Westminster", "SW1E": "Westminster",
    "SW1H": "Westminster", "SW1P": "Westminster", "SW1V": "Westminster",
    "SW1W": "Westminster", "SW1X": "Westminster", "SW1Y": "Westminster",
    "SW2": "Lambeth", "SW3": "Kensington and Chelsea",
    "SW4": "Lambeth", "SW5": "Kensington and Chelsea",
    "SW6": "Hammersmith and Fulham", "SW7": "Kensington and Chelsea",
    "SW8": "Lambeth", "SW9": "Lambeth", "SW10": "Kensington and Chelsea",
    "SW11": "Wandsworth", "SW12": "Wandsworth", "SW13": "Richmond upon Thames",
    "SW14": "Richmond upon Thames", "SW15": "Wandsworth",
    "SW16": "Lambeth", "SW17": "Wandsworth", "SW18": "Wandsworth",
    "SW19": "Merton", "SW20": "Merton",
    # W — West London
    "W1": "Westminster", "W2": "Westminster", "W3": "Ealing",
    "W4": "Hounslow", "W5": "Ealing", "W6": "Hammersmith and Fulham",
    "W7": "Ealing", "W8": "Kensington and Chelsea",
    "W9": "Westminster", "W10": "Kensington and Chelsea",
    "W11": "Kensington and Chelsea", "W12": "Hammersmith and Fulham",
    "W13": "Ealing", "W14": "Hammersmith and Fulham",
    # WC — West Central
    "WC1": "Camden", "WC2": "Westminster",
    # Outer London postcodes
    "BR1": "Bromley", "BR2": "Bromley", "BR3": "Bromley",
    "BR4": "Bromley", "BR5": "Bromley", "BR6": "Bromley", "BR7": "Bromley",
    "CR0": "Croydon", "CR2": "Croydon", "CR4": "Merton",
    "CR5": "Croydon", "CR7": "Croydon", "CR8": "Croydon",
    "DA1": "Bexley", "DA5": "Bexley", "DA6": "Bexley",
    "DA7": "Bexley", "DA8": "Bexley", "DA14": "Bexley",
    "DA15": "Bexley", "DA16": "Bexley", "DA17": "Bexley", "DA18": "Bexley",
    "EN1": "Enfield", "EN2": "Enfield", "EN3": "Enfield",
    "EN4": "Barnet", "EN5": "Barnet",
    "HA0": "Brent", "HA1": "Harrow", "HA2": "Harrow",
    "HA3": "Harrow", "HA4": "Hillingdon", "HA5": "Harrow",
    "HA6": "Hillingdon", "HA7": "Harrow", "HA8": "Barnet",
    "HA9": "Brent",
    "IG1": "Redbridge", "IG2": "Redbridge", "IG3": "Redbridge",
    "IG4": "Redbridge", "IG5": "Redbridge", "IG6": "Redbridge",
    "IG7": "Redbridge", "IG8": "Redbridge",
    "IG11": "Barking and Dagenham",
    "KT1": "Kingston upon Thames", "KT2": "Kingston upon Thames",
    "KT3": "Kingston upon Thames", "KT5": "Kingston upon Thames",
    "KT6": "Kingston upon Thames", "KT9": "Kingston upon Thames",
    "RM1": "Havering", "RM2": "Havering", "RM3": "Havering",
    "RM5": "Havering", "RM6": "Barking and Dagenham",
    "RM7": "Havering", "RM8": "Barking and Dagenham",
    "RM9": "Barking and Dagenham", "RM10": "Barking and Dagenham",
    "RM11": "Havering", "RM12": "Havering", "RM13": "Havering",
    "RM14": "Havering",
    "SM1": "Sutton", "SM2": "Sutton", "SM3": "Sutton",
    "SM4": "Merton", "SM5": "Sutton", "SM6": "Sutton",
    "TW1": "Richmond upon Thames", "TW2": "Richmond upon Thames",
    "TW3": "Hounslow", "TW4": "Hounslow", "TW5": "Hounslow",
    "TW7": "Hounslow", "TW8": "Hounslow",
    "TW9": "Richmond upon Thames", "TW10": "Richmond upon Thames",
    "TW11": "Richmond upon Thames", "TW12": "Richmond upon Thames",
    "TW13": "Hounslow", "TW14": "Hounslow",
    "UB1": "Ealing", "UB2": "Ealing", "UB3": "Hillingdon",
    "UB4": "Hillingdon", "UB5": "Ealing", "UB6": "Ealing",
    "UB7": "Hillingdon", "UB8": "Hillingdon", "UB9": "Hillingdon",
    "UB10": "Hillingdon", "UB11": "Hillingdon",
}

# ---------------------------------------------------------------------------
# Known landmarks/roads -> borough (handles boundary-edge cases)
# ---------------------------------------------------------------------------
_LANDMARK_TO_BOROUGH: dict[str, str] = {
    "vallance road": "Tower Hamlets",
    "brick lane": "Tower Hamlets",
    "bethnal green road": "Tower Hamlets",
    "whitechapel road": "Tower Hamlets",
    "mile end road": "Tower Hamlets",
    "commercial road": "Tower Hamlets",
    "cable street": "Tower Hamlets",
    "lambeth palace road": "Lambeth",
    "lambeth road": "Lambeth",
    "lambeth walk": "Lambeth",
    "kennington road": "Lambeth",
    "brixton road": "Lambeth",
    "westminster bridge road": "Lambeth",
    "waterloo road": "Lambeth",
    "the cut": "Lambeth",
    "lower marsh": "Lambeth",
    "borough high street": "Southwark",
    "southwark bridge road": "Southwark",
    "tower bridge road": "Southwark",
    "bermondsey street": "Southwark",
    "st thomas' hospital": "Lambeth",
    "st thomas hospital": "Lambeth",
    "royal london hospital": "Tower Hamlets",
    "kobi nazrul primary": "Tower Hamlets",
}

# Regex to extract a London postcode from text
_POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s*\d[A-Z]{2}\b", re.IGNORECASE
)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


class RoutingAgent:
    """Routes a CivicIssue to the correct council and department."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self._boroughs = self._load_boroughs()
        self._borough_by_name: dict[str, dict] = {}
        for b in self._boroughs:
            name = b.get("short_name", b["name"]).lower()
            self._borough_by_name[name] = b
            # Also index by full council name if different
            if "name" in b:
                self._borough_by_name[b["name"].lower()] = b

    def _load_boroughs(self) -> list[dict]:
        """Load borough data from JSON file, falling back to hardcoded list.

        boroughs.json wraps entries in {"boroughs": [...]} and nests
        coordinates under "center": {"lat": ..., "lon": ...}.  We
        normalise to flat dicts with top-level "lat" / "lon" keys and
        use "short_name" as "name" (matching the fallback format).
        """
        if BOROUGHS_JSON.exists():
            try:
                with open(BOROUGHS_JSON) as f:
                    raw = json.load(f)
                entries = raw.get("boroughs", raw) if isinstance(raw, dict) else raw
                normalised: list[dict] = []
                for b in entries:
                    flat = dict(b)
                    # Flatten nested center coordinates
                    if "center" in flat:
                        flat["lat"] = flat["center"]["lat"]
                        flat["lon"] = flat["center"]["lon"]
                    # Use short_name as canonical name for matching
                    if "short_name" in flat and "name" not in flat:
                        flat["name"] = flat["short_name"]
                    # Add council alias from name if not present
                    if "council" not in flat:
                        flat["council"] = flat["name"]
                    normalised.append(flat)
                if normalised:
                    return normalised
            except (json.JSONDecodeError, KeyError):
                pass
        return _BOROUGHS_FALLBACK

    def _find_borough_by_short_name(self, short_name: str) -> Optional[dict]:
        """Look up a borough dict by its short/display name."""
        return self._borough_by_name.get(short_name.lower())

    def process(self, issue: CivicIssue) -> CivicIssue:
        """Populate council, department, and borough fields."""
        # 1. Determine department from category
        issue.department = _CATEGORY_DEPARTMENT.get(
            issue.category, "General Enquiries"
        )

        # 2. Check for TfL-managed roads
        if self._is_tfl_road(issue):
            issue.council = "Transport for London (TfL)"
            issue.department = "TfL Highways"
            issue.borough = issue.borough or self._nearest_borough_name(issue)
            issue.status = "routed"
            return issue

        # 3. Try known landmark/road name lookup (most precise for boundary cases)
        borough_info = self._borough_from_landmark(issue)
        if borough_info:
            issue.borough = borough_info.get("short_name", borough_info["name"])
            issue.council = borough_info["council"]
            issue.status = "routed"
            return issue

        # 4. Try postcode-prefix lookup (more accurate than centroid)
        borough_info = self._borough_from_postcode(issue)
        if borough_info:
            issue.borough = borough_info.get("short_name", borough_info["name"])
            issue.council = borough_info["council"]
            issue.status = "routed"
            return issue

        # 5. Find borough by coordinates (nearest centroid — fallback)
        if issue.latitude and issue.longitude:
            borough_info = self._nearest_borough(issue.latitude, issue.longitude)
            if borough_info:
                issue.borough = borough_info.get("short_name", borough_info["name"])
                issue.council = borough_info["council"]

        # 6. Fallback: try to infer from address text
        if not issue.council and issue.address:
            borough_info = self._borough_from_text(issue.address)
            if borough_info:
                issue.borough = borough_info.get("short_name", borough_info["name"])
                issue.council = borough_info["council"]

        # 7. Last resort
        if not issue.council:
            issue.council = "Unknown — manual routing required"
            issue.borough = "Unknown"

        issue.status = "routed"
        return issue

    def _is_tfl_road(self, issue: CivicIssue) -> bool:
        """Check if the issue is on a TfL-managed road."""
        text = f"{issue.description} {issue.address}".lower()
        return any(kw in text for kw in _TFL_ROAD_KEYWORDS)

    def _borough_from_landmark(self, issue: CivicIssue) -> Optional[dict]:
        """Check if the issue mentions a known landmark or road near a borough boundary."""
        text = f"{issue.description} {issue.address}".lower()
        for landmark, borough_name in _LANDMARK_TO_BOROUGH.items():
            if landmark in text:
                return self._find_borough_by_short_name(borough_name)
        return None

    def _borough_from_postcode(self, issue: CivicIssue) -> Optional[dict]:
        """Extract a postcode from the issue text and look up the borough."""
        text = f"{issue.description} {issue.address}"
        match = _POSTCODE_RE.search(text)
        if not match:
            return None
        district = match.group(1).upper()
        # Try exact match first (e.g. "E1W"), then prefix without trailing letter
        borough_name = _POSTCODE_TO_BOROUGH.get(district)
        if not borough_name and len(district) > 2 and district[-1].isalpha():
            borough_name = _POSTCODE_TO_BOROUGH.get(district[:-1])
        if borough_name:
            return self._find_borough_by_short_name(borough_name)
        return None

    def _nearest_borough(self, lat: float, lon: float) -> Optional[dict]:
        """Find the borough whose centre is closest to the given coords."""
        best, best_dist = None, float("inf")
        for b in self._boroughs:
            d = _haversine_km(lat, lon, b["lat"], b["lon"])
            if d < best_dist:
                best, best_dist = b, d
        return best

    def _nearest_borough_name(self, issue: CivicIssue) -> str:
        if issue.latitude and issue.longitude:
            b = self._nearest_borough(issue.latitude, issue.longitude)
            if b:
                return b.get("short_name", b["name"])
        return ""

    def _borough_from_text(self, text: str) -> Optional[dict]:
        """Fuzzy match borough name in text."""
        lower = text.lower()
        for b in self._boroughs:
            if b["name"].lower() in lower:
                return b
            # Also check short_name if present (from boroughs.json)
            if b.get("short_name", "").lower() in lower:
                return b
        return None
