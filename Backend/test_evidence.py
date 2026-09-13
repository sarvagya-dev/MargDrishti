"""Quick end-to-end test for POST /evidence and GET /events/{id}."""
import urllib.request
import json
import uuid

BASE = "http://127.0.0.1:8000"

# 1. Create a fresh event
payload = json.dumps({
    "vehicle_id": "TEST_EV_UPLOAD",
    "timestamp": "2026-09-07T02:00:00Z",
    "latitude": 18.5204, "longitude": 73.8567,
    "speed": 40.0, "acceleration": -5.5, "heading": 180.0,
    "event_type": "HARD_BRAKING", "confidence": 0.90
}).encode()
req = urllib.request.Request(
    BASE + "/events", data=payload,
    headers={"Content-Type": "application/json"}, method="POST"
)
event = json.loads(urllib.request.urlopen(req).read())
eid = event["id"]
print(f"[1] Event created: id={eid}")

# 2. POST /evidence — fake 5-byte webm blob
boundary = "bnd" + uuid.uuid4().hex[:8]
CRLF = b"\r\n"
body = (
    b"--" + boundary.encode() + CRLF
    + b'Content-Disposition: form-data; name="event_id"' + CRLF + CRLF
    + str(eid).encode() + CRLF
    + b"--" + boundary.encode() + CRLF
    + b'Content-Disposition: form-data; name="video"; filename="ev.webm"' + CRLF
    + b"Content-Type: video/webm" + CRLF + CRLF
    + b"\x1a\x45\xdf\xa3FAKEWEBM" + CRLF
    + b"--" + boundary.encode() + b"--" + CRLF
)
req2 = urllib.request.Request(
    BASE + "/evidence", data=body, method="POST"
)
req2.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
res2 = json.loads(urllib.request.urlopen(req2).read())
print(f"[2] Evidence created: {json.dumps(res2, indent=2)}")

# 3. GET /events/{id} — should show evidence list
detail = json.loads(urllib.request.urlopen(BASE + f"/events/{eid}").read())
print(f"[3] GET /events/{eid}: evidence count = {len(detail['evidence'])}")
print("    evidence[0]:", json.dumps(detail["evidence"][0], indent=4))

# 4. GET /evidence/{evidence_id} — should 200 (the fake bytes)
ev_id = res2["id"]
resp4 = urllib.request.urlopen(BASE + f"/evidence/{ev_id}")
print(f"[4] GET /evidence/{ev_id}: status={resp4.status}, content-type={resp4.headers.get('content-type')}")

# 5. GET /hotspots — must still work
hots = json.loads(urllib.request.urlopen(BASE + "/hotspots").read())
print(f"[5] GET /hotspots: {len(hots)} hotspot(s) returned OK")

print("\nAll checks passed.")
