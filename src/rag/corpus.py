"""CorpusManager — load all London RAG datasets and build text chunks."""

from __future__ import annotations

import csv
import json
import logging
import math
from pathlib import Path
from typing import Any, Optional

from src.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# OSGB36 -> WGS84 (reuse from proximity_index)
# ---------------------------------------------------------------------------

def _osgb36_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """Convert British National Grid easting/northing to WGS84 lat/lon."""
    a = 6377563.396
    b = 6356256.909
    e2 = 1 - (b * b) / (a * a)
    F0 = 0.9996012717
    lat0 = math.radians(49)
    lon0 = math.radians(-2)
    N0 = -100000
    E0 = 400000

    n = (a - b) / (a + b)
    n2 = n * n
    n3 = n * n * n

    lat = lat0
    M = 0
    while True:
        lat = (northing - N0 - M) / (a * F0) + lat
        Ma = (1 + n + (5 / 4) * n2 + (5 / 4) * n3) * (lat - lat0)
        Mb = (3 * n + 3 * n2 + (21 / 8) * n3) * math.sin(lat - lat0) * math.cos(lat + lat0)
        Mc = ((15 / 8) * n2 + (15 / 8) * n3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
        Md = (35 / 24) * n3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)
        if abs(northing - N0 - M) < 0.00001:
            break

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    tan_lat = math.tan(lat)

    nu = a * F0 / math.sqrt(1 - e2 * sin_lat * sin_lat)
    rho = a * F0 * (1 - e2) / ((1 - e2 * sin_lat * sin_lat) ** 1.5)
    eta2 = nu / rho - 1

    VII = tan_lat / (2 * rho * nu)
    VIII = tan_lat / (24 * rho * nu ** 3) * (5 + 3 * tan_lat ** 2 + eta2 - 9 * tan_lat ** 2 * eta2)
    IX = tan_lat / (720 * rho * nu ** 5) * (61 + 90 * tan_lat ** 2 + 45 * tan_lat ** 4)
    X = 1 / (cos_lat * nu)
    XI = 1 / (cos_lat * 6 * nu ** 3) * (nu / rho + 2 * tan_lat ** 2)
    XII = 1 / (cos_lat * 120 * nu ** 5) * (5 + 28 * tan_lat ** 2 + 24 * tan_lat ** 4)
    XIIA = 1 / (cos_lat * 5040 * nu ** 7) * (61 + 662 * tan_lat ** 2 + 1320 * tan_lat ** 4 + 720 * tan_lat ** 6)

    dE = easting - E0

    lat_osgb = lat - VII * dE ** 2 + VIII * dE ** 4 - IX * dE ** 6
    lon_osgb = lon0 + X * dE - XI * dE ** 3 + XII * dE ** 5 - XIIA * dE ** 7

    sin_lo = math.sin(lat_osgb)
    cos_lo = math.cos(lat_osgb)
    sin_la = math.sin(lon_osgb)
    cos_la = math.cos(lon_osgb)

    nu_o = a / math.sqrt(1 - e2 * sin_lo * sin_lo)
    x1 = nu_o * cos_lo * cos_la
    y1 = nu_o * cos_lo * sin_la
    z1 = ((1 - e2) * nu_o) * sin_lo

    tx, ty, tz = 446.448, -125.157, 542.060
    s = -20.4894e-6
    rx = math.radians(0.1502 / 3600)
    ry = math.radians(0.2470 / 3600)
    rz = math.radians(0.8421 / 3600)

    x2 = tx + (1 + s) * x1 + (-rz) * y1 + (ry) * z1
    y2 = ty + (rz) * x1 + (1 + s) * y1 + (-rx) * z1
    z2 = tz + (-ry) * x1 + (rx) * y1 + (1 + s) * z1

    a_wgs = 6378137.0
    b_wgs = 6356752.3142
    e2_wgs = 1 - (b_wgs * b_wgs) / (a_wgs * a_wgs)

    p = math.sqrt(x2 * x2 + y2 * y2)
    lat_wgs = math.atan2(z2, p * (1 - e2_wgs))
    for _ in range(10):
        nu_w = a_wgs / math.sqrt(1 - e2_wgs * math.sin(lat_wgs) ** 2)
        lat_wgs = math.atan2(z2 + e2_wgs * nu_w * math.sin(lat_wgs), p)

    lon_wgs = math.atan2(y2, x2)
    return math.degrees(lat_wgs), math.degrees(lon_wgs)


