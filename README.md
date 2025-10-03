# CFL Member Dashboard

A real-time membership dashboard for Chico Fab Lab that displays active members, new members, recently quit members, and financial statistics. Designed to run on a cloud server with display on a Raspberry Pi in kiosk mode.

![CFL Logo](cfl-logo.webp)

## Features

- 📊 **Real-time Membership Stats**: Active members (ongoing vs total), new members, recently quit
- 💰 **Financial Overview**: Revenue by membership type, monthly revenue, projected annual revenue
- 👥 **Member Lists**: Auto-adjusting columns with first name + last initial for privacy
- 🎨 **Retro Design**: CFL-branded color scheme (teal, yellow, pink)
- 🔄 **Auto-refresh**: Dashboard updates every 5 minutes
- 📱 **Responsive Layout**: No scrolling, optimized for full-screen display

## Architecture

### Cloud Server (Does the work)
- Runs Playwright script to download Zeffy payment data
- Processes CSV and generates dashboard data
- Hosts dashboard HTML via web server
- Cron job updates data every 6 hours

### Raspberry Pi (Display only)
- Chromium browser in kiosk mode
- Displays cloud-hosted dashboard URL
- No data processing, just rendering

## Cloud Server Setup

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install -y python3 python3-pip

# Install Python dependencies
pip3 install playwright pandas openpyxl python-dotenv

# Install Playwright browser
playwright install chromium
playwright install-deps
```

### 2. Clone Repository

```bash
cd /var/www  # Or your preferred web directory
git clone <repository-url> cfl-dashboard
cd cfl-dashboard
```

### 3. Configure Credentials

```bash
# Copy example env file
cp .env.example .env

# Edit with your Zeffy credentials
nano .env
```

Add your Zeffy login:
```
ZEFFY_EMAIL=your-email@example.com
ZEFFY_PASSWORD=your-password
```

### 4. Set Up Web Server

#### Option A: Nginx (Recommended)

```bash
# Install Nginx
sudo apt install nginx

