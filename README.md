# SoulBridge AI - Unified Project

A complete AI companion platform with Flask backend and React frontend.

## Project Structure

```
soulbridgeai-unified/
├── backend/          # Flask backend with AI chat, referrals, subscriptions
├── frontend/         # React frontend application  
└── README.md         # This file
```

## Development Setup

### Backend (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend (React)  
```bash
cd frontend
npm install
npm start
```

## Production Deployment (Railway)

### Build Command:
```bash
npm install --prefix frontend && npm run build --prefix frontend && pip install -r backend/requirements.txt
```

### Start Command:
```bash
gunicorn backend.app:app
```

## Features

- ✅ AI Chat Companions (Blayzo, Blayzica, premium companions)
- ✅ Referral System with exclusive companions
- ✅ Subscription system with Stripe integration
- ✅ User authentication and profiles
- ✅ Voice chat capabilities
- ✅ Conversation library and export
- ✅ Admin dashboard
- ✅ Analytics and mood tracking

## API Endpoints

Backend serves both:
- API routes at `/api/*` 
- React frontend at all other routes

## Deployment

This unified structure is designed for Railway deployment with automatic React build integration.