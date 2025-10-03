#!/bin/bash
# CFL Dashboard - Cloud Server Setup Script
# Run this on your cloud server after cloning the repository

set -e  # Exit on error

echo "========================================="
echo "CFL Dashboard - Server Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "Please do not run as root. Run as regular user with sudo privileges."
   exit 1
fi

# Get current directory
INSTALL_DIR=$(pwd)
echo "Installing to: $INSTALL_DIR"
echo ""

# Update system
echo "Step 1: Updating system..."
sudo apt update

# Install Python and dependencies
echo ""
echo "Step 2: Installing Python and system dependencies..."
sudo apt install -y python3 python3-pip nginx

# Install Python packages
echo ""
echo "Step 3: Installing Python packages..."
pip3 install playwright pandas openpyxl python-dotenv

# Install Playwright browser
echo ""
echo "Step 4: Installing Playwright Chromium browser..."
playwright install chromium
playwright install-deps

# Configure credentials
echo ""
echo "Step 5: Configure Zeffy credentials..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please edit it with your credentials:"
    echo "  nano .env"
    echo ""
    read -p "Enter Zeffy email: " ZEFFY_EMAIL
    read -s -p "Enter Zeffy password: " ZEFFY_PASSWORD
    echo ""

    cat > .env << EOF
ZEFFY_EMAIL=$ZEFFY_EMAIL
ZEFFY_PASSWORD=$ZEFFY_PASSWORD
EOF

    echo "Credentials saved to .env"
else
    echo ".env file already exists, skipping..."
fi

# Set up Nginx
echo ""
echo "Step 6: Configuring Nginx..."
DOMAIN="chicofl.org"
SERVER_NAME="_"  # Accept any domain/IP

sudo tee /etc/nginx/sites-available/cfl-dashboard > /dev/null << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name $DOMAIN www.$DOMAIN _;

    root $INSTALL_DIR;
    index dashboard.html;

    location / {
        try_files \$uri \$uri/ =404;
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
EOF

# Disable default site and enable dashboard
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/cfl-dashboard /etc/nginx/sites-enabled/

# Test and restart Nginx
echo "Testing Nginx configuration..."
sudo nginx -t

echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# Set up update script
echo ""
echo "Step 7: Creating update script..."
cat > $INSTALL_DIR/update_dashboard.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
LOG_FILE="/var/log/cfl-dashboard.log"

echo "$(date): Starting dashboard update..." >> "$LOG_FILE"

# Run Zeffy export
python3 zeffy_export.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): Zeffy export successful" >> "$LOG_FILE"

    # Process data
    python3 analyze_members.py >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "$(date): Dashboard update completed successfully" >> "$LOG_FILE"
    else
        echo "$(date): ERROR - analyze_members.py failed" >> "$LOG_FILE"
    fi
else
    echo "$(date): ERROR - zeffy_export.py failed" >> "$LOG_FILE"
fi
EOF

chmod +x $INSTALL_DIR/update_dashboard.sh

# Create log file
sudo touch /var/log/cfl-dashboard.log
sudo chown $USER:$USER /var/log/cfl-dashboard.log

# Set up cron job
echo ""
echo "Step 8: Setting up cron job (runs every 6 hours)..."
CRON_CMD="0 */6 * * * $INSTALL_DIR/update_dashboard.sh"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -v "update_dashboard.sh"; echo "$CRON_CMD") | crontab -

echo "Cron job added successfully"

# Run initial data collection
echo ""
echo "Step 9: Running initial data collection..."
echo "This may take a minute..."

python3 zeffy_export.py
if [ $? -eq 0 ]; then
    echo "Zeffy export successful!"
    python3 analyze_members.py
    if [ $? -eq 0 ]; then
        echo "Data analysis successful!"
    else
        echo "WARNING: analyze_members.py failed. Check logs."
    fi
else
    echo "WARNING: zeffy_export.py failed. Check credentials in .env"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Dashboard URL: http://$SERVER_IP/dashboard.html"
echo "              http://chicofl.org/dashboard.html"
echo ""
echo "Next steps:"
echo "1. Test the dashboard URL in your browser"
echo "2. Update Pi kiosk mode with the URL above"
echo "3. Monitor logs: tail -f /var/log/cfl-dashboard.log"
echo ""
echo "Data updates automatically every 6 hours via cron"
echo "Manual update: $INSTALL_DIR/update_dashboard.sh"
echo ""
