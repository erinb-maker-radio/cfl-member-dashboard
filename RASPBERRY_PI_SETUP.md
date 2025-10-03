# Raspberry Pi Dashboard Setup Guide

## Hardware Requirements
- Raspberry Pi (3B+ or newer recommended)
- MicroSD card (16GB+)
- Flatscreen display with HDMI
- Power supply
- Internet connection (WiFi or Ethernet)

## Software Installation

### 1. Initial Raspberry Pi Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip chromium-browser unclutter xdotool

# Install Python dependencies
pip3 install pandas openpyxl python-dotenv
```

### 2. Install Dashboard Files
```bash
# Create dashboard directory
mkdir -p ~/CFL_Dashboard
cd ~/CFL_Dashboard

# Copy these files to the Pi:
# - dashboard.html
# - cfl-logo.webp
# - analyze_members.py
# - .env (with your Zeffy credentials)
# - dashboard_data.json (initial data)
```

### 3. Set Up Auto-Start Chromium in Kiosk Mode

Create autostart file:
```bash
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Add these lines:
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.5 -root
@chromium-browser --noerrdialogs --disable-infobars --kiosk file:///home/pi/CFL_Dashboard/dashboard.html
```

### 4. Set Up Automatic Data Refresh

Create cron job to update data every 6 hours:
```bash
crontab -e
```

Add this line:
```
0 */6 * * * cd /home/pi/CFL_Dashboard && python3 analyze_members.py >> /home/pi/dashboard.log 2>&1
```

### 5. Configure Display Settings

Edit config.txt for display:
```bash
sudo nano /boot/config.txt
```

Add/modify these settings:
```
# Disable screen blanking
hdmi_blanking=1

# Force HDMI output
hdmi_force_hotplug=1

# Set resolution (adjust for your display)
hdmi_group=2
hdmi_mode=82  # 1920x1080 @ 60Hz

# Disable overscan if edges are cut off
disable_overscan=1
```

### 6. Auto-Login to Desktop

Enable auto-login:
```bash
sudo raspi-config
```

Navigate to: `System Options` → `Boot / Auto Login` → `Desktop Autologin`

### 7. Reboot
```bash
sudo reboot
```

## File Transfer Options

### Option A: USB Drive
1. Copy files to USB drive from Windows
2. Insert USB into Pi
3. Copy files: `cp /media/pi/USB/* ~/CFL_Dashboard/`

### Option B: SCP (Secure Copy)
```bash
# From Windows (in PowerShell):
scp dashboard.html pi@raspberrypi.local:~/CFL_Dashboard/
scp cfl-logo.webp pi@raspberrypi.local:~/CFL_Dashboard/
scp analyze_members.py pi@raspberrypi.local:~/CFL_Dashboard/
scp .env pi@raspberrypi.local:~/CFL_Dashboard/
```

### Option C: Git Clone
```bash
# If you have files in a git repository
cd ~/CFL_Dashboard
git clone <your-repo-url> .
```

## Updating Data Source

You have two options for getting Zeffy export data:

### Option 1: Run Export Script on Pi
Install Playwright on Pi (requires more resources):
```bash
pip3 install playwright
playwright install chromium
python3 zeffy_export.py
```

### Option 2: Sync from Windows PC (Recommended)
Run export on Windows, then sync the CSV file to Pi:
```bash
# From Windows:
scp "C:\Users\erin\Zeffy_Exports\zeffy-payments-*.csv" pi@raspberrypi.local:~/CFL_Dashboard/
```

Then run analyze script on Pi:
```bash
ssh pi@raspberrypi.local
cd ~/CFL_Dashboard
python3 analyze_members.py
```

## Troubleshooting

### Display not showing
- Check HDMI cable connection
- Verify display is on correct input
- Check `/boot/config.txt` settings

### Dashboard not loading
- Verify file paths in autostart
- Check Chromium is installed: `which chromium-browser`
- Test manually: Open file manager, double-click `dashboard.html`

### Data not updating
- Check cron logs: `cat ~/dashboard.log`
- Verify Python dependencies: `pip3 list | grep pandas`
- Check .env file has correct credentials

### Screen goes blank
- Verify screen saver disabled in autostart
- Check DPMS settings: `xset q`

## Maintenance

### Refresh dashboard manually
```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Update data
cd ~/CFL_Dashboard
python3 analyze_members.py

# Restart Chromium (dashboard will auto-refresh every 5 min anyway)
pkill chromium
```

### View logs
```bash
tail -f ~/dashboard.log
```

### Update dashboard files
```bash
# Copy new files from USB or SCP
# Dashboard will refresh automatically within 5 minutes
```

## Power Management

For 24/7 display:
- Use official Raspberry Pi power supply (3A recommended)
- Consider UPS/battery backup
- Monitor temperature: `vcgencmd measure_temp`

## Network Setup

### WiFi Configuration
```bash
sudo raspi-config
# Navigate to: System Options → Wireless LAN
```

### Static IP (optional)
Edit dhcpcd.conf:
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

## Security Notes

- Change default password: `passwd`
- Keep system updated: `sudo apt update && sudo apt upgrade`
- Consider firewall: `sudo apt install ufw`
- Disable SSH if not needed: `sudo systemctl disable ssh`
