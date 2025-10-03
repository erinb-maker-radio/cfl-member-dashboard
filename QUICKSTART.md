# Quick Start Guide

## Server Setup (5 minutes)

### 1. SSH into your server
```bash
ssh erinb@142.44.212.80
# Password: xzf222#lol1!
```

### 2. Clone the repository
```bash
cd /var/www
sudo git clone <GITHUB_REPO_URL> cfl-dashboard
cd cfl-dashboard
sudo chown -R erinb:erinb .
```

### 3. Run the setup script
```bash
./server_setup.sh
```

This script will:
- Install Python, Nginx, and all dependencies
- Configure Nginx web server
- Prompt for Zeffy credentials
- Set up automatic updates (cron job every 6 hours)
- Run initial data collection
- Display the dashboard URL

### 4. Access your dashboard
Open in browser:
- **http://142.44.212.80/dashboard.html**
- **http://chicofl.org/dashboard.html** (if domain is configured)

---

## Raspberry Pi Setup (10 minutes)

### 1. Flash SD card
- Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- Choose OS: **Raspberry Pi OS (32-bit)** (for Pi 3B)
- Click ⚙️ settings:
  - ✅ Enable SSH
  - Username: `pi`
  - Password: `dashboard123`
  - ✅ Configure WiFi (your network SSID/password)
  - Set timezone
- Write to SD card

### 2. Boot and find IP
- Insert SD card into Pi
- Power on
- Wait 1-2 minutes for boot
- Find IP address:
  ```bash
  # From your computer
  ping raspberrypi.local
  # Or check your router's admin page
  ```

### 3. Connect via SSH
```bash
ssh pi@<PI_IP_ADDRESS>
# Password: dashboard123
```

### 4. Install kiosk mode
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install packages
sudo apt install -y chromium-browser unclutter xdotool

# Create autostart directory
mkdir -p ~/.config/lxsession/LXDE-pi

# Create autostart file
nano ~/.config/lxsession/LXDE-pi/autostart
```

Paste this (replace with your server URL):
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.5 -root
@chromium-browser --noerrdialogs --disable-infobars --kiosk --incognito http://chicofl.org/dashboard.html
```

Save: `Ctrl+X`, `Y`, `Enter`

### 5. Enable auto-login
```bash
sudo raspi-config
```
Navigate: `System Options` → `Boot / Auto Login` → `Desktop Autologin`

### 6. Disable screen blanking
```bash
sudo nano /etc/lightdm/lightdm.conf
```

Add under `[Seat:*]`:
```
xserver-command=X -s 0 -dpms
```

### 7. Reboot
```bash
sudo reboot
```

Dashboard should auto-launch in full-screen!

---

## Troubleshooting

### Dashboard not loading
```bash
# Check Nginx status
sudo systemctl status nginx

# Check logs
tail -f /var/log/cfl-dashboard.log
tail -f /var/log/nginx/error.log
```

### Data not updating
```bash
# Run update manually
cd /var/www/cfl-dashboard
./update_dashboard.sh

# Check cron
crontab -l
```

### Pi screen blank
```bash
# Check screen saver
xset q

# Restart Pi
sudo reboot
```

---

## Maintenance

### Update dashboard code
```bash
ssh erinb@142.44.212.80
cd /var/www/cfl-dashboard
git pull
sudo systemctl restart nginx
```

### View logs
```bash
# Dashboard logs
tail -f /var/log/cfl-dashboard.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Manual data refresh
```bash
cd /var/www/cfl-dashboard
./update_dashboard.sh
```

---

## URLs

- **Dashboard**: http://chicofl.org/dashboard.html
- **Server**: 142.44.212.80
- **Domain**: chicofl.org

## Credentials

### Server SSH
- User: `erinb`
- Host: `142.44.212.80`
- Password: `xzf222#lol1!`

### Raspberry Pi SSH
- User: `pi`
- Password: `dashboard123`
- Find IP: `ping raspberrypi.local` or check router

### Zeffy
- Email: (stored in server `.env` file)
- Password: (stored in server `.env` file)
