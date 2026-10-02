import os
import io
import csv
import json
import math
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ultralytics import YOLO

from database import StorageAndDatabaseManager
from privacy import PrivacyBlur

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pothole-server")

# Configuration with safe fallbacks
API_KEY = os.getenv("API_KEY", "test-api-key-12345")
CONF = float(os.getenv("CONF_THRESHOLD", "0.40"))
DEDUP_METERS = float(os.getenv("DEDUP_METERS", "12"))
DEDUP_SECONDS = int(os.getenv("DEDUP_SECONDS", "600"))
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")

app = FastAPI(
    title="PotholeSense AI Detection & Monitoring Server",
    description="Edge-to-Cloud IoT & Computer Vision Road Surface Monitoring System",
    version="2.0.0"
)

# Enable CORS for web dashboards and mobile/edge integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for uploads and assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load YOLO Model
logger.info(f"Loading YOLO model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
logger.info(f"YOLO model loaded. Detected classes: {model.names}")

# Initialize Storage & Database Manager (Supabase or Local SQLite)
db = StorageAndDatabaseManager()

# Initialize Privacy Blur (faces and license plates)
privacy = PrivacyBlur()

# Thread-safe in-memory deduplication cache
recent = []
lock = threading.Lock()


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def is_duplicate(lat: float, lon: float) -> bool:
    """Deduplicates potholes detected close together within recent time window."""
    now = time.time()
    with lock:
        recent[:] = [x for x in recent if now - x[2] < DEDUP_SECONDS]
        for la, lo, _ in recent:
            if haversine(lat, lon, la, lo) < DEDUP_METERS:
                return True
        recent.append((lat, lon, now))
    return False


def severity_from_ratio(ratio: float) -> str:
    """Calculates severity classification based on bounding box normalized area ratio."""
    if ratio < 0.01:
        return "low"
    if ratio < 0.03:
        return "medium"
    return "high"


class PotholeStatusUpdate(BaseModel):
    status: str = Field(..., description="Status must be 'open', 'in_progress', or 'fixed'")


# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    """Serves the interactive geospatial dashboard."""
    template_path = os.path.join("templates", "dashboard.html")
    if os.path.exists(template_path):
        return FileResponse(template_path, media_type="text/html")
    return HTMLResponse("<h1>PotholeSense AI Server Running</h1><p>Dashboard template not found.</p>")


@app.get("/mobile", response_class=HTMLResponse)
def get_mobile():
    """Serves the mobile edge camera & GPS patrol client."""
    template_path = os.path.join("templates", "mobile.html")
    if os.path.exists(template_path):
        return FileResponse(template_path, media_type="text/html")
    return HTMLResponse("<h1>Mobile template not found</h1>")


@app.get("/health")
def health():
    """Health check endpoint providing runtime status."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": {
            "path": MODEL_PATH,
            "classes": model.names,
            "conf_threshold": CONF
        },
        "storage_and_db": {
            "mode": "supabase" if db.use_supabase else "local_sqlite",
            "bucket": db.bucket_name if db.use_supabase else "local_filesystem"
        },
        "privacy": {
            "enabled": privacy.enabled,
            "mode": privacy.mode
        }
    }


@app.post("/detect")
def detect(
    frame: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...),
    device_id: str = Form("bus-01"),
    captured_at: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None),
):
    """
    Core AI edge upload endpoint:
    - Runs YOLO pothole inference
    - Computes confidence and severity
    - Performs spatial-temporal deduplication
    - Stores annotated frame and logs detection record
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    raw = frame.file.read()
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image encoding")

    result = model.predict(img, conf=CONF, imgsz=640, verbose=False)[0]
    if len(result.boxes) == 0:
        return {"detected": False, "pothole_count": 0}

    if is_duplicate(lat, lon):
        return {"detected": True, "logged": False, "reason": "duplicate", "pothole_count": len(result.boxes)}

    confs = result.boxes.conf.cpu().numpy()
    wh = result.boxes.xywhn.cpu().numpy()
    ratio = float((wh[:, 2] * wh[:, 3]).max())
    confidence = float(confs.max())
    severity = severity_from_ratio(ratio)

    safe_img, blurred = privacy.apply(img)
    annotated = result.plot(img=safe_img)
    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise HTTPException(status_code=500, detail="Frame encoding failed")

    # Upload annotated frame
    image_url = db.upload_image(device_id, buf.tobytes())

    ts = captured_at or datetime.now(timezone.utc).isoformat()
    row = {
        "device_id": device_id,
        "lat": lat,
        "lon": lon,
        "confidence": round(confidence, 3),
        "severity": severity,
        "pothole_count": int(len(result.boxes)),
        "image_url": image_url,
        "status": "open",
        "detected_at": ts,
    }
    saved_record = db.insert_pothole(row)

    return {
        "detected": True,
        "logged": True,
        "severity": severity,
        "confidence": round(confidence, 3),
        "pothole_count": int(len(result.boxes)),
        "blurred_regions": blurred,
        "record": saved_record
    }


@app.get("/potholes")
def list_potholes(
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
):
    """Retrieve list of potholes with optional filters."""
    return db.list_potholes(limit=limit, offset=offset, severity=severity, status=status, device_id=device_id)


@app.get("/potholes/stats")
def get_potholes_stats():
    """Retrieve summary metrics and KPI statistics."""
    return db.get_stats()


@app.get("/potholes/export/geojson")
def export_geojson():
    """Export all detected potholes as an RFC 7946 GeoJSON FeatureCollection."""
    potholes = db.list_potholes(limit=2000)
    features = []
    for p in potholes:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(p["lon"]), float(p["lat"])]
            },
            "properties": {
                "id": p["id"],
                "device_id": p["device_id"],
                "severity": p["severity"],
                "confidence": p["confidence"],
                "pothole_count": p.get("pothole_count", 1),
                "status": p.get("status", "open"),
                "image_url": p["image_url"],
                "detected_at": p["detected_at"]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return Response(
        content=json.dumps(geojson, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": 'attachment; filename="potholes.geojson"'}
    )


@app.get("/potholes/export/csv")
def export_csv():
    """Export pothole records as CSV."""
    potholes = db.list_potholes(limit=2000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "device_id", "lat", "lon", "confidence", "severity", "pothole_count", "status", "detected_at", "image_url"])

    for p in potholes:
        writer.writerow([
            p.get("id"),
            p.get("device_id"),
            p.get("lat"),
            p.get("lon"),
            p.get("confidence"),
            p.get("severity"),
            p.get("pothole_count", 1),
            p.get("status", "open"),
            p.get("detected_at"),
            p.get("image_url")
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=potholes.csv"}
    )


@app.get("/potholes/{pothole_id}")
def get_pothole(pothole_id: str):
    """Retrieve single pothole by ID."""
    record = db.get_pothole(pothole_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pothole not found")
    return record


@app.patch("/potholes/{pothole_id}")
def update_status(
    pothole_id: str,
    update: PotholeStatusUpdate,
    x_api_key: Optional[str] = Header(None)
):
    """Update pothole status (open, in_progress, fixed)."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if update.status not in ("open", "in_progress", "fixed"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'open', 'in_progress', or 'fixed'")

    res = db.update_pothole_status(pothole_id, update.status)
    if not res:
        raise HTTPException(status_code=404, detail="Pothole not found")
    return res


@app.delete("/potholes/{pothole_id}")
def delete_pothole(
    pothole_id: str,
    x_api_key: Optional[str] = Header(None)
):
    """Delete a pothole record."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    ok = db.delete_pothole(pothole_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pothole not found")
    return {"deleted": True, "id": pothole_id}
