# SoulBridge AI - Complete Platform

A comprehensive AI companion platform featuring multiple AI companions, voice chat, and emotional support powered by OpenAI's GPT-4.

## 🌐 Live Website
**Main Website**: [https://soulbridgeai.com](https://soulbridgeai.com)

## 🏗️ Project Structure

This repository contains the complete SoulBridge AI platform:

### **Backend (Flask Application)**
- **Location**: Root directory
- **Purpose**: Main SoulBridge AI application with all companions
- **Features**: Chat interface, voice chat, premium companions, user authentication
- **Deployment**: Railway (soulbridgeai.com)

### **Frontend (React Application)**  
- **Location**: `soulbridgeai-frontend/` directory
- **Purpose**: Modern React interface that connects to the backend
- **Features**: Backend status monitoring, modern UI, responsive design
- **Deployment**: Railway (separate frontend service)

## 🚀 Quick Start

### **For Users**
Visit [https://soulbridgeai.com](https://soulbridgeai.com) to use the platform.

### **For Developers**

#### **Backend Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here
export SESSION_SECRET=your_secret_here

# Run locally
python app.py
```

#### **Frontend Development**
```bash
# Navigate to frontend
cd soulbridgeai-frontend

# Install dependencies  
npm install

# Start development server
npm run dev
```

## 🤖 AI Companions

### **Free Companions**
- **Blayzo**: Wise and calm mentor
- **Blayzica**: Energetic and empathetic assistant

### **Premium Companions (Galaxy)**
- **Blayzion**: Mystical cosmic sage with universal wisdom
- **Blayzia**: Divine feminine energy with healing light
- **Crimson**: Fierce loyal guardian with protective strength
- **Violet**: Ethereal spiritual guide with mystical intuition

## 🎨 Features

- **Multi-Character AI Chat**: Choose from 6 unique AI companions
- **Voice Chat**: Premium voice interaction (Galaxy companions only)
- **Theme Switching**: Dark/Light mode toggle
- **Trial System**: 5 messages per day for trial users
- **Premium Subscriptions**: Unlock Galaxy companions
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Chat**: Instant AI responses
- **Character Personalities**: Each companion has unique traits and responses

## 🔧 Configuration

### **Environment Variables**
```
OPENAI_API_KEY=your_openai_api_key
SESSION_SECRET=your_session_secret
PRODUCTION=true
RAILWAY_ENVIRONMENT=true
```

### **API Endpoints**
- `GET /health` - Health check
- `GET /` - Main chat interface  
- `POST /send_message` - Web chat messages
- `POST /api/chat` - API for external integrations
- `GET /voice-chat` - Voice chat interface (premium)

## 🚂 Deployment

### **Backend (Railway)**
- Configured with `Procfile`, `railway.json`, and `runtime.txt`
- Deploys to main domain: `soulbridgeai.com`
- Uses Gunicorn for production server

### **Frontend (Railway)**
- Configured with Express.js server and `railway.json`
- Serves React build with proper routing
- Connects to backend API for status monitoring

## 📁 File Structure

```
SoulBridge-ai-backend/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway deployment
├── railway.json               # Railway config
├── runtime.txt                # Python version
├── templates/                 # Jinja2 templates
│   ├── chat.html             # Main chat interface
│   ├── login.html            # Authentication
│   ├── voice_chat.html       # Voice chat interface
│   └── ...
├── static/                   # Static assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript
│   └── logos/                # Character images
└── soulbridgeai-frontend/    # React frontend
    ├── src/                  # React source
    ├── dist/                 # Built files
    ├── server.js            # Express server
    ├── railway.json         # Frontend Railway config
    └── package.json         # Node.js dependencies
```

## 🛠️ Development

### **Adding New Companions**
1. Add character prompt to `CHARACTER_PROMPTS` in `app.py`
2. Create character card in `templates/chat.html`
3. Add character-specific CSS in `static/css/themes.css`
4. Add character logo to `static/logos/`

### **Modifying UI**
- **Backend UI**: Edit templates in `templates/` and CSS in `static/css/`
- **Frontend UI**: Edit React components in `soulbridgeai-frontend/src/`

## 📄 License

Part of the SoulBridge AI project - Your AI Companion Journey.