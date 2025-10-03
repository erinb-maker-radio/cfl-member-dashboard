#!/bin/bash
# Raspberry Pi Dashboard Startup Script
# Place in ~/CFL_Dashboard/start_dashboard.sh

# Set paths
DASHBOARD_DIR="/home/pi/CFL_Dashboard"
LOG_FILE="/home/pi/dashboard.log"

# Log startup
echo "$(date): Dashboard starting..." >> "$LOG_FILE"

# Wait for network
echo "$(date): Waiting for network..." >> "$LOG_FILE"
sleep 10

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0.5 -root &

# Start Chromium in kiosk mode
chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --kiosk \
    --incognito \
    --disable-translate \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-features=TranslateUI \
    --disk-cache-dir=/dev/null \
    --password-store=basic \
    "file://$DASHBOARD_DIR/dashboard.html" \
    >> "$LOG_FILE" 2>&1

echo "$(date): Dashboard closed" >> "$LOG_FILE"
