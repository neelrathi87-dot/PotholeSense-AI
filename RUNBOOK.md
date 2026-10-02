# 📖 PotholeSense Operational Runbook & Cheat Sheet

This document serves as the complete operational guide for deploying, running, tuning, and troubleshooting the PotholeSense AI road monitoring platform.

---

## 🛠️ 1. One-Time Setup

| # | Component | Action | Details |
|---|---|---|---|
| **1** | **Supabase** | Run `schema.sql` and `realtime.sql` | In your Supabase SQL editor to create the `potholes` table and enable realtime publication. |
| **2** | **Supabase** | Create Storage bucket | Name it `potholes` and toggle **Public Bucket** to ON. |
| **3** | **Server** | Setup environment | Ensure `best.pt` is in root, `.env` is filled, and run `pip install -r requirements.txt`. |
| **4** | **Dashboard** | Setup Next.js | Fill `dashboard/.env.local`, run `npm install` inside `dashboard/`. |
| **5** | **Edge Device (Pi)** | Hardware & Service | Install `gpsd`, attach USB GPS & camera, configure `pi.env`, install systemd service. |

---

## 🚀 2. Every Time You Use It (Execution Order)

Follow this launch sequence:

```text
[1. Server] ──► [2. Dashboard] ──► [3. Pi / Edge] ──► [4. Road Patrol / Bus]
```

1. **Server (FastAPI / AI Backend)**
   ```powershell
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Pass check:* Visiting `http://localhost:8000/health` returns `{"status":"ok"}`.

2. **Dashboard (Next.js)**
   ```powershell
   cd dashboard
   npm run dev
   ```
   *Pass check:* Open `http://localhost:3000` — map loads with filters and stats.

3. **Edge Client (Raspberry Pi)**
   * Starts automatically on boot if systemd service is installed.
   * Or run manually:
     ```bash
     python3 client.py
     ```
   *Pass check:* `journalctl -u pothole-client -f` shows:
     ```text
     [CLIENT INFO] Sender thread started. Target server: ...
     ```

4. **Patrol Vehicle / Bus**
   * As the vehicle moves ($> 1.5\text{ m/s}$ / $5.4\text{ km/h}$) with a valid GPS lock, road frames are evaluated.
   * Detections appear on the dashboard within seconds.

---

## 🗺️ 3. Using the Next.js Dashboard

| Goal | How To Do It |
|---|---|
| **See all hazards** | Open `http://localhost:3000`. The default view clusters nearby potholes into numbered circles. |
| **Zoom into an area** | Click on a numbered cluster bubble or scroll-zoom with mouse wheel / pinch. |
| **Inspect a pothole** | Click any marker to view the annotated evidence image, severity, confidence, timestamp, and bus ID. |
| **Navigate to incident** | Click *"Open in Google Maps"* inside the marker popup. |
| **Find worst road corridors**| Switch the **Map view** dropdown in the sidebar to **Heatmap**. |
| **Focus on urgent repairs** | Set **Severity** filter to `High` and **Status** filter to `Open`. |
| **See recent activity** | Set **Time range** to `Last 24 hours` or `Last 7 days`. |
| **Update repair status** | Enter your admin password in the sidebar (`admin123`), click a pothole marker, and change status to `In progress` or `Fixed`. |

> **Note on Fixed Potholes**: When a pothole is marked as `Fixed`, its marker turns gray, and it automatically drops out of the heatmap calculation and the *"High severity, unfixed"* counter.

---

## 🎛️ 4. Tuning Parameters After Initial Runs

| Observed Behavior | Recommended Adjustment | File / Location |
|---|---|---|
| **Shadows, road patches, or manholes flagged as potholes** | Increase `CONF_THRESHOLD` to `0.55` – `0.60` | Server `.env` |
| **Real shallow potholes missed by camera** | Lower `CONF_THRESHOLD` to `0.30` – `0.35` | Server `.env` |
| **Same pothole logged multiple times on one drive-by** | Increase `DEDUP_METERS` to `18` – `25` meters | Server `.env` |
| **Distinct adjacent potholes merged into one** | Lower `DEDUP_METERS` to `6` – `8` meters | Server `.env` |
| **Excessive mobile data usage on the patrol vehicle** | Lower `JPEG_QUALITY` (e.g. `60`) or `FRAME_WIDTH` (e.g. `512`), increase `SEND_INTERVAL` (e.g. `1.0s`) | Pi `pi.env` |

*(Remember to restart the server or Pi client after changing `.env` files).*

---

## ⚡ 5. Quick Test Without a Vehicle

To test the entire pipeline without driving:

1. **Send a test frame with curl to Nashik coordinates**:
   ```powershell
   curl -X POST http://localhost:8000/detect `
     -H "x-api-key: test-api-key-12345" `
     -F "frame=@pothole.jpg" `
     -F "lat=19.9975" `
     -F "lon=73.7898" `
     -F "device_id=bus-01"
   ```
2. **Observe Dashboard**: Open `http://localhost:3000` — the new detection pin appears on the map.
3. **Change Status**: Enter `admin123` in the sidebar password box, click the marker, change status to `Fixed`, and confirm the marker turns gray.

---

## 🩺 6. Troubleshooting Common Issues

| Symptom | Likely Cause | Solution |
|---|---|---|
| **No markers appear on dashboard** | Server not logging, or filters hiding records | Check server terminal logs; ensure filters are set to `All`. |
| **Markers only appear after manual refresh** | Realtime replication not activated in database | Run `alter publication supabase_realtime add table potholes;` in Supabase SQL editor. |
| **Popup images broken** | Bucket is private | In Supabase Storage, toggle `potholes` bucket to **Public**. |
| **Status update returns "Wrong admin password"** | Password mismatch | Check `ADMIN_PASSWORD` in `dashboard/.env.local` (default: `admin123`). |
| **Raspberry Pi client sends nothing** | Vehicle speed $< 1.5\text{ m/s}$ or no GPS fix | For indoor/bench testing, set `MIN_SPEED_MS=0` and `MOCK_GPS=true` in `pi.env`. |
| **HTTP 401 Unauthorized** | API Key mismatch | Verify `x-api-key` on Pi matches `API_KEY` in server `.env`. |
| **HTTP 500 on image upload** | Bucket name wrong or invalid key | Ensure bucket name is `potholes` and you used `service_role` key (not `anon` key) on the server. |
