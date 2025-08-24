# SoulBridge AI – Complete Platform

[![CI/CD Pipeline](https://github.com/TheGamerJay/soulbridgeai-unified/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/TheGamerJay/soulbridgeai-unified/actions/workflows/ci-cd.yml)
[![Railway Deploy](https://img.shields.io/badge/Railway-Deploy-blue)](https://railway.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)

A comprehensive AI companion platform with multiple companions, voice chat, and emotional support powered by tiered OpenAI models (Bronze → GPT-3.5, Silver → GPT-4, Gold → GPT-5).

## 🌐 Live Website
**Main Website:** https://soulbridgeai.com

---

## 🏗️ Project Structure

### Backend (Flask)
- Location: Root
- Purpose: Core API + web UI (chat), tier enforcement, usage limits, Mini Studio (Gold-only)
- Deployment: Railway (serves soulbridgeai.com)

### Frontend (React)
- Location: `soulbridgeai-frontend/`
- Purpose: Modern UI consuming backend APIs, health/status widgets
- Deployment: Railway (separate service)

---

## 🚀 Quick Start

### Users
Visit https://soulbridgeai.com

### Developers

#### Backend
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_key
export SESSION_SECRET=your_secret
# optional dev defaults
export DEFAULT_TIER=bronze
python app.py
```

#### Frontend
```bash
cd soulbridgeai-frontend
npm install
npm run dev
```

## 🧩 Tiers & Models
- **Bronze**: Uses GPT-3.5
- **Silver**: Uses GPT-4 (e.g., gpt-4o-mini / gpt-4-turbo)
- **Gold**: Uses GPT-5 (use your actual model ID when enabled)

All tier decisions are computed per request. Personalized pages and APIs send no-cache headers and `Vary: Cookie` to prevent global template sharing.

## 🔐 Feature Access by Tier

| Feature | Bronze | Silver | Gold |
|---------|--------|--------|------|
| Chat (text) | ✅ | ✅ | ✅ |
| Voice Chat | ⛔ | ⛔ | ✅ |
| Decoder / Fortune / Horoscope | Limits | Higher | ∞ |
| Mini Studio (lyrics/MIDI/vocals/FX/art) | ⛔ | ⛔ | ✅ |

**Mini Studio is Gold-only:**
- UI: button/link rendered only if `tier == "gold"`.
- Server: all Mini Studio routes wrapped with `@gold_only` and return 404 for non-gold.

## 🤖 AI Companions

### Core
- **Blayzo** – wise mentor
- **Blayzica** – energetic, empathetic

### Galaxy (Premium → Gold)
- **Blayzion** – mystical cosmic sage
- **Blayzia** – healing light, divine feminine
- **Crimson** – protective guardian
- **Violet** – ethereal spiritual guide

Trials may unlock visibility of higher-tier companions, but model & limits still follow the user's actual tier.

## 🎛️ Mini Studio (Gold-Only)

**Tools:** SecretWriter (lyrics), MIDI, Vocals, Effects, Cover Art

**Route:** `GET /mini-studio` → Gold only (404 otherwise)

**APIs (all Gold only):**
- `POST /api/secret-lyrics`
- `POST /api/midi`
- `POST /api/vocals`, `POST /api/jobs/vocals`
- `POST /api/effects`, `POST /api/jobs/effects`
- `POST /api/cover-art`, `POST /api/jobs/cover-art`
- `GET /api/export`

## 📡 Key API Endpoints

- `GET /health` – health + config
- `GET /` – main chat interface
- `POST /api/chat` – chat API (tier-based model selection)
- `GET /mini-studio` – Gold-only page (404 for others)
- `POST /api/decoder/run` – feature example with per-tier limits
- `GET /api/limits` – current tier + remaining quotas
- **Dev helper:** `POST /api/dev/set-tier { "tier": "bronze|silver|gold" }` (disable in prod)

## ⚙️ Configuration

### Environment
```ini
OPENAI_API_KEY=your_openai_key
SESSION_SECRET=your_session_secret
DEFAULT_TIER=bronze
DATABASE_URL=sqlite:///soulbridge.db
CORS_ORIGINS=http://localhost:5000,*
```

### Tier/Model/Limit Logic (in app.py)
- `get_effective_tier()` resolves: Header `X-User-Tier` → Session → Auth user → `DEFAULT_TIER`
- `TIER_MODEL = {"bronze":"gpt-3.5-turbo","silver":"gpt-4o-mini","gold":"gpt-5"}`
- `TIER_LIMITS` isolate usage by `(user_id, tier, feature)`; no cross-tier sharing
- No-cache headers for personalized HTML/JSON to prevent template reuse between users

## 🧱 Deployment (Railway)

- **Backend:** Procfile, railway.json, runtime.txt, served via Gunicorn
- **Frontend:** Built React app served by its own Railway service
- Both point to the same domain space and connect via environment-configured API base

### Production Build Commands
```bash
# Build Command
npm install --prefix frontend && npm run build --prefix frontend && pip install -r backend/requirements.txt

# Start Command  
gunicorn backend.app:app
```

## 📁 File Structure (high level)

```
SoulBridge-ai-backend/
├── app.py
├── requirements.txt
├── Procfile
├── railway.json
├── runtime.txt
├── templates/
│   ├── chat.html
│   ├── mini_studio_simple.html   # Gold-only
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── logos/
└── soulbridgeai-frontend/
    ├── src/
    ├── dist/
    ├── server.js
    ├── railway.json
    └── package.json
```

## 🛠️ Development Notes

### Adding a Companion
1. Add system prompt/parameters in backend registry
2. Update `templates/chat.html` (render gated by tier as needed)
3. Add assets under `static/logos/` and styles in `static/css/`

### Prevent Global Sharing
- Never compute tier at module import time
- Inject tier per request (`@context_processor`)
- Set headers on personalized responses:
  - `Cache-Control: no-store, private`
  - `Vary: Cookie`

---

## 📄 License
Part of the SoulBridge AI project – Your AI Companion Journey.