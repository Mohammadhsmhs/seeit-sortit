// London borough lookup from lat/lon.
//
//   findBoroughForLocation(lat, lon) → { borough, distance_km, source }
//
// Uses point-in-polygon over a simplified ONS LAD13 polygon set for the 33
// London boroughs (~119 KB GeoJSON shipped in the bundle). Falls back to the
// nearest borough centroid when a point is outside all polygons (boats on the
// Thames, points just past the M25, GPS drift) so we always have *something*
// to route to.

import boroughGeo from '../data/london_boroughs.json';
import { BOROUGH_BY_NAME, BoroughMeta } from '../data/boroughs';

type Ring = [number, number][];
type Poly = Ring[]; // [outer, ...holes]
type Feature = {
  type: 'Feature';
  properties: { name: string; code: string; bbox: [number, number, number, number] };
  geometry:
    | { type: 'Polygon'; coordinates: Poly }
    | { type: 'MultiPolygon'; coordinates: Poly[] };
};

const FEATURES = (boroughGeo as unknown as { features: Feature[] }).features;

function pointInRing(lon: number, lat: number, ring: Ring): boolean {
  // Ray casting, GeoJSON convention: [lon, lat]
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersect =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi + 1e-12) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function pointInPolygon(lon: number, lat: number, poly: Poly): boolean {
  if (!pointInRing(lon, lat, poly[0])) return false;
  for (let h = 1; h < poly.length; h++) {
    if (pointInRing(lon, lat, poly[h])) return false; // inside a hole → not in poly
  }
  return true;
}

function bboxHit(lon: number, lat: number, [minX, minY, maxX, maxY]: [number, number, number, number]): boolean {
  return lon >= minX && lon <= maxX && lat >= minY && lat <= maxY;
}

function distanceKm(aLat: number, aLon: number, bLat: number, bLon: number): number {
  // Haversine — small enough error inside London for our purposes
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(bLat - aLat);
  const dLon = toRad(bLon - aLon);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export type BoroughHit = {
  borough: BoroughMeta;
  source: 'polygon' | 'nearest_centroid';
  distance_km: number; // 0 if inside polygon
};

export function findBoroughForLocation(lat: number, lon: number): BoroughHit | null {
  // Fast path: point-in-polygon with bbox prefilter
  for (const f of FEATURES) {
    if (!bboxHit(lon, lat, f.properties.bbox)) continue;
    const polys: Poly[] =
      f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates];
    for (const poly of polys) {
      if (pointInPolygon(lon, lat, poly)) {
        const meta = BOROUGH_BY_NAME[f.properties.name];
        if (!meta) continue; // metadata missing for this name — fall through
        return { borough: meta, source: 'polygon', distance_km: 0 };
      }
    }
  }

  // Fallback: nearest borough centroid
  let best: { meta: BoroughMeta; dist: number } | null = null;
  for (const meta of Object.values(BOROUGH_BY_NAME)) {
    const d = distanceKm(lat, lon, meta.center.lat, meta.center.lon);
    if (!best || d < best.dist) best = { meta, dist: d };
  }
  if (!best) return null;
  return { borough: best.meta, source: 'nearest_centroid', distance_km: best.dist };
}

// Map a Sorted-internal category to the council department label string.
// Returns the human-readable department from the council's own taxonomy.
export type SortedCategory =
  | 'pothole'
  | 'flytipping'
  | 'streetlight'
  | 'graffiti'
  | 'drain'
  | 'tree'
  | 'parking'
  | 'other';

const CATEGORY_TO_DEPT: Record<SortedCategory, keyof BoroughMeta['departments']> = {
  pothole: 'roads_and_highways',
  flytipping: 'waste_and_fly_tipping',
  streetlight: 'street_lighting',
  graffiti: 'street_cleanliness',
  drain: 'roads_and_highways',
  tree: 'parks_and_public_spaces',
  parking: 'parking',
  other: 'street_cleanliness',
};

export function getDepartmentForCategory(meta: BoroughMeta, cat: SortedCategory): string {
  const key = CATEGORY_TO_DEPT[cat];
  return meta.departments[key];
}
