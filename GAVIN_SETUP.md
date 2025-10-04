# Setup Instructions for Gavin (Server Admin)

Hey Gavin! This is the CFL Member Dashboard that needs to be set up on the `tunr` server (142.44.212.80).

## What This Does

Automatically downloads Zeffy payment data every 6 hours and displays a live dashboard showing:
- Active members, new members, recently quit members
- Revenue stats and projections
- Volunteer list

The dashboard will be hosted at **http://chicofl.org/dashboard.html** for the Raspberry Pi to display.

## Server Setup (15 minutes)

SSH into the server as root or a user with sudo:

```bash
ssh erinb@142.44.212.80
# or
ssh root@142.44.212.80
```

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip nginx git
```

### 2. Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/erinb-maker-radio/cfl-member-dashboard.git
cd cfl-member-dashboard
sudo chown -R erinb:erinb .  # Give erinb ownership
```

### 3. Install Python Packages

```bash
pip3 install playwright pandas openpyxl python-dotenv
playwright install chromium
sudo playwright install-deps
```

### 4. Configure Zeffy Credentials

Create `.env` file:
```bash
nano .env
```

Add (ask Erin for the actual credentials):
```
ZEFFY_EMAIL=your-zeffy-email@example.com
ZEFFY_PASSWORD=your-zeffy-password
```

Save: `Ctrl+X`, `Y`, `Enter`

### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/cfl-dashboard
```

Paste this:
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name chicofl.org www.chicofl.org _;

    root /var/www/cfl-member-dashboard;
    index dashboard.html;

    location / {
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|webp)$ {
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Prevent access to sensitive files
    location ~ /\.(env|git) {
        deny all;
        return 404;
    }

    location ~ \.(py|sh)$ {
        deny all;
        return 404;
    }
}
```

Enable and restart:
```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/cfl-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Set Up Auto-Updates

Create update script:
```bash
nano /var/www/cfl-member-dashboard/update_dashboard.sh
```

Paste:
```bash
#!/bin/bash
cd /var/www/cfl-member-dashboard
python3 zeffy_export.py >> /var/log/cfl-dashboard.log 2>&1
python3 analyze_members.py >> /var/log/cfl-dashboard.log 2>&1
echo "$(date): Dashboard updated" >> /var/log/cfl-dashboard.log
```

Make executable and create log:
```bash
chmod +x /var/www/cfl-member-dashboard/update_dashboard.sh
sudo touch /var/log/cfl-dashboard.log
sudo chown erinb:erinb /var/log/cfl-dashboard.log
```

Add cron job (runs every 6 hours):
```bash
crontab -e
```

Add this line:
```
0 */6 * * * /var/www/cfl-member-dashboard/update_dashboard.sh
```

### 7. Initial Data Load

```bash
cd /var/www/cfl-member-dashboard
python3 zeffy_export.py
python3 analyze_members.py
```

If successful, you'll see a `dashboard_data.json` file created.

### 8. Test Dashboard

Open in browser:
- http://142.44.212.80/dashboard.html
- http://chicofl.org/dashboard.html

You should see the dashboard with member stats!

## Troubleshooting

### Check Nginx Status
```bash
sudo systemctl status nginx
sudo nginx -t  # Test config
```

### View Logs
```bash
# Dashboard logs
tail -f /var/log/cfl-dashboard.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Manual Data Refresh
```bash
cd /var/www/cfl-member-dashboard
./update_dashboard.sh
```

### Check Cron Jobs
```bash
crontab -l  # List cron jobs
```

## What Erin Needs to Know

Once setup is complete, tell Erin the dashboard URL:
- **http://chicofl.org/dashboard.html**

She'll use this URL to configure the Raspberry Pi kiosk display.

## Maintenance

### Update Code
```bash
cd /var/www/cfl-member-dashboard
git pull
sudo systemctl restart nginx
```

### Change Zeffy Credentials
```bash
nano /var/www/cfl-member-dashboard/.env
```

## Questions?

Contact Erin or check the full documentation in `README.md` and `QUICKSTART.md`.
