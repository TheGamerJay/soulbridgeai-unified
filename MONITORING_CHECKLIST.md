# 🚀 SoulBridge AI Monitoring Deployment Checklist

## ✅ Pre-Deployment Setup:

### **Environment Variables** (Get these ready):
- [ ] **Railway API Token** - From Railway dashboard → Settings → Tokens
- [ ] **Discord Webhook URL** - See DISCORD_SETUP.md
- [ ] **OpenAI API Key** - From platform.openai.com → API Keys
- [ ] **Site Health URL** - Currently: `https://soulbridgeai-unified-production.up.railway.app/health`

### **VPS/Server Setup**:
- [ ] Choose hosting platform (DigitalOcean, Linode, AWS EC2, etc.)
- [ ] Ubuntu 20.04+ recommended
- [ ] At least 1GB RAM, 1 CPU core
- [ ] SSH access configured

## 🛠️ Deployment Steps:

### **1. Server Preparation:**
```bash
# Connect to your VPS
ssh root@your-server-ip

# Run the deployment script
curl -fsSL https://raw.githubusercontent.com/TheGamerJay/soulbridgeai-unified/main/deploy_monitor.sh | bash
```

### **2. Configuration:**
```bash
# Navigate to monitoring directory
cd /opt/soulbridge-monitor

# Create environment file
nano .env
# Paste your environment variables here

# Login to Railway
railway login
# Follow the browser authentication

# Link to your project
railway link
# Select "soulbridgeai-unified"
```

### **3. Test & Start:**
```bash
# Test the script manually first
source monitor_env/bin/activate
python maintenance_improved.py
# Should send a "Monitor Started" message to Discord

# If working, set up as service
sudo systemctl start soulbridge-monitor
sudo systemctl enable soulbridge-monitor
sudo systemctl status soulbridge-monitor
```

### **4. Verification:**
- [ ] Discord message received: "Monitor Started"
- [ ] Health check shows ✅ "Site is healthy"
- [ ] Railway CLI can access your project
- [ ] Service starts automatically after server reboot

## 📊 Monitoring the Monitor:

### **Check Service Status:**
```bash
sudo systemctl status soulbridge-monitor
sudo journalctl -u soulbridge-monitor -f
```

### **Update the Monitor:**
```bash
cd /opt/soulbridge-monitor
wget -O maintenance_improved.py https://raw.githubusercontent.com/TheGamerJay/soulbridgeai-unified/main/maintenance_improved.py
sudo systemctl restart soulbridge-monitor
```

## 🚨 Emergency Commands:

### **Stop Monitoring:**
```bash
sudo systemctl stop soulbridge-monitor
```

### **Restart Monitoring:**
```bash
sudo systemctl restart soulbridge-monitor
```

### **View Live Logs:**
```bash
sudo journalctl -u soulbridge-monitor -f
```

## 📱 What to Expect:

**Within 30 minutes**: First health check message
**If site goes down**: Auto-restart attempt + GPT analysis
**Complex issues**: Alert with "Manual intervention needed"
**Recovery**: Confirmation message when site is back

## 🤝 When to Tag Claude:

The monitor will send alerts, but tag me (@Claude) when you see:
- Multiple restart failures
- Unusual error patterns in GPT analysis
- Performance degradation warnings
- Database or service dependency issues

I'll jump in immediately for deep analysis and permanent fixes! 🧠⚡