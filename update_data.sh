#!/bin/bash
# Data Update Script for Raspberry Pi
# Run this via cron every 6 hours

DASHBOARD_DIR="/home/pi/CFL_Dashboard"
LOG_FILE="/home/pi/dashboard.log"

echo "$(date): Starting data update..." >> "$LOG_FILE"

cd "$DASHBOARD_DIR"

# Run the analysis script
python3 analyze_members.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): Data update successful" >> "$LOG_FILE"
else
    echo "$(date): Data update FAILED" >> "$LOG_FILE"
fi

# Optional: Force Chromium refresh (not needed due to auto-refresh in HTML)
# pkill -USR1 chromium
