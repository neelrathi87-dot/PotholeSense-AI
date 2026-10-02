import os
import sys
import time
import math
import requests
from datetime import datetime, timezone

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key-12345")
IMAGE_PATH = os.getenv("TEST_IMAGE", "pothole.jpg")
CLEAR_IMAGE_PATH = os.getenv("CLEAR_IMAGE", "clear_road.jpg")

# 25-kilometer highway & arterial patrol corridor (NH-60 / Mumbai-Agra Highway)
LONG_DISTANCE_ROUTE = [
    {"lat": 19.9750, "lon": 73.7420, "km": 0.0, "spot": "Dwarka Circle Start"},
    {"lat": 19.9820, "lon": 73.7550, "km": 1.8, "spot": "Nashik Road Sector 1"},
    {"lat": 19.9890, "lon": 73.7680, "km": 3.4, "spot": "Upnagar Flyover"},
    {"lat": 19.9975, "lon": 73.7898, "km": 5.2, "spot": "MG Road Crossing"},
    {"lat": 20.0050, "lon": 73.8050, "km": 7.1, "spot": "Amrutdham Junction"},
    {"lat": 20.0180, "lon": 73.8240, "km": 9.5, "spot": "Panchavati Bypass"},
    {"lat": 20.0320, "lon": 73.8450, "km": 12.3, "spot": "Adgaon Toll Plaza"},
    {"lat": 20.0460, "lon": 73.8680, "km": 15.1, "spot": "NH-60 Highway North 1"},
    {"lat": 20.0610, "lon": 73.8920, "km": 18.0, "spot": "NH-60 Highway North 2"},
    {"lat": 20.0780, "lon": 73.9180, "km": 21.4, "spot": "Ozar Airport Approach"},
    {"lat": 20.0920, "lon": 73.9450, "km": 24.8, "spot": "HAL Industrial Gateway"},
]

def run_long_distance_simulation():
    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] Test image '{IMAGE_PATH}' not found.")
        return

    with open(IMAGE_PATH, "rb") as f:
        pothole_bytes = f.read()

    clear_bytes = None
    if os.path.exists(CLEAR_IMAGE_PATH):
        with open(CLEAR_IMAGE_PATH, "rb") as f:
            clear_bytes = f.read()

    total_km = LONG_DISTANCE_ROUTE[-1]["km"]
    print("==========================================================================")
    print(" 🚗 PotholeSense — Long Distance Highway Corridor Patrol Simulation")
    print(f" Total Route Distance : {total_km:.1f} Kilometers across 11 major highway sectors")
    print(f" Target Server Host   : {SERVER_URL}")
    print("==========================================================================\n")

    potholes_found = 0

    for idx, pt in enumerate(LONG_DISTANCE_ROUTE, 1):
        lat = pt["lat"]
        lon = pt["lon"]
        km = pt["km"]
        spot = pt["spot"]
        device_id = "highway-patrol-bus-12"

        # Most waypoints have potholes, occasional clear stretch
        is_pothole = (idx % 4 != 0)
        img_data = pothole_bytes if is_pothole else (clear_bytes or pothole_bytes)

        print(f"[{idx:02d}/{len(LONG_DISTANCE_ROUTE)}] km {km:4.1f} | {spot} ({lat:.4f}, {lon:.4f})")
        start_t = time.time()

        try:
            res = requests.post(
                f"{SERVER_URL}/detect",
                headers={"x-api-key": API_KEY},
                files={"frame": ("frame.jpg", img_data, "image/jpeg")},
                data={
                    "lat": lat,
                    "lon": lon,
                    "device_id": device_id,
                    "captured_at": datetime.now(timezone.utc).isoformat()
                },
                timeout=12
            )
            elapsed = (time.time() - start_t) * 1000

            if res.status_code == 200:
                data = res.json()
                if data.get("detected"):
                    potholes_found += 1
                    sev = data.get("severity", "").upper()
                    conf = data.get("confidence", 0) * 100
                    print(f"     🚨 POTHOLE DETECTED! Severity: [{sev}] | Conf: {conf:.1f}% ({elapsed:.0f}ms)")
                else:
                    print(f"     ✅ Clear road surface ({elapsed:.0f}ms)")
            else:
                print(f"     ❌ Server error {res.status_code}: {res.text}")
        except requests.RequestException as e:
            print(f"     ⚠️ Network error: {e}")

        time.sleep(0.8)

    print("\n==========================================================================")
    print(" 🎉 Long-Distance Corridor Patrol Complete!")
    print(f" • Distance Covered : {total_km:.1f} km")
    print(f" • Hazards Logged   : {potholes_found} potholes mapped across highway")
    print(" 👉 Open http://localhost:3000 to see:")
    print("    1. 'Heatmap' view: see the full 25km heat corridor")
    print("    2. 'Clustered markers' view: see regional grouping across the region")
    print("==========================================================================")

if __name__ == "__main__":
    run_long_distance_simulation()
