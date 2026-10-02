#!/bin/bash
# Desk testing script (Simulated GPS, zero minimum speed threshold)
export SERVER_URL="${SERVER_URL:-http://10.196.224.2:8000}"
export API_KEY="${API_KEY:-test-api-key-12345}"
export DEVICE_ID="${DEVICE_ID:-pi-bench-01}"
export MIN_SPEED_MS=0
export MOCK_GPS=true

echo "============================================="
echo " 🚗 PotholeSense Edge Client (Desk Test Mode)"
echo " Server : $SERVER_URL"
echo " Device : $DEVICE_ID"
echo " GPS    : Simulated Mock GPS"
echo " Speed  : 0 m/s threshold (Desk mode)"
echo "============================================="

python3 client.py
