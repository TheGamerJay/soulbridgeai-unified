# Railway Deployment Guide - SoulBridge AI Unified

## 🚀 Quick Deploy to Railway

### Prerequisites
- Railway account connected to your GitHub
- Project pushed to GitHub repository

### Deployment Steps

1. **Connect to Railway**
   - Go to [Railway](https://railway.app)
   - Create new project from GitHub repo
   - Select `soulbridgeai-unified` repository

2. **Configure Environment Variables**
   Set these in Railway dashboard:
   ```
   OPENAI_API_KEY=your_openai_api_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   SESSION_SECRET=your_session_secret
   PORT=8080
   PYTHONPATH=/app/backend
   RAILWAY_ENVIRONMENT=production
   ```

3. **Domain Setup**
   - Railway will auto-generate a domain
   - Or connect your custom domain in settings

## 🏗️ Build Process

### What Happens During Build:
1. **Frontend Build** (Node.js 18)
   - Installs React dependencies
   - Builds optimized production bundle
   - Copies assets (logos, etc.)

2. **Backend Setup** (Python 3.9)
   - Installs Python dependencies
   - Sets up Flask application
   - Configures static file serving

3. **Final Assembly**
   - React build files served by Flask
   - API routes available at `/api/*`
   - Frontend routes handled by React Router

## 📁 Project Structure
```
soulbridgeai-unified/
├── frontend/          # React application
│   ├── src/
│   ├── public/        # Static assets (logos)
│   └── build/         # Built files (created during deploy)
├── backend/           # Flask API server
│   ├── app.py         # Main Flask app
│   ├── static/        # Backend assets
│   └── templates/     # HTML templates
├── Dockerfile         # Multi-stage build
├── railway.toml       # Railway configuration
└── start.sh          # Production start script
```

## 🔧 Configuration Files

### `railway.toml`
- Uses Dockerfile for build
- Health check at `/`
- Auto-restart on failure

### `Dockerfile`
- Multi-stage build for optimization
- Frontend build with Node.js
- Backend runtime with Python
- Serves React from Flask

### `start.sh`
- Starts Gunicorn server
- Binds to Railway's PORT
- Production-ready configuration

## 🌐 API Endpoints

### Core Routes:
- `GET /` - React application
- `GET /api/health` - Health check
- `POST /api/chat` - AI chat endpoint
- `GET /admin` - Admin dashboard
- `GET /profile` - User profile

### Static Assets:
- `/static/*` - Backend static files
- `/*` - Frontend static files (JS, CSS, images)

## 🎯 Features Deployed:
- ✅ Complete AI chat system
- ✅ Character selection (Blayzo, Blayzica)
- ✅ Admin authentication
- ✅ User profiles and data export
- ✅ Responsive design
- ✅ All companion logos and assets
- ✅ Real-time chat interface
- ✅ Backend API integration

## 🔍 Troubleshooting

### Build Issues:
- Check Node.js version (requires 18.x)
- Verify all dependencies in package.json
- Ensure frontend builds successfully

### Runtime Issues:
- Check environment variables
- Verify OpenAI API key
- Check logs in Railway dashboard

### Asset Issues:
- Logos in `/frontend/public/`
- Static files served from Flask
- Check file paths in components

## 📊 Monitoring
- Health check: `https://your-app.railway.app/health`
- Logs available in Railway dashboard
- Auto-restart on failures configured

Your SoulBridge AI unified application is now ready for Railway deployment! 🚀