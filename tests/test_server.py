import os
import pytest
from fastapi.testclient import TestClient
from main import app, API_KEY

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "storage_and_db" in data

def test_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "PotholeSense AI" in response.text

def test_detect_unauthorized():
    with open("test.jpg", "rb") as f:
        response = client.post(
            "/detect",
            files={"frame": ("test.jpg", f, "image/jpeg")},
            data={"lat": 19.9975, "lon": 73.7898}
        )
    assert response.status_code == 401

def test_detect_success_and_deduplication():
    # 1. First detection (should succeed and log)
    with open("test.jpg", "rb") as f:
        response = client.post(
            "/detect",
            headers={"x-api-key": API_KEY},
            files={"frame": ("test.jpg", f, "image/jpeg")},
            data={"lat": 19.1234, "lon": 72.8567, "device_id": "test-vehicle-01"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["detected"] is True
    assert data["logged"] is True
    assert data["severity"] in ["low", "medium", "high"]
    assert "record" in data
    pothole_id = data["record"]["id"]

    # 2. Duplicate detection within 12 meters
    with open("test.jpg", "rb") as f:
        dup_response = client.post(
            "/detect",
            headers={"x-api-key": API_KEY},
            files={"frame": ("test.jpg", f, "image/jpeg")},
            data={"lat": 19.12341, "lon": 72.85671, "device_id": "test-vehicle-01"}
        )
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["detected"] is True
    assert dup_data["logged"] is False
    assert dup_data.get("reason") == "duplicate"

    # 3. Query list
    list_res = client.get("/potholes")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(x["id"] == pothole_id for x in items)

    # 4. Update status
    patch_res = client.patch(
        f"/potholes/{pothole_id}",
        headers={"x-api-key": API_KEY},
        json={"status": "in_progress"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_progress"

    # 5. Stats check
    stats_res = client.get("/potholes/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_potholes"] >= 1

    # 6. GeoJSON export
    geo_res = client.get("/potholes/export/geojson")
    assert geo_res.status_code == 200
    assert "FeatureCollection" in geo_res.text

    # 7. CSV export
    csv_res = client.get("/potholes/export/csv")
    assert csv_res.status_code == 200
    assert "device_id,lat,lon" in csv_res.text

    # 8. Delete pothole
    del_res = client.delete(f"/potholes/{pothole_id}", headers={"x-api-key": API_KEY})
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True
