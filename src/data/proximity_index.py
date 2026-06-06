"""Spatial proximity index for London civic data.

Loads schools, hospitals, care homes, collision history, and population
density from the RAG corpus CSVs and exposes fast radius queries using a
grid-based spatial index (0.01-degree cells ≈ 1.1 km × 0.7 km in London).
"""

from __future__ import annotations

import csv
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class School:
    name: str
    lat: float
    lon: float
    phase: str  # Primary, Secondary, etc.


@dataclass(slots=True)
class Hospital:
    name: str
    lat: float
    lon: float


@dataclass(slots=True)
class CareHome:
    name: str
    lat: float
    lon: float
    service_type: str


@dataclass(slots=True)
class Collision:
    lat: float
    lon: float
    severity: int  # 1=fatal, 2=serious, 3=slight
    date: str


@dataclass(slots=True)
class TrafficCountPoint:
    """A DfT AADF traffic count point."""
    lat: float
    lon: float
    aadf: int  # all_motor_vehicles — annual average daily flow
    road_name: str
    road_category: str  # Major or Minor
    all_hgvs: int = 0


# ---------------------------------------------------------------------------
# OSGB36 (British National Grid) -> WGS84 conversion
# ---------------------------------------------------------------------------
# Helmert transform constants for OSGB36 -> WGS84
# Reference: Ordnance Survey guide to coordinate systems in Great Britain

def _osgb36_to_latlon(easting: float, northing: float) -> tuple[float, float]:
    """Convert British National Grid easting/northing to WGS84 lat/lon.

    Uses the standard OSGB36 to WGS84 transform via an intermediate
    Transverse Mercator -> geodetic -> Helmert -> geodetic pipeline.
    Accuracy is typically within a few metres -- sufficient for proximity.
    """
    # Airy 1830 ellipsoid (OSGB36)
    a = 6377563.396
    b = 6356256.909
    e2 = 1 - (b * b) / (a * a)
    # National Grid constants
    F0 = 0.9996012717
    lat0 = math.radians(49)
    lon0 = math.radians(-2)
    N0 = -100000
    E0 = 400000

    n = (a - b) / (a + b)
    n2 = n * n
    n3 = n * n * n

    # Iterative latitude from northing
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

    # Helmert transform OSGB36 -> WGS84
    # Convert to Cartesian, apply transform, convert back
    sin_lo = math.sin(lat_osgb)
    cos_lo = math.cos(lat_osgb)
    sin_la = math.sin(lon_osgb)
    cos_la = math.cos(lon_osgb)

    nu_o = a / math.sqrt(1 - e2 * sin_lo * sin_lo)
    x1 = (nu_o + 0) * cos_lo * cos_la  # height ~0
    y1 = (nu_o + 0) * cos_lo * sin_la
    z1 = ((1 - e2) * nu_o + 0) * sin_lo

    # Helmert parameters (OSGB36 -> WGS84)
    tx, ty, tz = 446.448, -125.157, 542.060
    s = -20.4894e-6
    rx = math.radians(0.1502 / 3600)
    ry = math.radians(0.2470 / 3600)
    rz = math.radians(0.8421 / 3600)

    x2 = tx + (1 + s) * x1 + (-rz) * y1 + (ry) * z1
    y2 = ty + (rz) * x1 + (1 + s) * y1 + (-rx) * z1
    z2 = tz + (-ry) * x1 + (rx) * y1 + (1 + s) * z1

    # WGS84 ellipsoid
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
# Haversine distance
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Grid-based spatial index
# ---------------------------------------------------------------------------

_CELL_SIZE = 0.01  # ~1.1 km lat, ~0.7 km lon in London


def _cell(lat: float, lon: float) -> tuple[int, int]:
    return int(lat / _CELL_SIZE), int(lon / _CELL_SIZE)


def _nearby_cells(lat: float, lon: float, radius_km: float) -> list[tuple[int, int]]:
    """Return grid cells that could contain points within radius_km."""
    # 0.01 degree latitude ≈ 1.11 km; longitude ≈ 0.70 km at 51.5°N
    lat_cells = int(radius_km / 1.11) + 1
    lon_cells = int(radius_km / 0.70) + 1
    cy, cx = _cell(lat, lon)
    cells = []
    for dy in range(-lat_cells, lat_cells + 1):
        for dx in range(-lon_cells, lon_cells + 1):
            cells.append((cy + dy, cx + dx))
    return cells


