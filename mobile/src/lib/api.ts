// Client for the Sorted FastAPI backend on the DGX Spark.
//
// Backend lives in /main.py + /routers/reports.py + /services/vlm_service.py.
// Exposed via localtunnel at https://fixmy-council-seeit-sortit.loca.lt.
//
// Endpoint: POST /analyse-report (multipart/form-data)
//   image (required, binary)
//   text_description (optional, string) — pre-filled by STT on the phone, future hook
//
// Response: priority_score + priority_band + analysis{issue_type, severity 1-5,
// confidence 0-1, raw_label, description, location} + enrichment{borough,
// tfl_delay_factor, population_density}.
//
// Falls back to null (→ mock UI) on empty URL, network failure, or non-200.

// ─── Live tunnel URL (Mohammad's setup) ──────────────────────────────────
// To swap, just replace this string. Empty string disables the call.
export const VLM_BASE_URL = 'https://fixmy-council-seeit-sortit.loca.lt';
// ────────────────────────────────────────────────────────────────────────

const ENDPOINT_PATH = '/analyse-report';
const TIMEOUT_MS = 45_000;

export type VLMAnalysis = {
  issue_type: string;
  severity: number;        // 1-5
  location: string;
  description: string;
  confidence: number;      // 0-1
  raw_label: string;
};

export type VLMEnrichment = {
  tfl_delay_factor: number;
  population_density: number;
  borough?: string;
};

export type VLMReport = {
  status: string;
  priority_score: number;
  priority_band: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  analysis: VLMAnalysis;
  enrichment: VLMEnrichment;
};

export type ClassificationHints = {
  latitude?: number;
  longitude?: number;
  borough?: string;
  text_description?: string;
};

/**
 * Submit a captured photo to /analyse-report.
 * Returns parsed response or null (disabled / failure / timeout).
 * Never throws — caller falls through to mock UI.
 *
 * Hints (lat/lon/borough) are optional but strongly recommended — the model
 * uses them to ground its classification and the backend uses them for
 * borough-correct enrichment (TfL delay, density, scoring).
 */
export async function submitPhotoForClassification(
  photoUri: string,
  hints: ClassificationHints = {},
): Promise<VLMReport | null> {
  if (!VLM_BASE_URL) {
    console.log('[VLM] base URL empty — using mock fallback');
    return null;
  }
  console.log('[VLM] uri:', photoUri?.slice(0, 60), 'hints:', JSON.stringify(hints));

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const form = new FormData();
    form.append('image', {
      uri: photoUri,
      name: 'photo.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    if (hints.text_description) form.append('text_description', hints.text_description);
    if (hints.borough)          form.append('borough', hints.borough);
    if (hints.latitude  != null) form.append('latitude',  String(hints.latitude));
    if (hints.longitude != null) form.append('longitude', String(hints.longitude));

    const res = await fetch(`${VLM_BASE_URL}${ENDPOINT_PATH}`, {
      method: 'POST',
      body: form,
      // RN injects the multipart boundary itself; don't set Content-Type.
      // bypass-tunnel-reminder skips localtunnel's HTML warning page on the API path.
      headers: {
        Accept: 'application/json',
        'bypass-tunnel-reminder': '1',
      },
      signal: controller.signal,
    });
    console.log('[VLM] response status:', res.status);
    if (!res.ok) {
      const body = await res.text().catch(() => '<unreadable>');
      console.log('[VLM] non-200 body:', body.slice(0, 200));
      return null;
    }
    const data = (await res.json()) as VLMReport;
    if (!data?.analysis) {
      console.log('[VLM] missing analysis key in body');
      return null;
    }
    console.log('[VLM] OK — type:', data.analysis.issue_type, 'conf:', data.analysis.confidence, 'borough:', data.enrichment?.borough);
    return data;
  } catch (err) {
    console.log('[VLM] fetch error:', String(err).slice(0, 200));
    return null;
  } finally {
    clearTimeout(t);
  }
}

// ── UI mapping helpers ────────────────────────────────────────────────
import type { SortedCategory } from './geolocate';

/** Map the VLM's free-text issue_type to one of our CategoryIcon keys. */
export function mapIssueType(raw: string): { icon: SortedCategory; label: string } {
  const k = (raw || '').toLowerCase().replace(/[-\s]+/g, '_');
  if (k.includes('pothole')) return { icon: 'pothole', label: 'Pothole' };
  if (k.includes('graffiti')) return { icon: 'graffiti', label: 'Graffiti' };
  if (k.includes('streetlight') || k.includes('street_light') || k.includes('light')) {
    return { icon: 'streetlight', label: 'Streetlight out' };
  }
  if (k.includes('fly') || k.includes('tip') || k.includes('rubbish')) {
    return { icon: 'flytipping', label: 'Fly-tipping' };
  }
  if (k.includes('drain')) return { icon: 'drain', label: 'Blocked drain' };
  if (k.includes('tree')) return { icon: 'tree', label: 'Tree issue' };
  return { icon: 'other', label: raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) };
}

export function severityToBadge(s: number): { label: string; tone: 'high' | 'medium' | 'low' } {
  if (s >= 4) return { label: 'High', tone: 'high' };
  if (s >= 3) return { label: 'Medium', tone: 'medium' };
  return { label: 'Low', tone: 'low' };
}

/** Priority band → a stable color tone for the chip. */
export function bandTone(band: string): 'high' | 'medium' | 'low' {
  const up = (band || '').toUpperCase();
  if (up === 'CRITICAL' || up === 'HIGH') return 'high';
  if (up === 'MEDIUM') return 'medium';
  return 'low';
}
