// Client for the Sorted FastAPI backend.
//
// The backend lives in /main.py (FastAPI) + /routers/reports.py + /services/vlm_service.py.
// It exposes POST /submit-report which:
//   - accepts multipart/form-data with `image`
//   - runs the photo through a local Ollama VLM (Nemotron-3 Nano Omni)
//   - returns priority_score + vlm_analysis (issue_type, severity 1-5, location, description)
//
// Configure the base URL by editing VLM_BASE_URL below. For DGX→phone access during
// the demo, Mohammad's runbook is `npx localtunnel --port 8000` → paste the URL here.
//
// If the URL is empty or the request fails, the app falls back to the mock
// classification flow so the demo still tells a story when the DGX is offline.

// ─── EDIT THIS LINE WHEN MOHAMMAD GIVES YOU THE TUNNEL URL ──────────────
export const VLM_BASE_URL = ''; // e.g. 'https://sorted-demo.loca.lt'
// ────────────────────────────────────────────────────────────────────────

const ENDPOINT_PATH = '/submit-report';
const TIMEOUT_MS = 30_000;

export type VLMAnalysis = {
  issue_type: string;
  severity: number;
  location: string;
  description: string;
};

export type VLMReport = {
  status: string;
  priority_score: number;
  details: {
    vlm_analysis: VLMAnalysis;
    enrichment: {
      tfl_delay_factor: number;
      population_density: number;
    };
  };
};

/**
 * Submit a captured photo to Mohammad's /submit-report endpoint.
 * Returns the parsed response, or null if disabled / failed / timed out.
 * Never throws — caller can always fall through to the mock flow.
 */
export async function submitPhotoForClassification(photoUri: string): Promise<VLMReport | null> {
  if (!VLM_BASE_URL) return null;

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const form = new FormData();
    // React Native's FormData accepts {uri, name, type} for files (any cast for type strictness).
    form.append('image', {
      uri: photoUri,
      name: 'photo.jpg',
      type: 'image/jpeg',
    } as unknown as Blob);

    const res = await fetch(`${VLM_BASE_URL}${ENDPOINT_PATH}`, {
      method: 'POST',
      body: form,
      // Don't set Content-Type — RN injects the multipart boundary itself.
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    if (!res.ok) return null;
    const data = (await res.json()) as VLMReport;
    if (!data?.details?.vlm_analysis) return null;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

// ── UI mapping helpers ────────────────────────────────────────────────
// Map the VLM's free-text issue_type to one of our internal CategoryIcon keys.
import type { SortedCategory } from './geolocate';

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
