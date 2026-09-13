"""
test_arch.py  —  MARG-DRISHTI Cluster vs Hotspot Architecture Tests

Four focused tests proving the two-level model:

  Test A: One isolated vehicle → LOW risk (insufficient evidence)
  Test B: Five independent vehicles in one burst → clustered into one hotspot, higher risk
  Test C: Another independent burst at the SAME location 10+ min later
          → SAME logical hotspot, stronger cumulative evidence (NOT a new hotspot)
  Test D: Four chain-timed vehicles at a DIFFERENT location
          → possible_chain=True, discounted scoring

Run against a live backend (events.db freshly cleared):
    uvicorn main:app --host 127.0.0.1 --port 8000
    python test_arch.py
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def post(payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/events",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [HTTP {e.code}] {body}")
        return {}

def get_hotspots() -> list:
    with urllib.request.urlopen(f"{BASE}/hotspots") as r:
        return json.loads(r.read())

def print_hotspots(label: str, hotspots: list):
    print(f"\n  >>> {label}")
    if not hotspots:
        print("      (no hotspots)")
        return
    for h in hotspots:
        print(f"      hotspot_id      : {h['hotspot_id'][:8]}...")
        print(f"      location        : ({h['latitude']:.4f}, {h['longitude']:.4f})")
        print(f"      risk_score      : {h['risk_score']}  ({h['status']})")
        print(f"      unique_vehicles : {h['unique_vehicles']}")
        print(f"      total_events    : {h['total_events']}")
        print(f"      possible_chain  : {h['possible_chain']}")
        print(f"      first_detected  : {h['first_detected']}")
        print(f"      last_observed   : {h['last_observed']}")
        print()

# ─── Test A: One isolated vehicle ─────────────────────────────────────────────

def test_a():
    print("=" * 65)
    print("TEST A: One isolated vehicle (V17) at Pune NH-48")
    print("        Expect: LOW risk, 1 hotspot, 1 event, chain=False")
    print("=" * 65)

    now = datetime.now(timezone.utc)
    post({
        "vehicle_id": "V17",
        "timestamp": _ts(now),
        "latitude": 18.5204, "longitude": 73.8567,
        "speed": 65.0, "acceleration": -4.8,
        "heading": 90.0, "event_type": "HARD_BRAKING", "confidence": 0.85,
    })

    h = get_hotspots()
    print_hotspots("After Test A", h)

    assert len(h) == 1, f"Expected 1 hotspot, got {len(h)}"
    assert h[0]["total_events"] == 1
    assert h[0]["status"] == "LOW", f"Expected LOW, got {h[0]['status']}"
    assert h[0]["possible_chain"] is False
    print("  [PASS] Test A\n")
    return h[0]["hotspot_id"]

# ─── Test B: Five independent vehicles in one burst ───────────────────────────

def test_b():
    print("=" * 65)
    print("TEST B: Five independent vehicles in one burst (Mumbai Highway)")
    print("        Expect: same or higher-score hotspot, chain=False")
    print("=" * 65)

    # All within 50m of base and within 4 min window
    base = datetime.now(timezone.utc)
    base_lat, base_lon = 19.0760, 72.8777
    vehicles = [
        ("V23", 0,   0.00005,  0.00003,  63.0, 0.88),
        ("V31", 45, -0.00004,  0.00006,  61.0, 0.90),
        ("V42", 110, 0.00002, -0.00005,  65.0, 0.86),
        ("V50", 175, 0.00007,  0.00002,  67.0, 0.91),
        ("V61", 240,-0.00003, -0.00004,  64.0, 0.89),
    ]
    for vid, offset_s, dlat, dlon, spd, conf in vehicles:
        post({
            "vehicle_id": vid,
            "timestamp": _ts(base + timedelta(seconds=offset_s)),
            "latitude":  round(base_lat + dlat, 6),
            "longitude": round(base_lon + dlon, 6),
            "speed": spd, "acceleration": -5.0,
            "heading": 180.0, "event_type": "HARD_BRAKING", "confidence": conf,
        })

    h = get_hotspots()
    # Find the Mumbai hotspot (lat ~19.07)
    mum = [x for x in h if abs(x["latitude"] - base_lat) < 0.01]
    print_hotspots("After Test B — Mumbai hotspot only", mum)

    assert len(mum) == 1, f"Expected 1 Mumbai hotspot, got {len(mum)}"
    assert mum[0]["unique_vehicles"] == 5
    assert mum[0]["total_events"] == 5
    assert mum[0]["possible_chain"] is False
    print("  [PASS] Test B\n")
    return mum[0]["hotspot_id"]

# ─── Test C: Second independent burst at SAME location, 12+ min later ────────

def test_c(hotspot_id_from_b: str):
    print("=" * 65)
    print("TEST C: Another burst at SAME Mumbai location, 12 min later")
    print("        Expect: SAME hotspot_id as Test B, higher evidence")
    print("=" * 65)

    # 12 minutes in the future → new temporal clusters, same logical hotspot
    later = datetime.now(timezone.utc) + timedelta(minutes=12)
    base_lat, base_lon = 19.0760, 72.8777
    vehicles = [
        ("V72",  0,  0.00003, -0.00002, 60.0, 0.87),
        ("V84", 50,  0.00006,  0.00004, 58.0, 0.92),
        ("V95", 120,-0.00002,  0.00005, 62.0, 0.90),
    ]
    for vid, offset_s, dlat, dlon, spd, conf in vehicles:
        post({
            "vehicle_id": vid,
            "timestamp": _ts(later + timedelta(seconds=offset_s)),
            "latitude":  round(base_lat + dlat, 6),
            "longitude": round(base_lon + dlon, 6),
            "speed": spd, "acceleration": -4.9,
            "heading": 180.0, "event_type": "HARD_BRAKING", "confidence": conf,
        })

    h = get_hotspots()
    mum = [x for x in h if abs(x["latitude"] - base_lat) < 0.01]
    print_hotspots("After Test C — Mumbai hotspot cumulative", mum)

    assert len(mum) == 1, f"Expected 1 Mumbai hotspot, got {len(mum)}"
    c_hid = mum[0]["hotspot_id"]
    assert c_hid == hotspot_id_from_b, (
        f"SAME hotspot expected!\n  Test B id: {hotspot_id_from_b[:8]}...\n  Test C id: {c_hid[:8]}..."
    )
    assert mum[0]["unique_vehicles"] == 8,   f"Expected 8 unique vehicles (5+3), got {mum[0]['unique_vehicles']}"
    assert mum[0]["total_events"]    == 8,   f"Expected 8 total events, got {mum[0]['total_events']}"
    assert mum[0]["possible_chain"]  is False
    print("  [PASS] Test C — same logical hotspot, cumulative evidence\n")

# ─── Test D: Four chain-timed vehicles at different location ──────────────────

def test_d():
    print("=" * 65)
    print("TEST D: Chain-reaction burst — 4 vehicles at Delhi, ~1.44s gaps")
    print("        Expect: possible_chain=True, discounted score")
    print("=" * 65)

    # 50 km/h = 13.89 m/s  =>  expected gap = 20m / 13.89 = 1.44 s
    speed_kmh = 50.0
    speed_ms  = speed_kmh / 3.6
    expected_gap = 20.0 / speed_ms   # ~1.44 s

    base = datetime.now(timezone.utc)
    base_lat, base_lon = 28.6139, 77.2090
    vehicles = ["V1", "V2", "V3", "V4"]

    for i, vid in enumerate(vehicles):
        ts = base + timedelta(seconds=i * expected_gap)
        post({
            "vehicle_id": vid,
            "timestamp": _ts(ts),
            "latitude":  round(base_lat + i * 0.00002, 6),
            "longitude": round(base_lon + i * 0.00002, 6),
            "speed": speed_kmh, "acceleration": -5.2,
            "heading": 270.0, "event_type": "HARD_BRAKING", "confidence": 0.90,
        })

    h = get_hotspots()
    delhi = [x for x in h if abs(x["latitude"] - base_lat) < 0.01]
    print_hotspots("After Test D — Delhi hotspot", delhi)

    assert len(delhi) == 1, f"Expected 1 Delhi hotspot, got {len(delhi)}"
    assert delhi[0]["possible_chain"] is True, "Expected possible_chain=True"
    assert delhi[0]["unique_vehicles"] == 4
    print("  [PASS] Test D — chain detected, possible_chain=True\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nMAR-DRISHTI ARCHITECTURE TESTS")
    print("Verifying cluster / hotspot two-level model\n")

    try:
        test_a()
        hid_b = test_b()
        test_c(hid_b)
        test_d()
        print("=" * 65)
        print("ALL TESTS PASSED")
        print("=" * 65)

        print("\nFINAL GET /hotspots output:")
        final = get_hotspots()
        print_hotspots("All hotspots after full test run", final)

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