# Create config file
sudo nano /etc/nginx/sites-available/cfl-dashboard
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or server IP

    root /var/www/cfl-dashboard;
    index dashboard.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|webp)$ {
        expires 1h;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/cfl-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Option B: Apache

```bash
# Install Apache
sudo apt install apache2

# Create config
sudo nano /etc/apache2/sites-available/cfl-dashboard.conf
```

Add:
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/cfl-dashboard

    <Directory /var/www/cfl-dashboard>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

Enable and start:
```bash
sudo a2ensite cfl-dashboard
sudo systemctl restart apache2
```

### 5. Set Up Automatic Data Updates

Create update script:
```bash
nano /var/www/cfl-dashboard/update_dashboard.sh
```

Add:
```bash
#!/bin/bash
cd /var/www/cfl-dashboard

# Run Zeffy export
python3 zeffy_export.py >> /var/log/cfl-dashboard.log 2>&1

# Process data
python3 analyze_members.py >> /var/log/cfl-dashboard.log 2>&1

echo "$(date): Dashboard updated" >> /var/log/cfl-dashboard.log
```

Make executable:
```bash
chmod +x /var/www/cfl-dashboard/update_dashboard.sh
```

Add to crontab (runs every 6 hours):
```bash
crontab -e
```

Add this line:
```
0 */6 * * * /var/www/cfl-dashboard/update_dashboard.sh
```

### 6. Initial Data Load

```bash
cd /var/www/cfl-dashboard
python3 zeffy_export.py
python3 analyze_members.py
```

### 7. Test Dashboard

Open in browser: `http://your-server-ip/dashboard.html`

## Raspberry Pi Setup

### 1. Flash SD Card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

1. Choose OS: **Raspberry Pi OS (32-bit)** for Pi 3B
2. Click ⚙️ settings icon:
   - ✅ Enable SSH
   - Username: `pi`
   - Password: `dashboard123` (or your choice)
   - ✅ Configure WiFi (SSID, password, country)
   - Set locale/timezone
3. Write to SD card

### 2. Boot and Connect

```bash
# Find Pi on network
ping raspberrypi.local

# Or find IP manually and SSH
ssh pi@<pi-ip-address>
```

### 3. Install Kiosk Mode

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y chromium-browser unclutter xdotool

# Disable screen blanking
sudo nano /etc/lightdm/lightdm.conf
```

Add under `[Seat:*]`:
```
xserver-command=X -s 0 -dpms
```

### 4. Configure Auto-Start

```bash
# Create autostart directory
mkdir -p ~/.config/lxsession/LXDE-pi

# Create autostart file
nano ~/.config/lxsession/LXDE-pi/autostart
```

Add:
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.5 -root
@chromium-browser --noerrdialogs --disable-infobars --kiosk --incognito http://YOUR-SERVER-IP/dashboard.html
```

**Replace `YOUR-SERVER-IP` with your cloud server's IP or domain!**

### 5. Enable Auto-Login

```bash
sudo raspi-config
```

Navigate to: `System Options` → `Boot / Auto Login` → `Desktop Autologin`

### 6. Reboot

```bash
sudo reboot
```

Dashboard should launch automatically in full-screen!

## File Structure

```
cfl-dashboard/
├── dashboard.html          # Main dashboard display
├── cfl-logo.webp          # CFL logo
├── zeffy_export.py        # Playwright script to download Zeffy data
├── analyze_members.py     # Process CSV and generate dashboard data
├── .env.example           # Example credentials file
├── .env                   # Your actual credentials (gitignored)
├── dashboard_data.json    # Generated dashboard data (gitignored)
├── README.md              # This file
├── RASPBERRY_PI_SETUP.md  # Detailed Pi setup guide
├── start_dashboard.sh     # Pi startup script (optional)
└── update_data.sh         # Data update script (optional)
```

## How It Works

### Data Flow

1. **Zeffy Export** (`zeffy_export.py`):
   - Logs into Zeffy using Playwright
   - Exports payment data as CSV
   - Saves to local directory

2. **Data Analysis** (`analyze_members.py`):
   - Reads CSV file
   - Filters for membership payments (Basic, Pro, Volunteer)
   - Calculates active members, new members, quit members
   - Generates financial statistics
   - Outputs `dashboard_data.json`

3. **Dashboard Display** (`dashboard.html`):
   - Loads `dashboard_data.json`
   - Renders charts using Chart.js
   - Auto-refreshes every 5 minutes
   - Responsive layout adjusts columns based on member count

### Membership Logic

- **Active Members**: Payments in last 60 days
  - Ongoing: Currently active recurring payments
  - Cancelled: Stopped recurring but still within 60 days
- **New Members**: First payment within last 60 days
- **Recently Quit**: Last payment 60-120 days ago
- **Volunteers**: Separate list, excludes stopped recurring

### Name Privacy

All names displayed as "First Name + Last Initial" (e.g., "John S.")

## Customization

### Update Refresh Interval

Edit `dashboard.html`, line ~500:
```javascript
setInterval(loadData, 300000); // 300000ms = 5 minutes
```

### Change Color Scheme

Edit CSS variables in `dashboard.html`:
```css
:root {
    --cfl-teal: #1a9b94;
    --cfl-yellow: #ffd43b;
    --cfl-pink: #ff6b9d;
}
```

### Adjust Auto-Refresh Schedule

Edit crontab:
```bash
crontab -e

# Change from every 6 hours to every 4 hours:
0 */4 * * * /var/www/cfl-dashboard/update_dashboard.sh
```

## Troubleshooting

### Dashboard Not Loading on Pi

1. Check Pi can reach server: `ping YOUR-SERVER-IP`
2. Test URL in browser on another device
3. Check Chromium autostart: `cat ~/.config/lxsession/LXDE-pi/autostart`

### Data Not Updating

1. Check cron logs: `tail -f /var/log/cfl-dashboard.log`
2. Test scripts manually:
   ```bash
   cd /var/www/cfl-dashboard
   python3 zeffy_export.py
   python3 analyze_members.py
   ```
3. Verify Playwright: `playwright install chromium`

### Zeffy Login Fails

1. Check credentials in `.env`
2. Update Playwright: `pip3 install --upgrade playwright`
3. Check Zeffy selectors (may change with updates)

### Screen Goes Blank on Pi

1. Verify DPMS disabled: `xset q`
2. Check autostart has screen-off commands
3. Edit `/boot/config.txt`: Add `hdmi_blanking=1`

## Maintenance

### Update Dashboard Code

```bash
cd /var/www/cfl-dashboard
git pull
sudo systemctl restart nginx  # or apache2
```

### View Logs

```bash
# Server logs
tail -f /var/log/cfl-dashboard.log

# Nginx logs
tail -f /var/log/nginx/error.log

# Apache logs
tail -f /var/log/apache2/error.log
```

### Manual Data Refresh

```bash
ssh your-server
cd /var/www/cfl-dashboard
./update_dashboard.sh
```

## Security Notes

- **Never commit `.env` file** (contains credentials)
- Change default Pi password: `passwd`
- Consider HTTPS for production (use Let's Encrypt)
- Restrict server access with firewall
- Keep system updated: `sudo apt update && sudo apt upgrade`

## Requirements

### Cloud Server
- Ubuntu/Debian Linux
- Python 3.7+
- Nginx or Apache
- 1GB RAM minimum
- Internet access

### Raspberry Pi
- Pi 3 Model B or newer
- Raspberry Pi OS (32-bit for Pi 3)
- 16GB+ SD card
- HDMI display
- Network connection

## License

This project is for internal use by Chico Fab Lab.

## Support

For issues or questions, contact the CFL technical team.
