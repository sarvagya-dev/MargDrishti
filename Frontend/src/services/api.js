// ─── Mock data imports (cases + charts remain frontend-only) ───────────────────
// Imports must appear at the top of an ES module, before any other statements.
import { cases as mockCases, chartData as mockChartData } from "@/mock/data";

// ─── Backend base URL ──────────────────────────────────────────────────────────
// Single configurable constant — change this one value to target a different
// environment (staging, production, etc.). Never spread raw host strings
// throughout the codebase.
export const API_BASE_URL = "http://localhost:8000";

// ─── Utility: haversine distance in metres ─────────────────────────────────────
// Used to associate /events rows with a hotspot centroid because the backend
// does not expose which event IDs belong to which hotspot in the public API.
function haversineMetres(lat1, lon1, lat2, lon2) {
  const R = 6_371_000;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// ─── Utility: ISO 8601 → HH:MM ────────────────────────────────────────────────
// The existing ClusterInvestigation timeline expects a short "HH:MM" string.
// The backend stores full ISO 8601 timestamps.
function toHHMM(isoString) {
  if (!isoString) return "—";
  try {
    // Slice characters 11-16 of the ISO string ("2024-01-15T14:12:33" → "14:12")
    const slice = String(isoString).slice(11, 16);
    return slice.length === 5 ? slice : isoString;
  } catch {
    return String(isoString);
  }
}

// ─── Demo location lookup ──────────────────────────────────────────────────────
// Maps known seed hotspot coordinates to human-readable display names.
// Matching is proximity-based (< DEMO_MATCH_RADIUS_M) so it works even if
// the backend centroid drifts slightly as more cluster centroids are averaged in.
// For any hotspot that does NOT match a known demo location (e.g. a real
// phone event at a new geographic location) the generic fallback is used.
const DEMO_LOCATIONS = [
  {
    lat: 19.1196, lon: 72.8468,
    road_segment: "Mumbai Risk Cluster",
    location:     "Mumbai, Maharashtra",
    direction:    "Westbound",
  },
  {
    lat: 18.5074, lon: 73.8077,
    road_segment: "Pune Risk Cluster",
    location:     "Pune, Maharashtra",
    direction:    "Eastbound",
  },
  {
    lat: 26.8523, lon: 75.7950,
    road_segment: "Jaipur Risk Cluster",
    location:     "Jaipur, Rajasthan",
    direction:    "Westbound",
  },
];

// 5 km — wide enough to tolerate centroid drift, tight enough to avoid
// accidentally matching a different city's hotspot.
const DEMO_MATCH_RADIUS_M = 5_000;

function resolveDemoLocation(lat, lon) {
  for (const demo of DEMO_LOCATIONS) {
    if (haversineMetres(lat, lon, demo.lat, demo.lon) <= DEMO_MATCH_RADIUS_M) {
      return demo;
    }
  }
  return null; // unknown location — use generic fallback
}

// ─── Schema transform: backend HotspotResponse → frontend hotspot shape ────────
//
// The backend and frontend use different field names and types.
// ALL translation happens here so no component needs to change field names.
//
// Backend field        → Frontend field       Notes
// ──────────────────────────────────────────────────────────────
// hotspot_id           → id                  renamed
// status               → risk_level          renamed; same values LOW/MEDIUM/HIGH
// unique_vehicles      → vehicle_count       renamed
// total_events         → event_count         renamed
// first_detected       → first_observed      renamed
// last_observed        → last_observed       unchanged
// event_breakdown{}    → event_types[]       Dict keys → string array
// latitude, longitude  → latitude, longitude unchanged
// risk_score           → risk_score          unchanged
// possible_chain       → possible_chain      unchanged
// (absent)             → road_segment        DEMO lookup → "Road Risk Cluster" fallback
// (absent)             → location            DEMO lookup → decimal coordinates fallback
// (absent)             → direction           DEMO lookup → "—" fallback
// (absent)             → confidence          derived later from event rows
function transformHotspot(h) {
  const demo = resolveDemoLocation(h.latitude, h.longitude);
  const coordLabel = `${h.latitude.toFixed(4)}°N, ${h.longitude.toFixed(4)}°E`;

  return {
    // ── Renamed fields ──────────────────────────────────────────────────────
    id: h.hotspot_id,
    risk_level: h.status,               // "LOW" | "MEDIUM" | "HIGH"
    vehicle_count: h.unique_vehicles,
    event_count: h.total_events,
    first_observed: h.first_detected,
    last_observed: h.last_observed,
    // ── Pass-through fields ─────────────────────────────────────────────────
    latitude: h.latitude,
    longitude: h.longitude,
    risk_score: h.risk_score,
    possible_chain: h.possible_chain,
    // ── Type conversion: Dict[str,int] → string[] ───────────────────────────
    event_types: Object.keys(h.event_breakdown ?? {}),
    // ── Display fields: resolved from known demo locations, or factual fallback
    // road_segment: human-readable cluster name (e.g. "Mumbai Risk Cluster") or
    //               generic "Road Risk Cluster" for unrecognised phone events.
    // location: city + state for demo seeds; raw coordinates for unknown spots.
    // direction: cardinal direction for demo seeds; "—" for unknown spots.
    road_segment: demo?.road_segment ?? "Road Risk Cluster",
    location:     demo?.location     ?? coordLabel,
    direction:    demo?.direction    ?? "—",
    // confidence is derived from real event rows in getHotspotDetails;
    // left null here so the overview does not fabricate a per-hotspot value.
    confidence: null,
  };
}

// ─── Schema transform: backend EventResponse row → frontend vehicle shape ───────
//
// The existing Contributing Vehicles panel expects:
//   { id, event_type, timestamp }    — timeline + vehicle list
//
// We enrich with all real backend fields so the evidence modal and any future
// panels have access to them without requiring additional fetches.
//
// Evidence items get their URL prefixed with API_BASE_URL so the browser
// can stream the video directly from the backend.
function transformEventToVehicle(ev) {
  return {
    // ── Shape the existing UI reads ─────────────────────────────────────────
    id: ev.vehicle_id,
    event_type: ev.event_type,
    timestamp: toHHMM(ev.timestamp),    // "HH:MM" for timeline positioning
    // ── Extended real backend fields (evidence panel, export) ───────────────
    event_id: ev.id,
    latitude: ev.latitude,
    longitude: ev.longitude,
    speed: ev.speed,
    acceleration: ev.acceleration,
    heading: ev.heading,
    confidence: ev.confidence,
    full_timestamp: ev.timestamp,
    created_at: ev.created_at,
    // ── Evidence: absolute playback URLs ────────────────────────────────────
    // Backend returns relative path  "/evidence/{id}".
    // We prefix with API_BASE_URL so the <video> element can stream it.
    evidence: (ev.evidence ?? []).map((e) => ({
      id: e.id,
      event_id: e.event_id,
      content_type: e.content_type,
      filename: e.filename,
      created_at: e.created_at,
      url: `${API_BASE_URL}${e.url}`,   // e.g. "http://localhost:8000/evidence/2"
    })),
  };
}

// ─── Core HTTP helper ───────────────────────────────────────────────────────────
// Single point for all fetch calls. Throws a descriptive Error on network
// failure or non-2xx status so callers (and useQuery) surface it cleanly.
async function apiFetch(path) {
  const url = `${API_BASE_URL}${path}`;
  let res;
  try {
    res = await fetch(url, { mode: "cors" });
  } catch (networkErr) {
    throw new Error(
      `Cannot reach backend at ${url}. Is the FastAPI server running? (${networkErr.message})`,
    );
  }
  if (!res.ok) {
    throw new Error(`Backend error: ${path} → HTTP ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ─── Live API calls ─────────────────────────────────────────────────────────────

/**
 * GET /hotspots
 * Returns a Promise that resolves to the transformed hotspot array.
 * Callers should use useQuery (TanStack Query) or equivalent async handling.
 */
export async function getHotspots() {
  const data = await apiFetch("/hotspots");
  return data.map(transformHotspot);
}

// Radius used to associate /events rows with a hotspot centroid.
// Slightly wider than the backend's 200 m hotspot radius to account for
// centroid drift across multiple temporal clusters.
const HOTSPOT_EVENT_RADIUS_M = 250;

/**
 * GET /hotspots + GET /events + GET /events/{id}
 *
 * Fetches full hotspot details including contributing events and their evidence.
 *
 * Strategy (no backend endpoint maps hotspot → events directly):
 *   1. GET /hotspots — locate the hotspot by hotspot_id
 *   2. GET /events   — retrieve all stored event rows
 *   3. Filter events within HOTSPOT_EVENT_RADIUS_M of the hotspot centroid
 *   4. GET /events/{id} for each nearby event to include evidence records
 *
 * Returns a Promise<Object|null>.
 */
export async function getHotspotDetails(id) {
  // 1. Locate the raw hotspot (before transform so we have hotspot_id)
  const allRaw = await apiFetch("/hotspots");
  const rawHotspot = allRaw.find((h) => h.hotspot_id === id);
  if (!rawHotspot) return null;

  const hotspot = transformHotspot(rawHotspot);

  // 2. All stored events
  const allEvents = await apiFetch("/events");

  // 3. Filter to events near this hotspot's centroid
  const nearbyEvents = allEvents.filter((ev) => {
    const dist = haversineMetres(
      hotspot.latitude,
      hotspot.longitude,
      ev.latitude,
      ev.longitude,
    );
    return dist <= HOTSPOT_EVENT_RADIUS_M;
  });

  // 4. Re-fetch each nearby event individually to obtain linked evidence records.
  //    Falls back to the /events row (no evidence) if the individual fetch fails.
  const eventsWithEvidence = await Promise.all(
    nearbyEvents.map(async (ev) => {
      try {
        return await apiFetch(`/events/${ev.id}`);
      } catch {
        return { ...ev, evidence: [] };
      }
    }),
  );

  // Derive mean confidence from real event data; this is the only defensible
  // source of a "cluster confidence" figure without a dedicated backend field.
  const meanConfidence =
    eventsWithEvidence.length > 0
      ? eventsWithEvidence.reduce((sum, e) => sum + (e.confidence ?? 0), 0) /
        eventsWithEvidence.length
      : null;

  hotspot.confidence = meanConfidence;

  const vehicles = eventsWithEvidence.map(transformEventToVehicle);

  return { ...hotspot, vehicles };
}

/**
 * GET /events/{eventId}
 * Fetches a single event with all linked evidence records.
 * Used when the user clicks "View Evidence" in ClusterInvestigation.
 */
export async function getEventWithEvidence(eventId) {
  const ev = await apiFetch(`/events/${eventId}`);
  return transformEventToVehicle(ev);
}

// ─── Cases (frontend-only — no backend /cases endpoint) ────────────────────────
// Cases are managed entirely in-browser. The mock array in data.js acts as the
// in-session store. They are NOT persisted to the FastAPI backend.

export function getCases() {
  return mockCases;
}

export function createCase(hotspotId) {
  // road_segment and location cannot be synchronously derived from the backend
  // here (getHotspots is async). Use explicit "—" so the Cases table renders
  // without fabricated metadata.
  const newCase = {
    id: `CA-${String(mockCases.length + 1).padStart(3, "0")}`,
    hotspot_id: hotspotId,
    road_segment: "—",
    location: "—",
    risk_level: "LOW",            // default; updated if caller passes context
    status: "NEW",
    assigned_to: "Unassigned",
    created_at: new Date().toISOString(),
  };
  mockCases.push(newCase);
  return newCase;
}

export function updateCaseStatus(caseId, status) {
  const found = mockCases.find((c) => c.id === caseId);
  if (!found) return null;
  found.status = status;
  return found;
}

// ─── Chart data (no backend aggregation endpoint) ──────────────────────────────
// The existing recharts panels are preserved with the static demo series
// from mock/data.js until a backend aggregation endpoint is available.
// This is intentionally static demo data — not fabricated backend statistics.
export function getChartData() {
  return mockChartData;
}

// ─── Driver alert (in-memory, frontend-only) ────────────────────────────────────
let driverAlertState = "CLEAR";

export function getDriverAlert() {
  return { state: driverAlertState };
}

export function triggerDriverAlert(hotspotId) {
  driverAlertState = "HIGH_RISK";
  return { state: driverAlertState, hotspot_id: hotspotId };
}
