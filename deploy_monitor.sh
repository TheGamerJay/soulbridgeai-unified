#!/bin/bash
# Deploy SoulBridge AI Monitoring System

echo "🚀 Deploying SoulBridge AI Monitoring System..."

# Create monitoring directory
sudo mkdir -p /opt/soulbridge-monitor
cd /opt/soulbridge-monitor

# Install Python dependencies
echo "📦 Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv monitor_env
source monitor_env/bin/activate
pip install requests openai python-dotenv

# Download monitoring script
echo "📥 Setting up monitoring script..."
wget https://raw.githubusercontent.com/TheGamerJay/soulbridgeai-unified/main/maintenance_resend.py
chmod +x maintenance_resend.py

# Install Railway CLI
echo "🚄 Installing Railway CLI..."
curl -fsSL https://railway.app/install.sh | sh
echo 'export PATH="$PATH:/root/.railway/bin"' >> ~/.bashrc

# Create systemd service
echo "⚙️ Creating system service..."
sudo tee /etc/systemd/system/soulbridge-monitor.service > /dev/null << 'EOF'
[Unit]
Description=SoulBridge AI Monitoring System
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=30
User=root
WorkingDirectory=/opt/soulbridge-monitor
Environment=PATH=/opt/soulbridge-monitor/monitor_env/bin:/root/.railway/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/soulbridge-monitor/monitor_env/bin/python maintenance_resend.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set up environment variables
echo "🔧 Don't forget to:"
echo "1. Copy your .env.monitoring file to /opt/soulbridge-monitor/.env"
echo "2. Run: railway login"
echo "3. Run: railway link (select your project)"
echo "4. Start the service: sudo systemctl start soulbridge-monitor"
echo "5. Enable auto-start: sudo systemctl enable soulbridge-monitor"

echo "✅ Setup complete! Edit the .env file and start the service."