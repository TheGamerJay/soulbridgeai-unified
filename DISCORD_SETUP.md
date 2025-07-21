# Discord Webhook Setup for SoulBridge AI Monitoring

## 🎯 Quick Setup:

1. **Create a Discord Server** (if you don't have one)
   - Name it "SoulBridge AI Operations" or similar

2. **Create a Channel for Alerts**
   - Name it `#soulbridge-alerts` or `#monitoring`

3. **Create Webhook:**
   - Right-click the channel → "Edit Channel"
   - Go to "Integrations" → "Webhooks"
   - Click "Create Webhook"
   - Name it "SoulBridge Monitor"
   - Copy the webhook URL

4. **Test the Webhook:**
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "🤖 SoulBridge AI Monitor Test - Setup Complete!"}'
```

## 📱 Pro Tips:

- **Create separate channels** for different alert types:
  - `#health-alerts` - Uptime issues
  - `#error-logs` - Application errors  
  - `#performance` - Performance metrics

- **Set up role mentions** for critical alerts:
  - Create `@soulbridge-admin` role
  - Modify monitor to ping role for CRITICAL alerts

- **Mobile notifications:**
  - Install Discord mobile app
  - Enable push notifications for the server

## 🔔 Example Alert Types You'll Receive:

✅ **Healthy Status**: "Site is operational - all services running"
⚠️ **Warning**: "High response time detected - monitoring..."  
❌ **Critical**: "Site down - auto-restart initiated"
🤖 **AI Analysis**: "GPT-4 detected database connection timeout..."
🔄 **Recovery**: "Site back online after 3 minutes downtime"

Your webhook URL should look like:
`https://discord.com/api/webhooks/123456789/abcdef123456789`