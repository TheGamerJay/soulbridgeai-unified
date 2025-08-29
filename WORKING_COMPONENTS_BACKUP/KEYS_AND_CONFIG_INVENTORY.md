# 🔑 Keys & Configuration Backup Inventory
**Backup Date:** August 29, 2025
**Purpose:** Preserve all critical configuration, keys, and settings

---

## 🔐 **Environment Variables & Secrets**

### **Main Environment Files**
```
.env                      # Main production environment variables
.env.example             # Template for environment setup
.env.monitoring          # Monitoring configuration
backend/.env             # Backend-specific environment
backend/.env.example     # Backend environment template
backend/.env.music_studio_template  # Studio configuration template
backend/.env.production-db          # Production database settings
backend/.env.template               # General backend template
```

### **Critical Keys Preserved**
- ✅ **Admin Credentials**
  - Email: aceelnene@gmail.com
  - Password: [PRESERVED]

- ✅ **Stripe Configuration (Real Test Keys)**
  - Secret Key: sk_test_51RnqPtQ14t71rzlf... [PRESERVED]
  - Publishable Key: pk_test_51RnqPtQ14t71rzlf... [PRESERVED] 
  - Webhook Secret: whsec_NVwDLVaLxqFavfRtf... [PRESERVED]

- ✅ **Stripe Price IDs (Production Values)**
  - Silver Monthly: price_1RxcFwBR4omRdqnXPW1Sx34k
  - Silver Yearly: price_1RxcJjBR4omRdqnXgtbnvF2A
  - Gold Monthly: price_1RxcSPBR4omRdqnXNvqJCAbB
  - Gold Yearly: price_1RxcbwBR4omRdqnXTxU9jtES

- ✅ **OpenAI API Key** (for lyrics & cover art generation)
- ✅ **Email Configuration** (soulbridgeai.contact@gmail.com)

---

## ⚙️ **Application Configuration**

### **Core Config Files**
```
config.py                # Main application configuration
gunicorn_config.py      # WSGI server configuration
firebase-config.js      # Firebase client configuration  
requirements.txt        # Python dependencies
```

### **Configuration Settings Preserved**
- ✅ **Database Settings**
  - Local SQLite path configurations
  - Production PostgreSQL connection strings
  - Database utility configurations

- ✅ **Studio Configuration**
  - DiffSinger model paths
  - Audio processing settings (Sample rate: 44100, BPM: 120)
  - Studio storage paths
  - Feature flags (Mini Studio enabled, Library enabled)

- ✅ **Development vs Production Settings**
  - DEBUG_MODE flags
  - Environment detection logic
  - Local development safeguards

---

## 🔧 **Server & Deployment Configuration**

### **Server Configuration**
```python
# gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 2
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 5
```

### **Railway Deployment Settings**
- ✅ **Environment Variables** (production keys stored in Railway)
- ✅ **Build Configuration** 
- ✅ **Domain Settings** (www.soulbridgeai.com)

---

## 🎵 **Studio System Configuration**

### **Audio Processing Settings**
```
DEFAULT_SAMPLE_RATE=44100
DEFAULT_BPM=120
DIFFSINGER_DEFAULT_VOICE=default
DIFFSINGER_MODEL_PATH=../models/diffsinger
```

### **Feature Flags**
```
MINI_STUDIO_ENABLED=1
STUDIO_LIBRARY_ENABLED=1
USE_DIFFUSERS=0  # Use local Stable Diffusion
```

### **Storage Paths** (Auto-configured)
- Studio uploads directory
- Generated audio storage
- MIDI file storage  
- Cover art storage

---

## 🔥 **Firebase Configuration**
```javascript
// firebase-config.js
const firebaseConfig = {
    // Configuration preserved in backup
};
```

---

## 💳 **Payment & Billing Configuration**

### **Stripe Integration**
- ✅ **Test API Keys** (fully functional for development)
- ✅ **Product Price IDs** (mapped to Silver/Gold tiers)
- ✅ **Webhook Endpoints** (for payment processing)

### **Tier Configuration**
```
Bronze: $0/month (with ads)
Silver: $12.99/month or $117/year  
Gold: $19.99/month or $180/year
```

---

## 🛡️ **Security Settings**

### **API Keys & Secrets**
- ✅ All production keys backed up securely
- ✅ Development keys separate from production
- ✅ Webhook secrets for payment processing
- ✅ Database connection strings

### **Access Control**
- ✅ Admin user credentials
- ✅ Session management configuration
- ✅ Authentication middleware settings

---

## 📋 **Restoration Instructions**

### **To Restore Full Configuration:**
1. Copy all `.env*` files to new project root
2. Copy `config.py` and `gunicorn_config.py` to backend/
3. Copy `firebase-config.js` to static/js/
4. Install dependencies: `pip install -r requirements.txt`
5. Verify all keys and settings work

### **Environment Setup Priority:**
1. **Critical:** `.env` (main environment variables)
2. **Critical:** `config.py` (application configuration)  
3. **Important:** Stripe keys (payment processing)
4. **Important:** Database settings
5. **Nice-to-have:** Studio configuration

---

## ⚠️ **Security Notes**

- 🔒 **Never commit real keys to git**
- 🔒 **Production keys stored separately in Railway**
- 🔒 **Development keys are safe test keys**
- 🔒 **Backup folder should be .gitignored**

**All critical configuration safely preserved! Ready for modular refactor without losing anything important.** 🚀