class _SpatialGrid:
    """Simple grid index mapping (lat, lon) items to 0.01° cells."""

    def __init__(self):
        self._buckets: dict[tuple[int, int], list] = defaultdict(list)
        self._count = 0

    def insert(self, item, lat: float, lon: float) -> None:
        self._buckets[_cell(lat, lon)].append((lat, lon, item))
        self._count += 1

    def query(self, lat: float, lon: float, radius_km: float) -> list:
        """Return all items within radius_km of (lat, lon)."""
        results = []
        for cell_key in _nearby_cells(lat, lon, radius_km):
            for plat, plon, item in self._buckets.get(cell_key, ()):
                if _haversine_km(lat, lon, plat, plon) <= radius_km:
                    results.append(item)
        return results

    def __len__(self) -> int:
        return self._count


# ---------------------------------------------------------------------------
# London postcode prefix set (for hospital filtering)
# ---------------------------------------------------------------------------

_LONDON_POSTCODE_AREAS = {
    "E", "EC", "N", "NW", "SE", "SW", "W", "WC",
}


def _is_inner_london_postcode(postcode: str) -> bool:
    """Check if postcode starts with a core London prefix."""
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
# ProximityIndex
# ---------------------------------------------------------------------------

class ProximityIndex:
    """Spatial index over London schools, hospitals, care homes, collisions,
    and population density data.

    Initialisation loads and indexes all available CSV files.  If a file is
    missing or unparseable the corresponding index is left empty and a
    warning is logged.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or RAW_DATA_DIR

        self._school_grid = _SpatialGrid()
        self._hospital_grid = _SpatialGrid()
        self._care_home_grid = _SpatialGrid()
        self._collision_grid = _SpatialGrid()
        self._traffic_grid = _SpatialGrid()

        # LSOA code -> density (people per sq km)
        self._lsoa_density: dict[str, float] = {}
        # Grid of (lat, lon, lsoa_code) for nearest-LSOA lookup
        self._lsoa_grid = _SpatialGrid()

        # Flat list of all loaded traffic count points (for callers that want
        # to iterate, e.g. RAG corpus build / sanity check)
        self.traffic_points: list[TrafficCountPoint] = []

        # Postcode sector -> (lat, lon) built from schools for geocoding
        self._postcode_coords: dict[str, tuple[float, float]] = {}

        self._load_all()

    # -- Public query methods -----------------------------------------------

    def schools_within(self, lat: float, lon: float, radius_km: float) -> list[School]:
        return self._school_grid.query(lat, lon, radius_km)

    def hospitals_within(self, lat: float, lon: float, radius_km: float) -> list[Hospital]:
        return self._hospital_grid.query(lat, lon, radius_km)

    def care_homes_within(self, lat: float, lon: float, radius_km: float) -> list[CareHome]:
        return self._care_home_grid.query(lat, lon, radius_km)

    def collisions_within(
        self, lat: float, lon: float, radius_km: float, years_back: int = 3
    ) -> list[Collision]:
        all_nearby = self._collision_grid.query(lat, lon, radius_km)
        if years_back is None:
            return all_nearby
        # The collision dates are "DD/MM/YYYY" format; filter by year
        try:
            from datetime import datetime, timedelta
            cutoff_year = datetime.now().year - years_back
            return [c for c in all_nearby if _collision_year(c.date) >= cutoff_year]
        except Exception:
            return all_nearby

    def traffic_flow_at(
        self, lat: float, lon: float, radius_m: float = 200
    ) -> Optional[TrafficCountPoint]:
        """Return the *busiest* nearby DfT AADF count point (highest AADF).

        Args:
            lat, lon: location to query.
            radius_m: search radius in metres (default 200m).

        Returns:
            The TrafficCountPoint with the highest ``aadf`` within ``radius_m``,
            or ``None`` if no count points are nearby.
        """
        radius_km = radius_m / 1000.0
        hits = self._traffic_grid.query(lat, lon, radius_km)
        if not hits:
            return None
        return max(hits, key=lambda p: p.aadf)

    def population_density_at(self, lat: float, lon: float) -> float:
        """Return people-per-sq-km for the nearest LSOA, or 0.0 if unknown."""
        # Search outward: 0.5 km, then 1 km, then 2 km
        for radius in (0.5, 1.0, 2.0, 5.0):
            hits = self._lsoa_grid.query(lat, lon, radius)
            if hits:
                # Pick the nearest
                best_code = min(hits, key=lambda code: _haversine_km(
                    lat, lon,
                    *self._lsoa_centroids.get(code, (lat, lon))
                ))
                return self._lsoa_density.get(best_code, 0.0)
        return 0.0

    @property
    def school_count(self) -> int:
        return len(self._school_grid)

    @property
    def hospital_count(self) -> int:
        return len(self._hospital_grid)

    @property
    def care_home_count(self) -> int:
        return len(self._care_home_grid)

    @property
    def collision_count(self) -> int:
        return len(self._collision_grid)

    @property
    def traffic_count(self) -> int:
        return len(self._traffic_grid)

    @property
    def lsoa_count(self) -> int:
        return len(self._lsoa_density)

    # -- Private loading methods --------------------------------------------

    def _load_all(self) -> None:
        # Order matters: schools first (builds postcode lookup and LSOA centroids)
        self._lsoa_centroids: dict[str, tuple[float, float]] = {}
        self._load_schools()
        self._load_hospitals()
        self._load_care_homes()
        self._load_collisions()
        self._load_census()
        self._load_traffic()

        logger.info(
            "ProximityIndex loaded: %d schools, %d hospitals, %d care homes, "
            "%d collisions, %d LSOAs, %d traffic count points",
            self.school_count, self.hospital_count, self.care_home_count,
            self.collision_count, self.lsoa_count, self.traffic_count,
        )

    def _load_schools(self) -> None:
        path = self._data_dir / "schools" / "london_schools.csv"
        if not path.exists():
            logger.warning("Schools CSV not found: %s", path)
            return

        # Accumulators for postcode->coord and LSOA centroid lookup
        postcode_accum: dict[str, list[tuple[float, float]]] = defaultdict(list)
        lsoa_accum: dict[str, list[tuple[float, float]]] = defaultdict(list)

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

                    school = School(name=name, lat=lat, lon=lon, phase=phase)
                    self._school_grid.insert(school, lat, lon)

                    # Build postcode sector lookup
                    pc = row.get("Postcode", "").strip().upper()
                    if pc:
                        sector = _postcode_sector(pc)
                        if sector:
                            postcode_accum[sector].append((lat, lon))

                    # Build LSOA centroid lookup
                    lsoa_code = row.get("LSOA (code)", "").strip()
                    if lsoa_code:
                        lsoa_accum[lsoa_code].append((lat, lon))
        except Exception:
            logger.exception("Failed to load schools CSV")
            return

        # Compute average coordinates per postcode sector
        for sector, coords in postcode_accum.items():
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            self._postcode_coords[sector] = (avg_lat, avg_lon)

        # Compute LSOA centroids (average of school positions in each LSOA)
        for code, coords in lsoa_accum.items():
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            self._lsoa_centroids[code] = (avg_lat, avg_lon)

        logger.info("Loaded %d open schools, %d postcode sectors, %d LSOA centroids",
                     len(self._school_grid), len(self._postcode_coords), len(self._lsoa_centroids))

    def _load_hospitals(self) -> None:
        path = self._data_dir / "hospitals" / "nhs_trusts_sites.csv"
        if not path.exists():
            logger.warning("Hospitals CSV not found: %s", path)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 10:
                        continue
                    postcode = row[9].strip()
                    if not _is_inner_london_postcode(postcode):
                        continue
                    name = row[1].strip()

                    # Geocode via postcode sector from schools data
                    sector = _postcode_sector(postcode)
                    coords = self._postcode_coords.get(sector) if sector else None
                    if not coords:
                        continue

                    hospital = Hospital(name=name, lat=coords[0], lon=coords[1])
                    self._hospital_grid.insert(hospital, coords[0], coords[1])
        except Exception:
            logger.exception("Failed to load hospitals CSV")

    def _load_care_homes(self) -> None:
        path = self._data_dir / "care_homes" / "cqc_directory.csv"
        if not path.exists():
            logger.warning("Care homes CSV not found: %s", path)
            return

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
                    service_type = row.get("Service types", "")
                    postcode = row.get("Postcode", "").strip()

                    # Geocode via postcode sector
                    sector = _postcode_sector(postcode)
                    coords = self._postcode_coords.get(sector) if sector else None
                    if not coords:
                        continue

                    care_home = CareHome(
                        name=name, lat=coords[0], lon=coords[1],
                        service_type=service_type,
                    )
                    self._care_home_grid.insert(care_home, coords[0], coords[1])
        except Exception:
            logger.exception("Failed to load care homes CSV")

    def _load_collisions(self) -> None:
        path = self._data_dir / "stats19" / "collisions_2024.csv"
        if not path.exists():
            logger.warning("Collisions CSV not found: %s", path)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat = float(row.get("latitude", ""))
                        lon = float(row.get("longitude", ""))
                    except (ValueError, TypeError):
                        continue
                    # London bounding box
                    if not (51.2 <= lat <= 51.8 and -0.6 <= lon <= 0.4):
                        continue
                    try:
                        severity = int(row.get("collision_severity", "3"))
                    except ValueError:
                        severity = 3
                    date = row.get("date", "")

                    collision = Collision(lat=lat, lon=lon, severity=severity, date=date)
                    self._collision_grid.insert(collision, lat, lon)
        except Exception:
            logger.exception("Failed to load collisions CSV")

    def _load_traffic(self) -> None:
        """Load DfT AADF traffic count points for London."""
        path = self._data_dir / "traffic" / "london_aadf_2025.csv"
        if not path.exists():
            logger.warning("Traffic CSV not found: %s", path)
            return

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
                    # London bounding box sanity check
                    if not (51.2 <= lat <= 51.8 and -0.6 <= lon <= 0.4):
                        continue

                    try:
                        hgvs = int(row.get("all_hgvs", "0"))
                    except (ValueError, TypeError):
                        hgvs = 0

                    point = TrafficCountPoint(
                        lat=lat,
                        lon=lon,
                        aadf=aadf,
                        road_name=row.get("road_name", "").strip(),
                        road_category=row.get("road_type", "").strip(),
                        all_hgvs=hgvs,
                    )
                    self._traffic_grid.insert(point, lat, lon)
                    self.traffic_points.append(point)
        except Exception:
            logger.exception("Failed to load traffic CSV")

    def _load_census(self) -> None:
        path = self._data_dir / "census" / "london_lsoa_population_density.csv"
        if not path.exists():
            logger.warning("Census CSV not found: %s", path)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get("LSOA 2021 Code", "").strip()
                    if not code:
                        continue
                    try:
                        density = float(row.get("Mid-2024: People per Sq Km", "0"))
                    except (ValueError, TypeError):
                        density = 0.0
                    self._lsoa_density[code] = density

                    # Register in spatial grid if we have a centroid for this LSOA
                    centroid = self._lsoa_centroids.get(code)
                    if centroid:
                        self._lsoa_grid.insert(code, centroid[0], centroid[1])
        except Exception:
            logger.exception("Failed to load census CSV")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _postcode_sector(postcode: str) -> Optional[str]:
    """Extract postcode sector (e.g. 'SW1A 1' from 'SW1A 1AA').

    The sector is the outward code + first digit of inward code.
    """
    pc = postcode.strip().upper()
    if not pc:
        return None
    parts = pc.split()
    if len(parts) == 2 and len(parts[1]) >= 1:
        return parts[0] + " " + parts[1][0]
    # Attempt to split a spaceless postcode
    if len(pc) >= 5:
        return pc[:-2].rstrip() + " " + pc[-3]
    return None


def _collision_year(date_str: str) -> int:
    """Extract year from DD/MM/YYYY date string."""
    try:
        parts = date_str.split("/")
        return int(parts[2]) if len(parts) == 3 else 0
    except (IndexError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Singleton (lazy-loaded)
# ---------------------------------------------------------------------------

_instance: Optional[ProximityIndex] = None


def get_proximity_index() -> ProximityIndex:
    """Return a shared ProximityIndex instance (created on first call)."""
    global _instance
    if _instance is None:
        _instance = ProximityIndex()
    return _instance
