"""
risk_engine.py  —  MARG-DRISHTI Road-Risk Intelligence

Two-level model:

  event  -->  temporal cluster  -->  logical spatial hotspot
              (≤50 m, ≤5 min,        (≤200 m across any time)
               ≤30° heading)

Responsibilities (called on every POST /events via process_event_hook):
  1. CLUSTERING      — spatial + temporal + heading proximity
  2. HOTSPOT LINKAGE — find-or-create the logical hotspot for this cluster
  3. CHAIN DETECTION — consecutive inter-vehicle timing analysis (per cluster)
  4. RISK SCORING    — anomaly-relative score aggregated across all clusters
                       belonging to the same logical hotspot

Prototype anomaly score relative to baseline traffic behavior,
not a calibrated probability.
"""

import math
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import database

logger = logging.getLogger("risk_engine")

# ─── Constants ────────────────────────────────────────────────────────────────
CLUSTER_RADIUS_M     = 50.0    # merge into same temporal cluster if within this distance
CLUSTER_TIME_MAX_S   = 300.0   # and within this time window (5 min)
CLUSTER_HEADING_DEG  = 30.0    # and heading within this deviation

HOTSPOT_RADIUS_M     = 200.0   # link clusters to the same logical hotspot if within this distance

CHAIN_DELAY_DIST_M   = 20.0    # assumed following distance for chain timing (metres)
CHAIN_TOLERANCE_S    = 1.5     # ± tolerance on expected inter-vehicle gap (seconds)
CHAIN_MATCH_RATIO    = 0.5     # fraction of consecutive pairs that must match for chain verdict
CHAIN_WEIGHT         = 0.3     # weight applied to chain vehicles for scoring (vs 1.0)

GAP_INDEPENDENT_S    = 600.0   # ≥10 min → independent recurrence (NOT chain)

BASELINE_MIN_CLUSTERS = 5      # use hardcoded baseline if fewer clusters exist globally
BASELINE_HARDCODED    = 3.0    # events-per-cluster baseline when data is sparse

# ─── Geometry helpers ─────────────────────────────────────────────────────────

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in metres between two WGS-84 coordinates."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def _heading_diff(h1: float, h2: float) -> float:
    """Absolute angular difference between two headings (0-360), wrapped to ≤180°."""
    diff = abs(h1 - h2) % 360
    return diff if diff <= 180 else 360 - diff

def _parse_ts(ts: str) -> datetime:
    """Parse an ISO 8601 string to a timezone-aware datetime (UTC)."""
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

# ─── Chain Detection (per temporal cluster) ───────────────────────────────────

def _detect_chain(cluster_events: List[Dict[str, Any]]) -> bool:
    """
    Sort events by timestamp and check whether consecutive events show the
    timing signature of a stop-wave / chain-reaction:
        expected_gap = CHAIN_DELAY_DIST_M / speed_ms
        actual_gap   = seconds between consecutive timestamps
        match        = |actual_gap - expected_gap| <= CHAIN_TOLERANCE_S

    Returns True if >= CHAIN_MATCH_RATIO of consecutive pairs match AND
    no pair has a gap >= GAP_INDEPENDENT_S (which would indicate
    independent separate incidents, not a chain).
    """
    if len(cluster_events) < 2:
        return False

    sorted_evs = sorted(cluster_events, key=lambda e: _parse_ts(e["timestamp"]))
    matches = 0
    total_pairs = len(sorted_evs) - 1

    for i in range(total_pairs):
        ev_a = sorted_evs[i]
        ev_b = sorted_evs[i + 1]
        actual_gap = (_parse_ts(ev_b["timestamp"]) - _parse_ts(ev_a["timestamp"])).total_seconds()

        # A large gap means independent incidents — not a chain
        if actual_gap >= GAP_INDEPENDENT_S:
            return False

        speed_kmh = ev_a["speed"]
        if speed_kmh <= 0:
            continue
        speed_ms = speed_kmh / 3.6
        expected_gap = CHAIN_DELAY_DIST_M / speed_ms

        if abs(actual_gap - expected_gap) <= CHAIN_TOLERANCE_S:
            matches += 1

    return (matches / total_pairs) >= CHAIN_MATCH_RATIO

