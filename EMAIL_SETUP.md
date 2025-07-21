# 📧 Resend Email Setup for SoulBridge AI Monitoring

## 🎯 Why Resend over Discord:

✅ **Professional**: Clean email alerts vs. Discord pings
✅ **Reliable**: Email infrastructure is more stable
✅ **Accessible**: Check alerts from any email client  
✅ **Already Configured**: You have the API key set up
✅ **Rich Formatting**: Beautiful HTML alerts with stats
✅ **Archive**: Email history of all alerts automatically saved

## 🚀 Setup Steps:

### **1. Verify Resend Domain (Already Done)**
Your Resend account should already have a verified domain for sending.

### **2. Configure Environment Variables:**
```bash
# Your monitoring server .env file
RESEND_API_KEY=re_atdLxCys_5xcKG6NvWCQ1vfXfhpJUvnR5
MONITOR_FROM_EMAIL=monitor@soulbridgeai.com
MONITOR_TO_EMAIL=soulbridgeai.contact@gmail.com
OPENAI_API_KEY=your_openai_api_key_here
RAILWAY_API_TOKEN=your_railway_token_here
```

### **3. Test Email Setup:**
```bash
# Test Resend API manually
curl -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer re_atdLxCys_5xcKG6NvWCQ1vfXfhpJUvnR5" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "SoulBridge AI Monitor <monitor@soulbridgeai.com>",
    "to": ["soulbridgeai.contact@gmail.com"],
    "subject": "🤖 Monitor Test - Setup Complete!",
    "text": "SoulBridge AI monitoring system is ready!"
  }'
```

## 📨 Email Alert Types You'll Receive:

### **🟢 INFO Alerts:**
- ✅ "Monitoring System Started"
- ✅ "Site Recovery Confirmed" 
- ✅ "Daily Status Report" (every 24 hours)

### **🟡 MEDIUM Alerts:**
- ⚠️ "Site Health Check Failed" (first failure)
- ⚠️ "Continued Health Check Failures"
- ⚠️ "Monitor System Error"

### **🟠 HIGH Alerts:**
- 🔄 "Auto-Restart Initiated"
- 🔄 "Restart Complete - Analysis Report"

### **🔴 CRITICAL Alerts:**
- ❌ "Restart Failed - Manual Intervention Required"
- ❌ "Multiple System Failures"

## 📋 Professional Email Features:

**Beautiful HTML Design:**
- SoulBridge AI branded header
- Color-coded severity levels  
- Real-time statistics dashboard
- Clean, readable formatting

**Comprehensive Information:**
- Timestamp and severity level
- Detailed error descriptions
- GPT-4 AI analysis of issues
- Recent log excerpts
- Monitor uptime and statistics

**Smart Filtering:**
- Quiet hours (11PM-7AM) respect
- Severity-based filtering
- Consolidated reports to avoid spam

## 🔄 Integration with Claude:

**Email alerts will include:**
- "For complex issues, please involve Claude for deep analysis"
- Clear indicators when manual intervention is needed
- Context for you to easily share with Claude

**When to tag Claude:**
- CRITICAL severity emails
- Multiple restart failures
- Unusual GPT analysis patterns
- "Manual intervention required" messages

## 📱 Mobile Setup:

**Gmail Mobile App:**
1. Enable push notifications for monitor emails
2. Create filter to star/highlight SoulBridge alerts
3. Set up VIP notifications for CRITICAL alerts

**iPhone Mail:**
1. Add soulbridgeai.contact@gmail.com to VIP list
2. Enable VIP notifications 

## 🎨 Sample Email Preview:

```
Subject: [HIGH] SoulBridge AI: Auto-Restart Initiated

🟠 SoulBridge AI Monitor
Auto-Restart Initiated

Timestamp: 2025-07-21 16:30:00 UTC
Severity: HIGH

🔄 Initiating automatic restart after 3 consecutive failures

Error: Connection failed: Connection timeout

Restart process starting now...

Statistics:
- Monitor Uptime: 24h 15m
- Total Checks: 48  
- Total Failures: 3
- Consecutive Failures: 3

---
SoulBridge AI Automated Monitoring System
Check interval: 30 minutes
```

Professional, informative, and actionable! 🚀