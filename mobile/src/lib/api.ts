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

/**
 * Submit a captured photo to /analyse-report.
 * Returns parsed response or null (disabled / failure / timeout).
 * Never throws — caller falls through to mock UI.
 */
export async function submitPhotoForClassification(
  photoUri: string,
  textDescription?: string,
): Promise<VLMReport | null> {
  if (!VLM_BASE_URL) return null;

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const form = new FormData();
    form.append('image', {
      uri: photoUri,
      name: 'photo.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);
    if (textDescription) {
      form.append('text_description', textDescription);
    }

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
    if (!res.ok) return null;
    const data = (await res.json()) as VLMReport;
    if (!data?.analysis) return null;
    return data;
  } catch {
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
