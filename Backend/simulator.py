"""
MARG-DRISHTI Vehicle Telemetry Event Simulator
POSTs simulated vehicle telemetry events to the ingestion backend (http://localhost:8000/events)
and retrieves/displays resulting hotspot risk analytics (http://localhost:8000/hotspots).

Scenarios:
  - SCENARIO_B : Single vehicle isolated event ("insufficient evidence")
  - SCENARIO_C : 5 vehicles in a 3-5 min window ("clustered hotspot")
  - SCENARIO_D : Repeated burst at same spot after 10+ min simulated gap ("recurring evidence")
  - SCENARIO_E : 4 vehicles with ~20m/speed inter-vehicle delay ("chain reaction triggered")
"""

import argparse
import datetime
import json
import random
import sys
import time
import urllib.request
from typing import List, Dict, Any

# Ensure stdout handles UTF-8 on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DEFAULT_BACKEND_URL = "http://localhost:8000"

def parse_iso(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def post_event(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/events"
    # Ensure all simulator events are tagged with source='SIMULATOR'
    payload["source"] = "SIMULATOR"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [ERROR] Failed to POST event for vehicle {payload.get('vehicle_id')}: {e}")
        return {}

def fetch_hotspots(base_url: str) -> List[Dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/hotspots"
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [ERROR] Failed to fetch /hotspots: {e}")
        return []

def print_separator(char: str = "─", length: int = 70):
    print(char * length)

def print_hotspots_summary(hotspots: List[Dict[str, Any]], title: str = "BACKEND HOTSPOTS ANALYTICS"):
    print(f"\n┌{"─" * 68}┐")
    print(f"│  📊 {title:<60} │")
    print(f"├{"─" * 68}┤")
    if not hotspots:
        print("│  (No active hotspots detected)                                       │")
    else:
        for h in hotspots:
            h_id = h.get("hotspot_id", "")[:8]
            score = h.get("risk_score", 0)
            status = h.get("status", "LOW")
            vehicles = h.get("unique_vehicles", 0)
            events = h.get("total_events", 0)
            chain = h.get("possible_chain", False)
            chain_str = "⚠️ YES (CHAIN)" if chain else "NO (INDEPENDENT)"
            lat = h.get("latitude", 0.0)
            lon = h.get("longitude", 0.0)

            print(f"│  • HOTSPOT ID   : {h_id:<46} │")
            print(f"│    LOCATION     : Lat {lat:.4f}, Lon {lon:.4f}{' ' * 27} │")
            print(f"│    RISK SCORE   : {score:<3} ({status:<6}) {' ' * 38} │")
            print(f"│    VEHICLES     : {vehicles} unique | {events} total events{' ' * 27} │")
            print(f"│    CHAIN FLAG   : {chain_str:<46} │")
            print(f"├{"─" * 68}┤")
    print(f"└{"─" * 68}┘\n")


# ─── SCENARIO EXECUTORS ────────────────────────────────────────────────────────

def run_scenario_b(base_url: str, fast_time: bool):
    print_separator("=")
    print(" 🎬 SCENARIO B: Single Vehicle Isolated Event")
    print(" Description: 1 vehicle (V17) hard braking at isolated location.")
    print(" Expectation: Low risk score, insufficient evidence for alert.")
    print_separator("=")

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "vehicle_id": "V17",
        "timestamp": parse_iso(now),
        "latitude": 18.5204,
        "longitude": 73.8567,
        "speed": 65.0,
        "acceleration": -4.8,
        "heading": 90.0,
        "event_type": "HARD_BRAKING",
        "confidence": 0.85
    }

    print(f"\n  [POST] Vehicle {payload['vehicle_id']} @ ({payload['latitude']}, {payload['longitude']}) | Speed: {payload['speed']} km/h")
    res = post_event(base_url, payload)
    print(f"  [RESPONSE] Event ingested successfully. ID: {res.get('id')}")

    time.sleep(0.5)
    hotspots = fetch_hotspots(base_url)
    print_hotspots_summary(hotspots, "SCENARIO B HOTSPOT RESULT")


def run_scenario_c(base_url: str, fast_time: bool):
    print_separator("=")
    print(" 🎬 SCENARIO C: Clustered Multi-Vehicle Burst (3-5 min window)")
    print(" Description: 5 vehicles (V23, V31, V42, V50, V61) at Mumbai Highway within 50m.")
    print(" Expectation: Single cluster created, higher risk score.")
    print_separator("=")

    base_lat = 19.0760
    base_lon = 72.8777
    vehicles = ["V23", "V31", "V42", "V50", "V61"]
    base_time = datetime.datetime.now(datetime.timezone.utc)

    # 3-5 min gaps: 0s, 45s, 110s, 180s, 240s
    time_gaps = [0, 45, 110, 180, 240]

    for i, v_id in enumerate(vehicles):
        # Small spatial offset within 50m (~0.0002 deg)
        lat_offset = random.uniform(-0.00015, 0.00015)
        lon_offset = random.uniform(-0.00015, 0.00015)
        ev_time = base_time + datetime.timedelta(seconds=time_gaps[i])

        payload = {
            "vehicle_id": v_id,
            "timestamp": parse_iso(ev_time),
            "latitude": round(base_lat + lat_offset, 6),
            "longitude": round(base_lon + lon_offset, 6),
            "speed": round(random.uniform(55.0, 68.0), 1),
            "acceleration": round(random.uniform(-5.5, -4.6), 2),
            "heading": 180.0,
            "event_type": "HARD_BRAKING",
            "confidence": round(random.uniform(0.82, 0.94), 2)
        }

        print(f"  [POST {i+1}/5] Vehicle {payload['vehicle_id']} @ t+{time_gaps[i]}s | Speed: {payload['speed']} km/h")
        post_event(base_url, payload)
        if not fast_time:
            time.sleep(1.0)
        else:
            time.sleep(0.15)

    time.sleep(0.5)
    hotspots = fetch_hotspots(base_url)
    print_hotspots_summary(hotspots, "SCENARIO C HOTSPOT RESULT")


def run_scenario_d(base_url: str, fast_time: bool):
    print_separator("=")
    print(" 🎬 SCENARIO D: Repeated Hotspot Burst after 10+ min gap")
    print(" Description: Repeat burst at Mumbai Highway location after 12-min simulated gap.")
    print(" Expectation: Risk score rises due to recurring independent evidence.")
    print_separator("=")

    # Same location as Scenario C
    base_lat = 19.0760
    base_lon = 72.8777
    vehicles = ["V72", "V84", "V95"]

    # 12 minutes (720 seconds) after previous burst
    base_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=12)
    time_gaps = [0, 50, 120]

    for i, v_id in enumerate(vehicles):
        lat_offset = random.uniform(-0.0001, 0.0001)
        lon_offset = random.uniform(-0.0001, 0.0001)
        ev_time = base_time + datetime.timedelta(seconds=time_gaps[i])

        payload = {
            "vehicle_id": v_id,
            "timestamp": parse_iso(ev_time),
            "latitude": round(base_lat + lat_offset, 6),
            "longitude": round(base_lon + lon_offset, 6),
            "speed": round(random.uniform(50.0, 62.0), 1),
            "acceleration": round(random.uniform(-5.2, -4.5), 2),
            "heading": 180.0,
            "event_type": "HARD_BRAKING",
            "confidence": round(random.uniform(0.85, 0.95), 2)
        }

        print(f"  [POST {i+1}/3] Vehicle {payload['vehicle_id']} @ t+12m{time_gaps[i]}s | Speed: {payload['speed']} km/h")
        post_event(base_url, payload)
        if not fast_time:
            time.sleep(1.0)
        else:
            time.sleep(0.15)

    time.sleep(0.5)
    hotspots = fetch_hotspots(base_url)
    print_hotspots_summary(hotspots, "SCENARIO D HOTSPOT RESULT (CUMULATIVE EVIDENCE)")


def run_scenario_e(base_url: str, fast_time: bool):
    print_separator("=")
    print(" 🎬 SCENARIO E: Chain-Reaction Crash Burst")
    print(" Description: 4 vehicles (V1-V4) with ~20m / speed inter-vehicle delay.")
    print(" Expectation: Backend detects timing signature & flags possible_chain=true.")
    print_separator("=")

    base_lat = 28.6139
    base_lon = 77.2090
    vehicles = ["V1", "V2", "V3", "V4"]
    speed_kmh = 50.0 # 50 km/h = 13.89 m/s -> expected gap = 20m / 13.89 m/s = 1.44s
    speed_ms = speed_kmh / 3.6
    expected_gap_s = 20.0 / speed_ms # ~1.44 seconds

    base_time = datetime.datetime.now(datetime.timezone.utc)

    for i, v_id in enumerate(vehicles):
        delay_seconds = i * expected_gap_s
        ev_time = base_time + datetime.timedelta(seconds=delay_seconds)

        payload = {
            "vehicle_id": v_id,
            "timestamp": parse_iso(ev_time),
            "latitude": round(base_lat + (i * 0.00002), 6),
            "longitude": round(base_lon + (i * 0.00002), 6),
            "speed": speed_kmh,
            "acceleration": -5.2,
            "heading": 270.0,
            "event_type": "HARD_BRAKING",
            "confidence": 0.90
        }

        print(f"  [POST {i+1}/4] Vehicle {payload['vehicle_id']} @ t+{delay_seconds:.2f}s | Gap: ~{expected_gap_s:.2f}s (Expected for {speed_kmh}km/h)")
        post_event(base_url, payload)
        if not fast_time:
            time.sleep(1.0)
        else:
            time.sleep(0.15)

    time.sleep(0.5)
    hotspots = fetch_hotspots(base_url)
    print_hotspots_summary(hotspots, "SCENARIO E HOTSPOT RESULT (CHAIN-REACTION FLAG)")


# ─── MAIN CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MARG-DRISHTI Telemetry Event Simulator")
    parser.add_argument(
        "--scenario",
        type=str,
        default="ALL",
        choices=["B", "C", "D", "E", "ALL", "SCENARIO_B", "SCENARIO_C", "SCENARIO_D", "SCENARIO_E"],
        help="Scenario to run: B, C, D, E, or ALL (default: ALL)"
    )
    parser.add_argument(
        "--fast-time",
        action="store_true",
        default=True,
        help="Compress simulated gaps into real-time milliseconds for live demos (default: True)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_BACKEND_URL,
        help=f"Backend base URL (default: {DEFAULT_BACKEND_URL})"
    )

    args = parser.parse_args()
    scenario = args.scenario.upper().replace("SCENARIO_", "")

    print("\n🚀 MARG-DRISHTI VEHICLE EVENT SIMULATOR")
    print(f"   Target Backend: {args.url}")
    print(f"   Mode          : Scenario {scenario} | Fast-Time: {args.fast_time}\n")

    if scenario in ["B", "ALL"]:
        run_scenario_b(args.url, args.fast_time)

    if scenario in ["C", "ALL"]:
        run_scenario_c(args.url, args.fast_time)

    if scenario in ["D", "ALL"]:
        run_scenario_d(args.url, args.fast_time)

    if scenario in ["E", "ALL"]:
        run_scenario_e(args.url, args.fast_time)

    print("✅ Simulation complete.\n")

if __name__ == "__main__":
    main()
