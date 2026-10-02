import os
import sys
import time
import queue
import logging
import threading
from datetime import datetime, timezone

import cv2
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CLIENT %(levelname)s] %(message)s")
logger = logging.getLogger("edge-client")

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key-12345")
DEVICE_ID = os.getenv("DEVICE_ID", "bus-01")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "")  # Path to mp4/video or empty for webcam
INTERVAL = float(os.getenv("SEND_INTERVAL", "0.5"))
MIN_SPEED = float(os.getenv("MIN_SPEED_MS", "1.5"))
WIDTH = int(os.getenv("FRAME_WIDTH", "640"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "70"))
MOCK_GPS = os.getenv("MOCK_GPS", "false").lower() in ("true", "1", "yes")

q = queue.Queue(maxsize=60)
session = requests.Session()
gps_connected = False


def init_gps():
    global gps_connected
    if MOCK_GPS:
        logger.info("MOCK_GPS enabled. Using simulated GPS stream.")
        gps_connected = False
        return
    try:
        import gpsd
        gpsd.connect()
        gps_connected = True
        logger.info("Successfully connected to gpsd daemon.")
    except Exception as e:
        logger.warning(f"Could not connect to gpsd ({e}). Falling back to simulated coordinates.")
        gps_connected = False


# Simulated mock route state
sim_lat = float(os.getenv("MOCK_LAT", "19.9975"))
sim_lon = float(os.getenv("MOCK_LON", "73.7898"))
sim_speed = 8.5  # m/s (~30 km/h)


def get_fix():
    global sim_lat, sim_lon
    if gps_connected:
        try:
            import gpsd
            p = gpsd.get_current()
            if p.mode < 2:
                return None
            speed = getattr(p, "speed", None)
            if callable(speed):
                speed_val = speed()
            else:
                speed_val = speed if speed is not None else 5.0
            return p.lat, p.lon, speed_val
        except Exception as e:
            logger.debug(f"GPS read error: {e}")
            return None
    else:
        # Advance simulated vehicle position slightly
        sim_lat += 0.0001
        sim_lon += 0.00015
        return sim_lat, sim_lon, sim_speed


def capture_loop():
    source = VIDEO_SOURCE if VIDEO_SOURCE and os.path.exists(VIDEO_SOURCE) else CAMERA_INDEX
    logger.info(f"Opening video capture source: {source}")
    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        logger.error(f"Failed to open video source {source}. Please check camera connection or file path.")
        return

    last = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            if VIDEO_SOURCE:
                logger.info("End of video file. Rewinding to start.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.5)
                continue
            time.sleep(0.5)
            continue

        now = time.time()
        if now - last < INTERVAL:
            continue

        fix = get_fix()
        if fix is None:
            continue

        lat, lon, speed = fix
        if speed < MIN_SPEED:
            continue

        last = now
        h, w = frame.shape[:2]
        frame = cv2.resize(frame, (WIDTH, int(h * WIDTH / w)))
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not ok:
            continue

        item = {
            "jpg": buf.tobytes(),
            "lat": lat,
            "lon": lon,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

        if q.full():
            try:
                q.get_nowait()
            except queue.Empty:
                pass
        q.put(item)


def sender_loop():
    logger.info(f"Sender thread started. Target server: {SERVER_URL}/detect")
    while True:
        item = q.get()
        for attempt in range(3):
            try:
                r = session.post(
                    f"{SERVER_URL}/detect",
                    headers={"x-api-key": API_KEY},
                    files={"frame": ("f.jpg", item["jpg"], "image/jpeg")},
                    data={
                        "lat": item["lat"],
                        "lon": item["lon"],
                        "device_id": DEVICE_ID,
                        "captured_at": item["ts"],
                    },
                    timeout=10,
                )
                if r.status_code == 200:
                    resp = r.json()
                    if resp.get("detected"):
                        logger.info(f"POTHOLE DETECTED! Severity: {resp.get('severity')} | Logged: {resp.get('logged')} | Count: {resp.get('pothole_count')}")
                    else:
                        logger.debug("Frame analyzed: Clear road (No potholes).")
                    break
                elif 400 <= r.status_code < 500:
                    logger.warning(f"Server returned client error {r.status_code}: {r.text}")
                    break
            except requests.RequestException as e:
                logger.warning(f"Network error (attempt {attempt + 1}/3): {e}")
                time.sleep(2 * (attempt + 1))


if __name__ == "__main__":
    init_gps()
    threading.Thread(target=sender_loop, daemon=True).start()
    try:
        capture_loop()
    except KeyboardInterrupt:
        logger.info("Edge client stopped by user.")