# ─── Hotspot-level Scoring ────────────────────────────────────────────────────

def _score_hotspot(
    member_clusters: List[Dict[str, Any]],
) -> int:
    """
    Aggregate risk score for a logical hotspot across all its temporal clusters.

    prototype anomaly score relative to baseline traffic behavior,
    not a calibrated probability.

    Algorithm:
      For each member cluster:
        - Fetch its events.
        - Detect chain independently.
        - Assign per-vehicle weights: 0.3 if chain cluster, else 1.0.
      Across all clusters, a vehicle keeps its MAXIMUM weight
      (appearing later in an independent cluster restores it to 1.0).
      Baseline = avg events-per-cluster across all clusters globally
                 (hardcoded at 3.0 when fewer than 5 clusters exist).
      risk_score = clamp(100 * weighted_unique_vehicles / baseline
                         * mean_confidence_all_events, 0, 100)
    """
    all_clusters = database.get_all_clusters()
    if len(all_clusters) >= BASELINE_MIN_CLUSTERS:
        total_ev = sum(
            len(c["event_ids"].split(",")) if c["event_ids"] else 0
            for c in all_clusters
        )
        baseline = total_ev / len(all_clusters)
    else:
        baseline = BASELINE_HARDCODED

    vehicle_weights: Dict[str, float] = {}   # vehicle_id -> max weight seen
    all_events: List[Dict[str, Any]] = []

    for cluster in member_clusters:
        ids = [int(x) for x in cluster["event_ids"].split(",") if x]
        if not ids:
            continue
        evs = database.get_events_by_ids(ids)
        if not evs:
            continue
        all_events.extend(evs)

        is_chain = _detect_chain(evs)

        # Identify vehicles discounted by chain detection within this cluster
        if is_chain and len(evs) >= 2:
            sorted_evs = sorted(evs, key=lambda e: _parse_ts(e["timestamp"]))
            chain_vids = set()
            for i in range(len(sorted_evs) - 1):
                chain_vids.add(sorted_evs[i]["vehicle_id"])
                chain_vids.add(sorted_evs[i + 1]["vehicle_id"])
        else:
            chain_vids = set()

        for ev in evs:
            vid = ev["vehicle_id"]
            w = CHAIN_WEIGHT if vid in chain_vids else 1.0
            # Independent cluster: vehicle gets max(existing, 1.0) — strengthens score
            vehicle_weights[vid] = max(vehicle_weights.get(vid, 0.0), w)

    if not all_events:
        return 0

    weighted_unique = sum(vehicle_weights.values())
    mean_conf = sum(e["confidence"] for e in all_events) / len(all_events)

    raw = 100.0 * (weighted_unique / baseline) * mean_conf
    return max(0, min(100, round(raw)))

