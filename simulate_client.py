import os
import sys
import time
import requests
from datetime import datetime, timezone

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key-12345")
IMAGE_PATH = os.getenv("TEST_IMAGE", "test.jpg")

# Realistic waypoints along an urban corridor (Nashik, Maharashtra)
WAYPOINTS = [
    {"lat": 19.99745, "lon": 73.78980, "desc": "MG Road Crossing"},
    {"lat": 19.99820, "lon": 73.79110, "desc": "City Center Approach"},
    {"lat": 19.99950, "lon": 73.79320, "desc": "Ashok Stambh Junction"},
    {"lat": 20.00110, "lon": 73.79580, "desc": "College Road Entry"},
    {"lat": 20.00280, "lon": 73.79840, "desc": "Gangapur Naka"},
    {"lat": 20.00450, "lon": 73.80120, "desc": "Highway Bypass North"},
]

def run_simulation():
    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] Test image '{IMAGE_PATH}' not found. Please provide a valid test image.")
        return

    print("==================================================================")
    print(" 🚗 PotholeSense AI - Vehicle Patrol & Edge Upload Simulation")
    print("==================================================================")
    print(f"Target Server : {SERVER_URL}")
    print(f"Image Source  : {IMAGE_PATH}")
    print(f"Waypoints     : {len(WAYPOINTS)} locations along patrol corridor")
    print("------------------------------------------------------------------\n")

    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    for idx, wp in enumerate(WAYPOINTS, 1):
        lat = wp["lat"]
        lon = wp["lon"]
        desc = wp["desc"]
        device_id = f"bus-{idx % 3 + 1:02d}"

        print(f"[{idx}/{len(WAYPOINTS)}] Simulating Vehicle at {desc} ({lat}, {lon})")
        start_t = time.time()
        
        try:
            res = requests.post(
                f"{SERVER_URL}/detect",
                headers={"x-api-key": API_KEY},
                files={"frame": ("frame.jpg", img_bytes, "image/jpeg")},
                data={
                    "lat": lat,
                    "lon": lon,
                    "device_id": device_id,
                    "captured_at": datetime.now(timezone.utc).isoformat()
                },
                timeout=15
            )
            elapsed = (time.time() - start_t) * 1000

            if res.status_code == 200:
                data = res.json()
                if data.get("detected"):
                    sev = data.get("severity", "").upper()
                    conf = data.get("confidence", 0) * 100
                    logged = "LOGGED TO DB" if data.get("logged") else "DEDUPLICATED"
                    print(f"     ✅ Detection: [{sev}] Severity | Conf: {conf:.1f}% | {logged} ({elapsed:.0f}ms)")
                else:
                    print(f"     ℹ️ No pothole detected ({elapsed:.0f}ms)")
            else:
                print(f"     ❌ Server error {res.status_code}: {res.text}")

        except requests.RequestException as e:
            print(f"     ⚠️ Network error connecting to {SERVER_URL}: {e}")

        time.sleep(1.0)

    print("\n------------------------------------------------------------------")
    print("🎉 Simulation Complete!")
    print(f"👉 Open your browser at {SERVER_URL} to view the live interactive map!")
    print("==================================================================")

if __name__ == "__main__":
    run_simulation()
