"""
demo_seed.py — MARG-DRISHTI demo hotspot seeder

Called once from main.py's lifespan hook when the events table is empty.
Seeds 3 realistic hotspot areas (Mumbai HIGH, Pune LOW, Jaipur MEDIUM) by
inserting events through the same insert_event + process_event_hook pipeline
that the live phone POST /events endpoint uses.

IDEMPOTENCY GUARANTEE:
  seed_demo_hotspots() checks get_all_events() before doing anything.
  If any events already exist in SQLite it returns immediately without
  inserting a single row.  Safe to call on every server start.

IMPORTANT:
  - No fake hotspot objects are injected directly into the clusters/hotspots
    tables. Every demo hotspot is derived by the real risk engine from real
    event rows, exactly as live phone events are.
  - Coordinates are chosen so the 50 m clustering radius and 200 m hotspot
    radius never merge Mumbai / Pune / Jaipur events into one hotspot.
"""

import datetime
import logging
from typing import Dict, Any

from database import insert_event, get_all_events
import risk_engine

logger = logging.getLogger("demo_seed")


def _iso(dt: datetime.datetime) -> str:
    """Format a UTC datetime as an ISO 8601 string with milliseconds and Z."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _seed_event(payload: Dict[str, Any]) -> None:
    """Insert one event and run it through the risk engine — identical to POST /events."""
    stored = insert_event(payload)
    risk_engine.process_event_hook(stored)


def seed_demo_hotspots() -> None:
    """
    Insert demo events for three geographically separated hotspot areas.
    Does nothing if events table already contains rows.
    """
    if get_all_events():
        logger.info("[DemoSeed] Events already present — skipping demo seed.")
        return

    logger.info("[DemoSeed] Empty database detected — seeding demo hotspots …")

    # ── Reference timestamp: a realistic past window ────────────────────────
    # Using a fixed past time keeps the seeded data stable between restarts
    # (hotspot timestamps won't change unless the DB is reset).
    base = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=datetime.timezone.utc)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HOTSPOT 1 — MUMBAI (HIGH risk)
    # 5 independent vehicles within 50 m over a ~4 min window → single cluster
    # Coords: near the Western Express Highway, Andheri, Mumbai
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    mumbai_lat = 19.1196
    mumbai_lon = 72.8468
    mumbai_vehicles = [
        ("MH-V01", 0,   "HARD_BRAKING",         0.92, -5.1,  62.0,  180.0),
        ("MH-V02", 48,  "HARD_BRAKING",         0.89, -4.8,  58.0,  180.0),
        ("MH-V03", 105, "SUDDEN_DECELERATION",  0.87, -4.2,  55.0,  182.0),
        ("MH-V04", 172, "HARD_BRAKING",         0.91, -5.3,  60.0,  179.0),
        ("MH-V05", 230, "SUDDEN_DECELERATION",  0.88, -4.5,  57.0,  181.0),
    ]
    for vid, gap_s, etype, conf, acc, speed, hdg in mumbai_vehicles:
        # Small spatial offsets within 50 m radius (~0.00015° ≈ 17 m)
        lat_off = {"MH-V01": 0.0,       "MH-V02": 0.00012,  "MH-V03": -0.00011,
                   "MH-V04": 0.00008,   "MH-V05": -0.00013}.get(vid, 0.0)
        lon_off = {"MH-V01": 0.0,       "MH-V02": 0.00010,  "MH-V03": 0.00014,
                   "MH-V04": -0.00012,  "MH-V05": 0.00009}.get(vid, 0.0)
        _seed_event({
            "vehicle_id":   vid,
            "timestamp":    _iso(base + datetime.timedelta(seconds=gap_s)),
            "latitude":     round(mumbai_lat + lat_off, 6),
            "longitude":    round(mumbai_lon + lon_off, 6),
            "speed":        speed,
            "acceleration": acc,
            "heading":      hdg,
            "event_type":   etype,
            "confidence":   conf,
        })

    logger.info("[DemoSeed] Mumbai hotspot seeded (5 events, HIGH expected).")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HOTSPOT 2 — PUNE (LOW risk)
    # 1 vehicle, 2 events — minimal evidence, LOW risk expected
    # Coords: near the Pune-Mumbai Expressway (NH-48), Khopoli area exit
    # Distance from Mumbai centroid: ~120 km → guaranteed separate hotspot
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    pune_lat = 18.5074
    pune_lon = 73.8077
    pune_events = [
        ("PU-V01", 0,   "ROAD_ANOMALY",  0.71, -2.1, 72.0, 90.0),
        ("PU-V01", 30,  "ROAD_ANOMALY",  0.68, -1.9, 70.0, 90.0),
    ]
    for vid, gap_s, etype, conf, acc, speed, hdg in pune_events:
        lat_off = 0.0 if gap_s == 0 else 0.00004
        _seed_event({
            "vehicle_id":   vid,
            "timestamp":    _iso(base + datetime.timedelta(seconds=3600 + gap_s)),
            "latitude":     round(pune_lat + lat_off, 6),
            "longitude":    round(pune_lon, 6),
            "speed":        speed,
            "acceleration": acc,
            "heading":      hdg,
            "event_type":   etype,
            "confidence":   conf,
        })

    logger.info("[DemoSeed] Pune hotspot seeded (2 events, LOW expected).")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HOTSPOT 3 — JAIPUR (MEDIUM/LOW risk)
    # 3 independent vehicles within 50 m over ~3 min → MEDIUM expected
    # Coords: near NH-48 Jaipur bypass, Durgapura
    # Distance from Mumbai: ~1,140 km → guaranteed separate hotspot
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    jaipur_lat = 26.8523
    jaipur_lon = 75.7950
    jaipur_vehicles = [
        ("JP-V01", 0,   "TRAJECTORY_DEVIATION", 0.56, -3.2, 80.0, 270.0),
        ("JP-V02", 70,  "HARD_BRAKING",         0.54, -4.1, 75.0, 269.0),
        ("JP-V03", 155, "TRAJECTORY_DEVIATION", 0.52, -3.5, 78.0, 271.0),
    ]
    for vid, gap_s, etype, conf, acc, speed, hdg in jaipur_vehicles:
        lat_off = {"JP-V01": 0.0, "JP-V02": 0.00010, "JP-V03": -0.00009}.get(vid, 0.0)
        lon_off = {"JP-V01": 0.0, "JP-V02": 0.00008, "JP-V03": 0.00011}.get(vid, 0.0)
        _seed_event({
            "vehicle_id":   vid,
            "timestamp":    _iso(base + datetime.timedelta(seconds=7200 + gap_s)),
            "latitude":     round(jaipur_lat + lat_off, 6),
            "longitude":    round(jaipur_lon + lon_off, 6),
            "speed":        speed,
            "acceleration": acc,
            "heading":      hdg,
            "event_type":   etype,
            "confidence":   conf,
        })

    logger.info("[DemoSeed] Jaipur hotspot seeded (3 events, MEDIUM/LOW expected).")
    logger.info("[DemoSeed] Demo seed complete — 10 events inserted across 3 hotspot areas.")