def _score_to_status(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"

# ─── Temporal Clustering ──────────────────────────────────────────────────────

def _find_matching_cluster(
    event: Dict[str, Any],
    clusters: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Return the first existing temporal cluster that satisfies all three merge criteria:
      - haversine distance to centroid < CLUSTER_RADIUS_M (50 m)
      - |event.timestamp - cluster.last_timestamp| < CLUSTER_TIME_MAX_S (5 min)
      - heading deviation from cluster average < CLUSTER_HEADING_DEG (30°)
    Returns None if no match found (new cluster needed).
    """
    ev_lat  = event["latitude"]
    ev_lon  = event["longitude"]
    ev_head = event["heading"]
    ev_ts   = _parse_ts(event["timestamp"])

    for c in clusters:
        if _haversine_m(ev_lat, ev_lon, c["centroid_lat"], c["centroid_lon"]) >= CLUSTER_RADIUS_M:
            continue
        time_diff = abs((ev_ts - _parse_ts(c["last_timestamp"])).total_seconds())
        if time_diff >= CLUSTER_TIME_MAX_S:
            continue
        if _heading_diff(ev_head, c["avg_heading"]) >= CLUSTER_HEADING_DEG:
            continue
        return c  # all criteria met

    return None

def _update_centroid(old_lat: float, old_lon: float, old_n: int,
                     new_lat: float, new_lon: float) -> tuple[float, float]:
    """Running average centroid after adding one new point."""
    n = old_n + 1
    return (old_lat * old_n + new_lat) / n, (old_lon * old_n + new_lon) / n

def _update_heading(old_avg: float, old_n: int, new_heading: float) -> float:
    """Running average heading (simple arithmetic mean — fine for ≤30° spread)."""
    return (old_avg * old_n + new_heading) / (old_n + 1)

# ─── Logical Hotspot Linkage ──────────────────────────────────────────────────

def _find_or_create_hotspot(cluster: Dict[str, Any]) -> str:
    """
    Find a logical hotspot within HOTSPOT_RADIUS_M of the cluster centroid,
    or create a new one.  Updates the hotspot centroid as a running average
    and increments cluster_count.  Returns the hotspot_id.
    """
    existing = database.find_hotspot_near(
        cluster["centroid_lat"], cluster["centroid_lon"], HOTSPOT_RADIUS_M
    )

    if existing:
        # Update hotspot centroid as running average of cluster centroids
        n = existing["cluster_count"]
        new_lat = (existing["centroid_lat"] * n + cluster["centroid_lat"]) / (n + 1)
        new_lon = (existing["centroid_lon"] * n + cluster["centroid_lon"]) / (n + 1)
        hotspot = {
            "id":            existing["id"],
            "centroid_lat":  new_lat,
            "centroid_lon":  new_lon,
            "cluster_count": n + 1,
        }
    else:
        hotspot = {
            "id":            str(uuid.uuid4()),
            "centroid_lat":  cluster["centroid_lat"],
            "centroid_lon":  cluster["centroid_lon"],
            "cluster_count": 1,
        }

    database.save_hotspot(hotspot)
    return hotspot["id"]

# ─── Public hook ──────────────────────────────────────────────────────────────

def process_event_hook(event_data: Dict[str, Any]) -> None:
    """
    Called by main.py after every successful event insert.
    Runs temporal clustering, hotspot linkage, chain detection, and scoring.
    """
    try:
        clusters = database.get_all_clusters()
        match    = _find_matching_cluster(event_data, clusters)

        event_id = event_data["id"]
        ev_ts    = event_data["timestamp"]

        if match:
            # ── Merge into existing temporal cluster ─────────────────────
            ids_str = match["event_ids"]
            existing_ids = [int(x) for x in ids_str.split(",") if x]
            existing_ids.append(event_id)
            n_old = len(existing_ids) - 1

            new_lat, new_lon = _update_centroid(
                match["centroid_lat"], match["centroid_lon"], n_old,
                event_data["latitude"], event_data["longitude"]
            )
            new_heading = _update_heading(match["avg_heading"], n_old, event_data["heading"])
            last_ts  = ev_ts if _parse_ts(ev_ts) > _parse_ts(match["last_timestamp"]) else match["last_timestamp"]
            first_ts = match["first_timestamp"]

            cluster = {
                "id":             match["id"],
                "hotspot_id":     match.get("hotspot_id"),  # preserve existing linkage
                "centroid_lat":   new_lat,
                "centroid_lon":   new_lon,
                "avg_heading":    new_heading,
                "last_timestamp": last_ts,
                "first_timestamp": first_ts,
                "event_ids":      ",".join(str(i) for i in existing_ids),
                "possible_chain": False,
                "risk_score":     0,
                "status":         "LOW",
            }
        else:
            # ── Create new temporal cluster ──────────────────────────────
            cluster = {
                "id":             str(uuid.uuid4()),
                "hotspot_id":     None,   # will be assigned below
                "centroid_lat":   event_data["latitude"],
                "centroid_lon":   event_data["longitude"],
                "avg_heading":    event_data["heading"],
                "last_timestamp": ev_ts,
                "first_timestamp": ev_ts,
                "event_ids":      str(event_id),
                "possible_chain": False,
                "risk_score":     0,
                "status":         "LOW",
            }

        # ── Ensure this cluster is linked to a logical hotspot ────────────
        # Only create/update hotspot linkage when this is a brand-new cluster
        # (a merge keeps its existing hotspot_id).
        if not cluster.get("hotspot_id"):
            cluster["hotspot_id"] = _find_or_create_hotspot(cluster)

        # ── Persist cluster first so events are queryable ─────────────────
        # Compute chain + score for THIS cluster only
        ids = [int(x) for x in cluster["event_ids"].split(",") if x]
        cluster_events = database.get_events_by_ids(ids)
        is_chain = _detect_chain(cluster_events)
        cluster["possible_chain"] = is_chain
        cluster["risk_score"]     = 0    # hotspot-level score computed below
        cluster["status"]         = "LOW"
        database.save_cluster(cluster)

        # ── Recompute hotspot-level risk score ────────────────────────────
        # Aggregate across ALL clusters belonging to this logical hotspot.
        member_clusters = database.get_clusters_for_hotspot(cluster["hotspot_id"])
        hotspot_score   = _score_hotspot(member_clusters)
        hotspot_status  = _score_to_status(hotspot_score)

        # Write the score back to the cluster so per-cluster queries still work
        cluster["risk_score"] = hotspot_score
        cluster["status"]     = hotspot_status
        database.save_cluster(cluster)

        logger.info(
            f"[RiskEngine] Cluster {cluster['id'][:8]}... -> "
            f"Hotspot {cluster['hotspot_id'][:8]}... | "
            f"events={len(ids)} chain={is_chain} "
            f"hotspot_score={hotspot_score} status={hotspot_status}"
        )

    except Exception as exc:
        logger.error(f"[RiskEngine] process_event_hook failed: {exc}", exc_info=True)

# ─── GET /hotspots response builder ───────────────────────────────────────────

def get_hotspots() -> List[Dict[str, Any]]:
    """
    Build the Hotspot response array from logical hotspot records.
    Each logical hotspot aggregates events from all its temporal clusters.
    Called by GET /hotspots in main.py.
    """
    hotspots_db = database.get_all_hotspots()
    result = []

    for h in hotspots_db:
        member_clusters = database.get_clusters_for_hotspot(h["id"])
        if not member_clusters:
            continue

        # Collect all event ids across all member clusters
        all_event_ids: List[int] = []
        for c in member_clusters:
            all_event_ids.extend(int(x) for x in c["event_ids"].split(",") if x)

        if not all_event_ids:
            continue

        all_events = database.get_events_by_ids(all_event_ids)
        if not all_events:
            continue

        # Aggregate fields
        unique_vehicles = len({e["vehicle_id"] for e in all_events})
        breakdown: Dict[str, int] = {}
        for ev in all_events:
            breakdown[ev["event_type"]] = breakdown.get(ev["event_type"], 0) + 1

        # Chain: true if ANY member cluster detected a chain
        any_chain = any(bool(c["possible_chain"]) for c in member_clusters)

        # Timestamps: earliest first_timestamp, latest last_timestamp across clusters
        first_detected = min(c["first_timestamp"] for c in member_clusters)
        last_observed  = max(c["last_timestamp"]  for c in member_clusters)

        # Score: re-compute at hotspot level (uses the same logic as during ingestion)
        hotspot_score  = _score_hotspot(member_clusters)
        hotspot_status = _score_to_status(hotspot_score)

        result.append({
            "hotspot_id":      h["id"],
            "latitude":        h["centroid_lat"],
            "longitude":       h["centroid_lon"],
            "risk_score":      hotspot_score,
            "status":          hotspot_status,
            "unique_vehicles": unique_vehicles,
            "total_events":    len(all_events),
            "event_breakdown": breakdown,
            "possible_chain":  any_chain,
            "first_detected":  first_detected,
            "last_observed":   last_observed,
        })

    result.sort(key=lambda h: h["risk_score"], reverse=True)
    return result
