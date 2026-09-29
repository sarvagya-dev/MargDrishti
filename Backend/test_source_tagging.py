"""
Test script to verify source tagging implementation
Run this AFTER the backend server is started manually
"""
import json
import urllib.request
import sys

API_BASE = "http://localhost:8000"

def test_api(endpoint, method="GET", data=None):
    """Simple HTTP request helper"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            with urllib.request.urlopen(url) as resp:
                return json.loads(resp.read().decode("utf-8"))
        elif method == "POST":
            req_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        elif method == "DELETE":
            req = urllib.request.Request(url, method="DELETE")
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: {endpoint} - {e}")
        return None

def main():
    print("=" * 70)
    print("MARG-DRISHTI Source Tagging Test")
    print("=" * 70)
    
    # 1. Check backend health
    print("\n1. Checking backend health...")
    health = test_api("/")
    if not health:
        print("   ❌ Backend not responding. Start it with: python main.py")
        sys.exit(1)
    print(f"   ✓ Backend OK: {health.get('service')}")
    
    # 2. Get initial event count
    print("\n2. Checking initial events...")
    initial_events = test_api("/events")
    if initial_events is None:
        print("   ❌ Failed to fetch events")
        sys.exit(1)
    
    demo_count = sum(1 for e in initial_events if e.get("source") == "DEMO_SEED")
    phone_count = sum(1 for e in initial_events if e.get("source") == "PHONE")
    sim_count = sum(1 for e in initial_events if e.get("source") == "SIMULATOR")
    
    print(f"   Initial event counts:")
    print(f"   - DEMO_SEED: {demo_count}")
    print(f"   - PHONE: {phone_count}")
    print(f"   - SIMULATOR: {sim_count}")
    
    # 3. Post a test PHONE event
    print("\n3. Posting test PHONE event...")
    phone_event = {
        "vehicle_id": "TEST-PHONE-01",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "speed": 50.0,
        "acceleration": -3.5,
        "heading": 90.0,
        "event_type": "HARD_BRAKING",
        "confidence": 0.85,
        "source": "PHONE"
    }
    result = test_api("/events", "POST", phone_event)
    if result and result.get("source") == "PHONE":
        print(f"   ✓ PHONE event created: ID {result.get('id')}")
    else:
        print("   ❌ PHONE event creation failed")
    
    # 4. Post a test SIMULATOR event
    print("\n4. Posting test SIMULATOR event...")
    sim_event = {
        "vehicle_id": "TEST-SIM-01",
        "timestamp": "2025-01-15T10:31:00.000Z",
        "latitude": 28.6140,
        "longitude": 77.2091,
        "speed": 52.0,
        "acceleration": -4.0,
        "heading": 90.0,
        "event_type": "HARD_BRAKING",
        "confidence": 0.88,
        "source": "SIMULATOR"
    }
    result = test_api("/events", "POST", sim_event)
    if result and result.get("source") == "SIMULATOR":
        print(f"   ✓ SIMULATOR event created: ID {result.get('id')}")
    else:
        print("   ❌ SIMULATOR event creation failed")
    
    # 5. Verify both events exist
    print("\n5. Verifying event creation...")
    all_events = test_api("/events")
    test_phone = [e for e in all_events if e.get("vehicle_id") == "TEST-PHONE-01"]
    test_sim = [e for e in all_events if e.get("vehicle_id") == "TEST-SIM-01"]
    
    if test_phone and test_phone[0].get("source") == "PHONE":
        print("   ✓ TEST-PHONE-01 verified with source=PHONE")
    else:
        print("   ❌ TEST-PHONE-01 not found or wrong source")
    
    if test_sim and test_sim[0].get("source") == "SIMULATOR":
        print("   ✓ TEST-SIM-01 verified with source=SIMULATOR")
    else:
        print("   ❌ TEST-SIM-01 not found or wrong source")
    
    # 6. Test DELETE /events/simulator
    print("\n6. Testing DELETE /events/simulator...")
    delete_result = test_api("/events/simulator", "DELETE")
    if delete_result:
        print(f"   ✓ Delete successful: {delete_result.get('message')}")
        print(f"   Deleted: {delete_result.get('deleted')} event(s)")
    else:
        print("   ❌ Delete failed")
    
    # 7. Verify SIMULATOR events deleted, PHONE events preserved
    print("\n7. Verifying selective deletion...")
    final_events = test_api("/events")
    final_phone = [e for e in final_events if e.get("vehicle_id") == "TEST-PHONE-01"]
    final_sim = [e for e in final_events if e.get("vehicle_id") == "TEST-SIM-01"]
    final_demo = [e for e in final_events if e.get("source") == "DEMO_SEED"]
    
    if final_phone:
        print("   ✓ TEST-PHONE-01 preserved after deletion")
    else:
        print("   ❌ TEST-PHONE-01 was incorrectly deleted!")
    
    if not final_sim:
        print("   ✓ TEST-SIM-01 correctly deleted")
    else:
        print("   ❌ TEST-SIM-01 still exists (should be deleted)")
    
    if len(final_demo) == demo_count:
        print(f"   ✓ All {demo_count} DEMO_SEED events preserved")
    else:
        print(f"   ❌ DEMO_SEED events changed: was {demo_count}, now {len(final_demo)}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
