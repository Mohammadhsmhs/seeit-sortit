"""TfL Unified API client — live calls (free, no auth required for basic endpoints).

The TfL Unified API (https://api.tfl.gov.uk) is publicly accessible.
No authentication is needed for the endpoints used here; an optional
``app_key`` raises rate limits from ~50 req/min to ~500 req/min.

Endpoints used:
  - GET /Road/{road_id}             — road corridor status (free, no key)
  - GET /Road/{road_id}/Disruption  — disruptions on a specific road (free)
  - GET /Road/all/Disruption        — all current road disruptions (free)
  - GET /AccidentStats/{year}       — historical accidents (free, only years
                                      up to ~2019 are available; 2020+ returns
                                      400 Bad Request)
"""

from __future__ import annotations

import logging
import math
from typing import Any

import requests

from src.config import TFL_APP_KEY, TFL_BASE_URL

logger = logging.getLogger(__name__)


class TfLClient:
    """Client for the Transport for London Unified API.

    Base URL: https://api.tfl.gov.uk
    No authentication needed for basic endpoints; app_key raises rate limits.
    """

    def __init__(
        self,
        base_url: str = TFL_BASE_URL,
        app_key: str = TFL_APP_KEY,
        timeout: int = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.timeout = timeout

    def _params(self) -> dict[str, str]:
        p: dict[str, str] = {}
        if self.app_key:
            p["app_key"] = self.app_key
        return p

    def _get(self, path: str, params: dict | None = None) -> Any:
        all_params = {**self._params(), **(params or {})}
        resp = requests.get(
            f"{self.base_url}{path}",
            params=all_params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # -- Road Status ---------------------------------------------------------

    def get_road_status(self, road_id: str = "A2") -> dict[str, Any]:
        """GET /Road/{road_id} — live road corridor status.

        Returns a dict with keys: id, displayName, statusSeverity,
        statusSeverityDescription, bounds, envelope, url.

        Example:
            >>> client.get_road_status("A205")
            {"id": "a205", "displayName": "South Circular (A205)",
             "statusSeverity": "Good",
             "statusSeverityDescription": "No Exceptional Delays", ...}

        Returns an empty dict on error (e.g. unrecognised road ID).
        """
        try:
            data = self._get(f"/Road/{road_id}")
            # API returns a list with one item
            if isinstance(data, list) and data:
                return data[0]
            return data if isinstance(data, dict) else {}
        except requests.RequestException:
            logger.warning("TfL Road status request failed for %s", road_id, exc_info=True)
            return {}

    # -- Per-road Disruptions ------------------------------------------------

    def get_road_disruptions_for(self, road_id: str) -> list[dict[str, Any]]:
        """GET /Road/{road_id}/Disruption — disruptions on a specific road.

        Much more efficient than fetching all disruptions when you know
        the road ID.  Returns a list of disruption dicts.
        """
        try:
            data = self._get(f"/Road/{road_id}/Disruption")
            return data if isinstance(data, list) else []
        except requests.RequestException:
            logger.warning("TfL Road disruption request failed for %s", road_id, exc_info=True)
            return []

    # -- All Road Disruptions ------------------------------------------------

    def get_road_disruptions(
        self, severity: str | None = None
    ) -> list[dict[str, Any]]:
        """GET /Road/all/Disruption — all current road disruptions in London.

        Each item has: id, url, point, severity, ordinal, category,
        subCategory, comments, currentUpdate, geography, streets.
        """
        params: dict[str, str] = {}
        if severity:
            params["severities"] = severity
        try:
            return self._get("/Road/all/Disruption", params)
        except requests.RequestException:
            logger.warning("TfL all-disruptions request failed", exc_info=True)
            return []

    # -- Accident Stats ------------------------------------------------------

    def get_accidents(self, year: int = 2019) -> list[dict[str, Any]]:
        """GET /AccidentStats/{year} — historical accident data.

        NOTE: Only years up to ~2019 are available on the public API.
        Requesting 2020+ returns a 400 error.  The response for a full
        year is very large (~35 MB JSON); prefer filtering client-side
        after fetching.

        Each item has: id, lat, lon, severity, borough, casualties,
        vehicles, date, location.
        """
        try:
            return self._get(f"/AccidentStats/{year}")
        except requests.RequestException:
            logger.warning("TfL AccidentStats request failed for year %d", year, exc_info=True)
            return []

    # -- Convenience: nearby disruptions -------------------------------------

    def get_disruptions_near(
        self, lat: float, lon: float, radius_m: int = 500
    ) -> list[dict[str, Any]]:
        """Find current disruptions near a point (client-side filter).

        Fetches all disruptions via /Road/all/Disruption then filters to
        those whose geography Point falls within *radius_m* metres of
        (lat, lon).  Returns disruptions sorted by distance, each
        augmented with ``_distance_m``.
        """
        all_disruptions = self.get_road_disruptions()
        results: list[dict[str, Any]] = []
        for d in all_disruptions:
            geo = d.get("geography") or {}
            if not isinstance(geo, dict):
                continue
            coords = geo.get("coordinates")
            if not isinstance(coords, list) or len(coords) < 2:
                continue
            d_lon, d_lat = coords[0], coords[1]
            dist_m = _haversine_m(lat, lon, d_lat, d_lon)
            if dist_m <= radius_m:
                results.append({**d, "_distance_m": round(dist_m)})
        results.sort(key=lambda x: x["_distance_m"])
        return results

    # -- Convenience: summarise road status for severity agent ---------------

    def get_road_status_summary(self, road_id: str) -> str | None:
        """Return a human-readable one-liner about the road's current state.

        Returns None if the road is in normal condition or the API call
        fails, so callers can simply skip it.

        Example return: "Active disruption on South Circular (A205): Serious
        — Utility works at St Mildreds Road"
        """
        status = self.get_road_status(road_id)
        if not status:
            return None

        display_name = status.get("displayName", road_id.upper())
        severity = status.get("statusSeverity", "")
        description = status.get("statusSeverityDescription", "")

        # If the road is "Good" / "No Exceptional Delays", check for
        # individual disruptions which may still be present.
        disruptions = self.get_road_disruptions_for(road_id)
        active = [d for d in disruptions if d.get("status") == "Active"]

        if active:
            first = active[0]
            d_severity = first.get("severity", "Unknown")
            d_category = first.get("subCategory") or first.get("category", "disruption")
            d_location = first.get("location", "")
            summary = f"Active disruption on {display_name}: {d_severity} — {d_category}"
            if d_location:
                summary += f" at {d_location}"
            if len(active) > 1:
                summary += f" (+{len(active) - 1} more)"
            return summary

        if severity and severity.lower() != "good":
            return f"{display_name}: {severity} — {description}"

        return None


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two points."""
    R = 6_371_000  # Earth radius in metres
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
