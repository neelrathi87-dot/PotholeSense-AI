# 🚗 Raspberry Pi Edge Setup & Deployment Guide

This directory contains everything required to deploy the **PotholeSense** edge client on a Raspberry Pi or in-vehicle computer.

---

## 📦 Directory Contents
- `client.py`: The edge client script handling camera capture, GPS reading, throttling, downsampling, and HTTP transmission.
- `requirements.txt`: Python packages needed for the Pi (`opencv-python-headless`, `requests`, `gpsd-py3`).
- `pothole.jpg`: Sample test image for quick network and detection verification.
- `run_desk_test.sh`: 1-click bash script to run on your desk (uses mock GPS and disables speed filtering).
- `run_field_client.sh`: 1-click bash script for live road patrol with real GPS and camera.

---

## 🛠️ Step 1: Install System Packages on the Pi

Connect to your Raspberry Pi via terminal/SSH and run:

```bash
sudo apt update
sudo apt install -y gpsd gpsd-clients python3-pip
```

---

## 📡 Step 2: Configure and Test USB GPS Receiver

1. Plug your USB GPS receiver into the Raspberry Pi.
2. Confirm the system sees it:
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   ```
3. Start or restart `gpsd`:
   ```bash
   sudo systemctl restart gpsd
   ```
4. Verify satellite fix (you need a 2D or 3D fix):
   ```bash
   cgps -s
   ```
   *(Ensure you are near a window or outdoors with clear sky view. The first satellite fix can take 2–5 minutes).*

---

## 🐍 Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Step 4: Run the Client

### Option A: Desk Testing (No GPS fix needed)
Run the desk test script, which uses simulated coordinates and zero minimum speed:

```bash
chmod +x run_desk_test.sh
./run_desk_test.sh
```

### Option B: Field Patrol Mode (Vehicle Road Test)
When ready to drive or walk with real GPS:

```bash
chmod +x run_field_client.sh
./run_field_client.sh
```

### Custom Server Address:
If your laptop IP changes, you can pass it directly:
```bash
SERVER_URL="http://<your-laptop-ip>:8000" ./run_desk_test.sh
```

---

## ⚡ Step 5: Enable Auto-Start on Boot (systemd service)

To automatically launch the pothole detection client whenever the vehicle or Raspberry Pi turns on:

1. Setup the project folder on the Pi:
   ```bash
   mkdir -p /home/pi/pothole
   cp client.py requirements.txt pothole.jpg pothole-client.service pi.env.example /home/pi/pothole/
   cd /home/pi/pothole
   cp pi.env.example pi.env
   ```
2. Edit `pi.env` with your actual server URL and API key:
   ```bash
   nano pi.env
   ```
3. Install and enable the systemd service:
   ```bash
   sudo cp pothole-client.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now pothole-client
   ```
4. Check live service status and streaming logs:
   ```bash
   sudo systemctl status pothole-client
   journalctl -u pothole-client -f
   ```
5. To stop or restart:
   ```bash
   sudo systemctl stop pothole-client
   sudo systemctl restart pothole-client
   ```
