#!/bin/bash
# Real road patrol launcher script (Real USB GPS & USB camera)
export SERVER_URL="${SERVER_URL:-http://10.196.224.2:8000}"
export API_KEY="${API_KEY:-test-api-key-12345}"
export DEVICE_ID="${DEVICE_ID:-bus-01}"
export CAMERA_INDEX=0
export MIN_SPEED_MS=1.5
export MOCK_GPS=false

echo "============================================="
echo " 🚗 PotholeSense Edge Patrol Client (Field Mode)"
echo " Server : $SERVER_URL"
echo " Device : $DEVICE_ID"
echo " GPS    : Real GPS Hardware via gpsd"
echo " Speed  : 1.5 m/s threshold (> 5.4 km/h)"
echo "============================================="

python3 client.py
