# SoulBridge AI - Unified Project

[![CI/CD Pipeline](https://github.com/TheGamerJay/soulbridgeai-unified/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/TheGamerJay/soulbridgeai-unified/actions/workflows/ci-cd.yml)
[![Railway Deploy](https://img.shields.io/badge/Railway-Deploy-blue)](https://railway.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)

A complete AI companion platform with Flask backend and React frontend, featuring real-time notifications, business intelligence, and enterprise security.

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