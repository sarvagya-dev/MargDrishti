import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    with urllib.request.urlopen(f"{BASE_URL}/") as response:
        data = json.loads(response.read().decode())
        print("GET / Health Check:", data)

def test_post_event():
    payload = {
        "vehicle_id": "DL-01-CA-9999",
        "timestamp": "2026-09-06T21:42:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "speed": 78.4,
        "acceleration": -3.9,
        "heading": 45.0,
        "event_type": "HARD_BRAKING",
        "confidence": 0.88
    }
    req = urllib.request.Request(
        f"{BASE_URL}/events",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("POST /events Response:", data)

def test_get_events():
    with urllib.request.urlopen(f"{BASE_URL}/events") as response:
        data = json.loads(response.read().decode())
        print("GET /events Response Count:", len(data))
        for item in data:
            print("  - Event ID:", item["id"], "| Vehicle:", item["vehicle_id"], "| Type:", item["event_type"])

if __name__ == "__main__":
    test_health()
    test_post_event()
    test_get_events()