# ---------------------------------------------------------------------------
# London postcode prefix set
# ---------------------------------------------------------------------------

_LONDON_POSTCODE_AREAS = {
    "E", "EC", "N", "NW", "SE", "SW", "W", "WC",
}


def _is_london_postcode(postcode: str) -> bool:
    if not postcode:
        return False
    pc = postcode.strip().upper()
    area = ""
    for ch in pc:
        if ch.isalpha():
            area += ch
        else:
            break
    return area in _LONDON_POSTCODE_AREAS


# ---------------------------------------------------------------------------
# Severity label lookup
# ---------------------------------------------------------------------------

_SEVERITY_LABELS = {1: "fatal", 2: "serious", 3: "slight"}


# ---------------------------------------------------------------------------
# CorpusManager
# ---------------------------------------------------------------------------

class CorpusManager:
    """Load all London datasets from data/raw/ and create RAG text chunks.

    Each chunk is a dict with keys:
      text            - human-readable description for RAG retrieval
      lat, lon        - WGS84 coordinates (float, may be None for census)
      source_dataset  - one of: collisions, schools, hospitals, care_homes, census
      metadata        - dict of structured fields from the source record
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or RAW_DATA_DIR
        self._chunks: list[dict[str, Any]] = []
        # Postcode sector -> (lat, lon) built from schools for geocoding
        self._postcode_coords: dict[str, tuple[float, float]] = {}

    @property
    def chunks(self) -> list[dict[str, Any]]:
        return self._chunks

    # -- public API ----------------------------------------------------------

    def build_index(self) -> int:
        """Load all datasets and return total chunk count."""
        self._chunks = []
        self._postcode_coords = {}

        # Schools first (builds postcode lookup for geocoding hospitals/care homes)
        self._load_schools()
        self._load_collisions()
        self._load_hospitals()
        self._load_care_homes()
        self._load_census()
        self._load_traffic()

        logger.info("Corpus built: %d total chunks", len(self._chunks))
        return len(self._chunks)

    def get_context_for_issue(
        self,
        lat: float,
        lon: float,
        radius_km: float = 1.0,
        max_chunks: int = 20,
    ) -> list[dict[str, Any]]:
        """Return the most relevant chunks near a location, sorted by distance."""
        results: list[dict[str, Any]] = []
        for chunk in self._chunks:
            clat = chunk.get("lat")
            clon = chunk.get("lon")
            if clat is None or clon is None:
                continue
            dist = _haversine_km(lat, lon, clat, clon)
            if dist <= radius_km:
                results.append({**chunk, "_distance_km": round(dist, 3)})

        results.sort(key=lambda x: x["_distance_km"])
        return results[:max_chunks]

    def get_stats(self) -> dict[str, Any]:
        """Return summary of loaded data."""
        by_dataset: dict[str, int] = {}
        geo_count = 0
        lat_min = lat_max = lon_min = lon_max = None

        for chunk in self._chunks:
            ds = chunk.get("source_dataset", "unknown")
            by_dataset[ds] = by_dataset.get(ds, 0) + 1
            clat = chunk.get("lat")
            clon = chunk.get("lon")
            if clat is not None and clon is not None:
                geo_count += 1
                if lat_min is None:
                    lat_min = lat_max = clat
                    lon_min = lon_max = clon
                else:
                    lat_min = min(lat_min, clat)
                    lat_max = max(lat_max, clat)
                    lon_min = min(lon_min, clon)
                    lon_max = max(lon_max, clon)

        return {
            "total_chunks": len(self._chunks),
            "chunks_by_dataset": by_dataset,
            "geo_chunks": geo_count,
            "bounding_box": {
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lon_min": lon_min,
                "lon_max": lon_max,
            } if lat_min is not None else None,
        }

    # -- search helpers (kept for backwards compatibility) -------------------

    def search_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 1.0,
        dataset_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return chunks within *radius_km* of the given point."""
        results: list[dict[str, Any]] = []
        for chunk in self._chunks:
            if dataset_name and chunk.get("source_dataset") != dataset_name:
                continue
            clat = chunk.get("lat")
            clon = chunk.get("lon")
            if clat is None or clon is None:
                continue
            dist = _haversine_km(lat, lon, clat, clon)
            if dist <= radius_km:
                results.append({**chunk, "_distance_km": round(dist, 3)})
        results.sort(key=lambda x: x["_distance_km"])
        return results

    def search_text(self, query: str, dataset_name: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Simple keyword search across chunks."""
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        for chunk in self._chunks:
            if dataset_name and chunk.get("source_dataset") != dataset_name:
                continue
            if query_lower in chunk.get("text", "").lower():
                results.append(chunk)
                if len(results) >= limit:
                    break
        return results

    # -- dataset loaders -----------------------------------------------------

    def _load_collisions(self) -> None:
        """Load STATS19 collision data, filtering to London."""
        path = self._data_dir / "stats19" / "collisions_2024.csv"
        if not path.exists():
            logger.warning("Collisions CSV not found: %s", path)
            return

        # Pre-load casualties for enrichment: collision_index -> list of casualty info
        casualty_map = self._load_casualties()

        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter to London: Metropolitan Police (1) or City of London (97)
                    pf = row.get("police_force", "")
                    if pf not in ("1", "97"):
                        continue

                    try:
                        lat = float(row.get("latitude", ""))
                        lon = float(row.get("longitude", ""))
                    except (ValueError, TypeError):
                        continue

                    sev_code = row.get("collision_severity", "3")
                    try:
                        sev_int = int(sev_code)
                    except ValueError:
                        sev_int = 3
                    sev_label = _SEVERITY_LABELS.get(sev_int, "unknown")

                    date = row.get("date", "unknown")
                    speed_limit = row.get("speed_limit", "")
                    num_vehicles = row.get("number_of_vehicles", "")
                    num_casualties = row.get("number_of_casualties", "")

                    # Build casualty description from linked records
                    collision_index = row.get("collision_index", "")
                    casualties = casualty_map.get(collision_index, [])
                    casualty_parts = []
                    for cas in casualties:
                        casualty_parts.append(cas)

                    # Compose text chunk
                    parts = [f"Road collision on {date}"]
                    parts.append(f"Severity: {sev_label}")
                    if num_vehicles:
                        parts.append(f"{num_vehicles} vehicle(s)")
                    if num_casualties:
                        parts.append(f"{num_casualties} casualt{'y' if num_casualties == '1' else 'ies'}")
                    if speed_limit and speed_limit != "-1":
                        parts.append(f"{speed_limit}mph zone")
                    if casualty_parts:
                        parts.append("Involving: " + ", ".join(casualty_parts[:3]))

                    text = ". ".join(parts) + f". Location: {lat:.4f}, {lon:.4f}"

                    self._chunks.append({
                        "text": text,
                        "lat": lat,
                        "lon": lon,
                        "source_dataset": "collisions",
                        "metadata": {
                            "date": date,
                            "severity": sev_int,
                            "severity_label": sev_label,
                            "speed_limit": speed_limit,
                            "num_vehicles": num_vehicles,
                            "num_casualties": num_casualties,
                            "collision_index": collision_index,
                        },
                    })
                    count += 1
        except Exception:
            logger.exception("Failed to load collisions CSV")

        logger.info("Loaded %d London collision chunks", count)

    def _load_casualties(self) -> dict[str, list[str]]:
        """Load STATS19 casualties and group by collision_index.

        Returns a mapping: collision_index -> list of short casualty descriptions.
        """
        path = self._data_dir / "stats19" / "casualties_2024.csv"
        if not path.exists():
            return {}

        _CASUALTY_CLASS = {"1": "driver/rider", "2": "passenger", "3": "pedestrian"}
        _CASUALTY_TYPE = {
            "0": "pedestrian", "1": "cyclist", "2": "motorcyclist",
            "8": "car occupant", "9": "car occupant",
            "10": "minibus occupant", "11": "bus occupant",
        }

        result: dict[str, list[str]] = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    idx = row.get("collision_index", "")
                    if not idx:
                        continue
                    cas_class = _CASUALTY_CLASS.get(
                        row.get("casualty_class", ""), ""
                    )
                    cas_type = _CASUALTY_TYPE.get(
                        row.get("casualty_type", ""), ""
                    )
                    label = cas_type or cas_class or "unknown"

                    sev = row.get("casualty_severity", "3")
                    sev_label = _SEVERITY_LABELS.get(int(sev) if sev.isdigit() else 3, "")
                    if sev_label and sev_label != "slight":
                        label = f"{label} ({sev_label} injury)"

                    result.setdefault(idx, []).append(label)
        except Exception:
            logger.exception("Failed to load casualties CSV")

        return result

    def _load_schools(self) -> None:
        """Load London schools from GIAS register."""
        path = self._data_dir / "schools" / "london_schools.csv"
        if not path.exists():
            logger.warning("Schools CSV not found: %s", path)
            return

        from collections import defaultdict
        postcode_accum: dict[str, list[tuple[float, float]]] = defaultdict(list)
        count = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("EstablishmentStatus (name)") != "Open":
                        continue

                    easting_s = row.get("Easting", "").strip()
                    northing_s = row.get("Northing", "").strip()
                    if not easting_s or not northing_s:
                        continue
                    try:
                        easting = float(easting_s)
                        northing = float(northing_s)
                    except ValueError:
                        continue
                    if easting == 0 or northing == 0:
                        continue

                    lat, lon = _osgb36_to_latlon(easting, northing)
                    name = row.get("EstablishmentName", "Unknown School")
                    phase = row.get("PhaseOfEducation (name)", "")
                    postcode = row.get("Postcode", "").strip()
                    la_name = row.get("LA (name)", "")
                    school_type = row.get("TypeOfEstablishment (name)", "")
                    num_pupils = row.get("NumberOfPupils", "")

                    # Build text
                    parts = [name]
                    if school_type:
                        parts[0] += f", {school_type.lower()}"
                    if postcode:
                        parts.append(f"at {postcode}")
                    if la_name:
                        parts.append(la_name)
                    parts.append("Currently open")
                    if num_pupils and num_pupils not in ("", "0"):
                        parts.append(f"{num_pupils} pupils")
                    if phase:
                        parts.append(f"Phase: {phase}")

                    text = ". ".join(parts)

                    self._chunks.append({
                        "text": text,
                        "lat": lat,
                        "lon": lon,
                        "source_dataset": "schools",
                        "metadata": {
                            "name": name,
                            "phase": phase,
                            "postcode": postcode,
                            "la_name": la_name,
                            "school_type": school_type,
                            "num_pupils": num_pupils,
                        },
                    })
                    count += 1

                    # Build postcode sector lookup for geocoding other datasets
                    if postcode:
                        sector = _postcode_sector(postcode)
                        if sector:
                            postcode_accum[sector].append((lat, lon))
        except Exception:
            logger.exception("Failed to load schools CSV")
            return

        # Average coordinates per postcode sector
        for sector, coords in postcode_accum.items():
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            self._postcode_coords[sector] = (avg_lat, avg_lon)

        logger.info("Loaded %d school chunks, %d postcode sectors", count, len(self._postcode_coords))

    def _load_hospitals(self) -> None:
        """Load NHS trust sites, filtering to London by postcode."""
        path = self._data_dir / "hospitals" / "nhs_trusts_sites.csv"
        if not path.exists():
            logger.warning("Hospitals CSV not found: %s", path)
            return

        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 10:
                        continue
                    postcode = row[9].strip()
                    if not _is_london_postcode(postcode):
                        continue

                    name = row[1].strip()
                    address = row[4].strip() if len(row) > 4 else ""

                    # Geocode via postcode sector
                    sector = _postcode_sector(postcode)
                    coords = self._postcode_coords.get(sector) if sector else None
                    if not coords:
                        continue

                    lat, lon = coords

                    parts = [name]
                    if address:
                        parts.append(f"NHS site at {address}")
                    parts.append(postcode)

                    text = ", ".join(parts)

                    self._chunks.append({
                        "text": text,
                        "lat": lat,
                        "lon": lon,
                        "source_dataset": "hospitals",
                        "metadata": {
                            "name": name,
                            "postcode": postcode,
                            "address": address,
                            "ods_code": row[0].strip() if row else "",
                        },
                    })
                    count += 1
        except Exception:
            logger.exception("Failed to load hospitals CSV")

        logger.info("Loaded %d London hospital chunks", count)

    def _load_care_homes(self) -> None:
        """Load CQC care directory, filtering to London."""
        path = self._data_dir / "care_homes" / "cqc_directory.csv"
        if not path.exists():
            logger.warning("Care homes CSV not found: %s", path)
            return

        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                # Skip 4 metadata rows
                for _ in range(4):
                    next(f)
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Region", "").strip() != "London":
                        continue

                    name = row.get("Name", "Unknown")
                    postcode = row.get("Postcode", "").strip()
                    service_type = row.get("Service types", "")
                    la = row.get("Local authority", "")
                    provider = row.get("Provider name", "")

                    # Geocode via postcode sector
                    sector = _postcode_sector(postcode)
                    coords = self._postcode_coords.get(sector) if sector else None
                    if not coords:
                        continue

                    lat, lon = coords

                    parts = [name]
                    if service_type:
                        parts.append(service_type.lower())
                    if postcode:
                        parts.append(f"at {postcode}")
                    if la:
                        parts.append(la)
                    if provider and provider != name:
                        parts.append(f"Provider: {provider}")

                    text = ". ".join(parts)

                    self._chunks.append({
                        "text": text,
                        "lat": lat,
                        "lon": lon,
                        "source_dataset": "care_homes",
                        "metadata": {
                            "name": name,
                            "postcode": postcode,
                            "service_type": service_type,
                            "local_authority": la,
                            "provider": provider,
                        },
                    })
                    count += 1
        except Exception:
            logger.exception("Failed to load care homes CSV")

        logger.info("Loaded %d London care home chunks", count)

    def _load_traffic(self) -> None:
        """Load DfT AADF traffic count points for London."""
        path = self._data_dir / "traffic" / "london_aadf_2025.csv"
        if not path.exists():
            logger.warning("Traffic CSV not found: %s", path)
            return

        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat = float(row.get("latitude", ""))
                        lon = float(row.get("longitude", ""))
                        aadf = int(row.get("all_motor_vehicles", "0"))
                    except (ValueError, TypeError):
                        continue
                    if not (51.2 <= lat <= 51.8 and -0.6 <= lon <= 0.4):
                        continue

                    road_name = row.get("road_name", "").strip()
                    road_type = row.get("road_type", "").strip()
                    borough = row.get("local_authority_name", "").strip()

                    try:
                        all_hgvs = int(row.get("all_hgvs", "0"))
                    except (ValueError, TypeError):
                        all_hgvs = 0
                    try:
                        cars = int(row.get("cars_and_taxis", "0"))
                    except (ValueError, TypeError):
                        cars = 0
                    try:
                        buses = int(row.get("buses_and_coaches", "0"))
                    except (ValueError, TypeError):
                        buses = 0
                    try:
                        cycles = int(row.get("pedal_cycles", "0"))
                    except (ValueError, TypeError):
                        cycles = 0

                    # Chunk text per task spec
                    text = (
                        f"Traffic count point on {road_name or 'unnamed road'} "
                        f"in {borough or 'London'}: ~{aadf:,} vehicles/day, "
                        f"including {all_hgvs:,} HGVs."
                    )

                    self._chunks.append({
                        "text": text,
                        "lat": lat,
                        "lon": lon,
                        "source_dataset": "traffic",
                        "metadata": {
                            "count_point_id": row.get("count_point_id", ""),
                            "year": row.get("year", ""),
                            "road_name": road_name,
                            "road_type": road_type,
                            "borough": borough,
                            "aadf": aadf,
                            "all_hgvs": all_hgvs,
                            "cars_and_taxis": cars,
                            "buses_and_coaches": buses,
                            "pedal_cycles": cycles,
                        },
                    })
                    count += 1
        except Exception:
            logger.exception("Failed to load traffic CSV")

        logger.info("Loaded %d London traffic count chunks", count)

    def _load_census(self) -> None:
        """Load Census LSOA population density for London."""
        path = self._data_dir / "census" / "london_lsoa_population_density.csv"
        if not path.exists():
            logger.warning("Census CSV not found: %s", path)
            return

        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lsoa_code = row.get("LSOA 2021 Code", "").strip()
                    lsoa_name = row.get("LSOA 2021 Name", "").strip()
                    borough = row.get("LAD 2023 Name", "").strip()
                    population = row.get("Mid-2024: Population", "")
                    density = row.get("Mid-2024: People per Sq Km", "")
                    area = row.get("Area Sq Km", "")

                    if not lsoa_code:
                        continue

                    parts = [f"{lsoa_name} ({lsoa_code})"]
                    if borough:
                        parts.append(borough)
                    if population:
                        parts.append(f"population {population}")
                    if density:
                        parts.append(f"{density} people per sq km")
                    if area:
                        parts.append(f"area {area} sq km")

                    text = ". ".join(parts)

                    # Census chunks don't have precise lat/lon (they're area-based)
                    self._chunks.append({
                        "text": text,
                        "lat": None,
                        "lon": None,
                        "source_dataset": "census",
                        "metadata": {
                            "lsoa_code": lsoa_code,
                            "lsoa_name": lsoa_name,
                            "borough": borough,
                            "population": population,
                            "density": density,
                            "area_sq_km": area,
                        },
                    })
                    count += 1
        except Exception:
            logger.exception("Failed to load census CSV")

        logger.info("Loaded %d census LSOA chunks", count)

    # -- serialisation -------------------------------------------------------

    def to_json(self) -> str:
        """Serialise chunks to JSON string."""
        return json.dumps(self._chunks, ensure_ascii=False)

    def save(self, path: str | Path) -> None:
        """Save chunks to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        logger.info("Saved %d chunks to %s", len(self._chunks), path)

    def load(self, path: str | Path) -> int:
        """Load pre-built chunks from a JSON file. Returns chunk count."""
        path = Path(path)
        if not path.exists():
            return 0
        self._chunks = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Loaded %d chunks from %s", len(self._chunks), path)
        return len(self._chunks)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _postcode_sector(postcode: str) -> Optional[str]:
    """Extract postcode sector (e.g. 'SW1A 1' from 'SW1A 1AA')."""
    pc = postcode.strip().upper()
    if not pc:
        return None
    parts = pc.split()
    if len(parts) == 2 and len(parts[1]) >= 1:
        return parts[0] + " " + parts[1][0]
    if len(pc) >= 5:
        return pc[:-2].rstrip() + " " + pc[-3]
    return None
