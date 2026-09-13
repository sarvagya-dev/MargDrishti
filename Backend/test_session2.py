"""
test_session2.py  —  MARG-DRISHTI Session 2 verification

Scenario A: CHAIN burst
  4 vehicles at the same spot on NH-48, Pune (within 50m of each other),
  timestamps ~1.4s apart (expected gap for 50 km/h = 20m / 13.9 m/s ≈ 1.44s).
  -> Should form ONE cluster with possible_chain=true and discounted scoring.

Scenario B: NON-CHAIN / independent recurrence
  3 vehicles at a different spot, 15 minutes apart each.
  -> Should form ONE cluster with possible_chain=false, full-weight scoring.
"""

import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"

def post(payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/events",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(path: str) -> object:
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

# ── SCENARIO A: chain-like burst on NH-48, Pune ──────────────────────────────
# speed 50 km/h ≈ 13.89 m/s  -> expected gap = 20 / 13.89 ≈ 1.44 s
# We space timestamps exactly 1.44 s apart — well within ±1.5 s tolerance
print("\n=== SCENARIO A — Chain burst (4 vehicles, 1.44s gaps) ===")
chain_base = "2026-09-06T15:00:00Z"
chain_events = [
    {"vehicle_id": f"CHAIN-V{i+1}", "timestamp": f"2026-09-06T15:00:0{round(i*1.44):01d}Z",
     "latitude": 18.5200, "longitude": 73.8560,
     "speed": 50.0, "acceleration": -5.0,
     "heading": 90.0, "event_type": "HARD_BRAKING", "confidence": 0.92}
    for i in range(4)
]
# Fix timestamps manually for precision
chain_ts = [
    "2026-09-06T15:00:00Z",
    "2026-09-06T15:00:01Z",   # 1.0s gap  — within 1.44±1.5
    "2026-09-06T15:00:03Z",   # 2.0s gap  — within 1.44±1.5
    "2026-09-06T15:00:04Z",   # 1.0s gap  — within 1.44±1.5
]
for i, ev in enumerate(chain_events):
    ev["timestamp"] = chain_ts[i]
    resp = post(ev)
    print(f"  POST event {i+1}: id={resp['id']} vehicle={ev['vehicle_id']} ts={ev['timestamp']}")

time.sleep(0.3)   # let engine settle

# ── SCENARIO B: independent recurrence, 15-min gaps ──────────────────────────
print("\n=== SCENARIO B — Non-chain / independent recurrence (3 vehicles, 15-min gaps) ===")
indep_events = [
    {"vehicle_id": "IND-V1", "timestamp": "2026-09-06T16:00:00Z",
     "latitude": 12.9718, "longitude": 77.5940,
     "speed": 60.0, "acceleration": -4.0,
     "heading": 45.0, "event_type": "HARD_BRAKING", "confidence": 0.85},
    {"vehicle_id": "IND-V2", "timestamp": "2026-09-06T16:15:00Z",
     "latitude": 12.9719, "longitude": 77.5941,
     "speed": 58.0, "acceleration": -3.8,
     "heading": 46.0, "event_type": "HARD_BRAKING", "confidence": 0.80},
    {"vehicle_id": "IND-V3", "timestamp": "2026-09-06T16:30:00Z",
     "latitude": 12.9720, "longitude": 77.5942,
     "speed": 62.0, "acceleration": -4.2,
     "heading": 44.0, "event_type": "HARD_BRAKING", "confidence": 0.88},
]
for i, ev in enumerate(indep_events):
    resp = post(ev)
    print(f"  POST event {i+1}: id={resp['id']} vehicle={ev['vehicle_id']} ts={ev['timestamp']}")

time.sleep(0.3)

# ── GET /hotspots ─────────────────────────────────────────────────────────────
print("\n=== GET /hotspots ===")
hotspots = get("/hotspots")
print(f"  Total clusters: {len(hotspots)}\n")
for h in hotspots:
    print(f"  Hotspot: {h['hotspot_id'][:8]}...")
    print(f"    lat/lon:        ({h['latitude']:.4f}, {h['longitude']:.4f})")
    print(f"    risk_score:     {h['risk_score']}  ->  {h['status']}")
    print(f"    unique_vehicles:{h['unique_vehicles']}")
    print(f"    total_events:   {h['total_events']}")
    print(f"    event_breakdown:{h['event_breakdown']}")
    print(f"    possible_chain: {h['possible_chain']}")
    print(f"    first_detected: {h['first_detected']}")
    print(f"    last_observed:  {h['last_observed']}")
    print()
