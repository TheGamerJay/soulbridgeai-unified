# SoulBridge AI - Complete Project File List

## Main Backend Files
```
./ai_content_filter.py
./ai_model_manager.py
./analytics.py
./app.py
./auth.py
./auto_response.py
./email_service.py
./main.py
./models.py
./oauth.py
./push_notifications.py
./referral_system.py
./run_dev.py
```

## Configuration Files
```
./.env
./.env.example
./.eslintrc.json
./.prettierrc.json
./package-lock.json
./Procfile
./pyproject.toml
./railway.json
./requirements.txt
./runtime.txt
```

## Setup & Build Scripts
```
./quick_start.bat
./run_server.bat
./setup.bat
```

## Documentation
```
./API_DOCUMENTATION.md
./AUTHENTICATION_COMPLETE.md
./EXPORT_BACKUP_COMPLETE.md
./FIREBASE_SETUP.md
./MOOD_TRACKING_COMPLETE.md
./README.md
./replit.md
./SETUP_COMPLETE.md
```

## Database & Logs
```
./soulbridge.db
./soulbridge.log
./env.txt
```

## VS Code & IDE Files
```
./soulbridge.code-workspace
./.claude/settings.local.json
```

## Frontend (React/Vite)
```
./soulbridgeai-frontend/.env
./soulbridgeai-frontend/.gitignore
./soulbridgeai-frontend/eslint.config.js
./soulbridgeai-frontend/index.html
./soulbridgeai-frontend/package.json
./soulbridgeai-frontend/package-lock.json
./soulbridgeai-frontend/vite.config.js
```

## Frontend Source Files
```
./soulbridgeai-frontend/src/App.css
./soulbridgeai-frontend/src/App.jsx
./soulbridgeai-frontend/src/components/AdminDashboard.jsx
./soulbridgeai-frontend/src/components/AdminDashboard.css
./soulbridgeai-frontend/src/components/CompanionSelector.jsx
./soulbridgeai-frontend/src/components/CompanionSelector.css
./soulbridgeai-frontend/src/components/features/Analytics.jsx
./soulbridgeai-frontend/src/components/features/UserManagement.jsx
./soulbridgeai-frontend/src/index.css
./soulbridgeai-frontend/src/main.jsx
```

## Frontend Build Output
```
./soulbridgeai-frontend/dist/index.html
./soulbridgeai-frontend/dist/assets/index-CiNw4gQw.css
./soulbridgeai-frontend/dist/assets/index-Dnth9pCy.js
./soulbridgeai-frontend/dist/favicon.ico
./soulbridgeai-frontend/dist/vite.svg
```

## Static Assets
```
./static/css/animations.css
./static/css/base.css
./static/css/components.css
./static/css/themes.css
./static/logos/IntroLogo.png
./static/logos/SoulBridgeLogo.png
./static/audio/notification.mp3
```

## HTML Templates
```
./templates/admin_dashboard.html
./templates/analytics.html
./templates/billing.html
./templates/chat.html
./templates/customer_service.html
./templates/diagnostics.html
./templates/export_backup.html
./templates/forgot_password.html
./templates/help.html
./templates/knowledge_base.html
./templates/library.html
./templates/live_chat.html
./templates/login.html
./templates/profile.html
./templates/referrals.html
./templates/register.html
./templates/reset_password.html
./templates/subscription.html
./templates/support.html
./templates/terms.html
./templates/voice_chat.html
```

## Core Features & Components

### Authentication System
- User registration, login, logout
- Password reset functionality (email-based)
- OAuth integration (Google, Facebook)
- Session management
- Email verification

### AI Chat System
- Multiple AI companions with unique personalities
- Real-time chat interface
- Message history and persistence
- Content filtering and moderation
- Voice chat capabilities

### User Management
- User profiles and settings
- Subscription management (Stripe integration)
- Referral system
- Analytics and usage tracking
- Mood tracking

### Admin Dashboard
- User analytics and metrics
- System health monitoring
- Support ticket management
- Content moderation tools
- Revenue tracking

### Responsive Design
- Day/night theme toggle
- Mobile-responsive layouts
- Character selection interface
- Modern UI with animations

### Infrastructure
- SQLite database
- Email service (SMTP)
- Push notifications
- Error logging and monitoring
- Development and production configs

## Recent Updates
- ✅ Implemented complete forgot password functionality
- ✅ Fixed Choose Your Companion section visibility in day mode
- ✅ Updated rainbow gradient border consistency (3px)
- ✅ Enhanced responsive design and theme support

## Technology Stack
- **Backend**: Python Flask
- **Frontend**: React.js with Vite
- **Database**: SQLite
- **Styling**: Custom CSS with theme system
- **AI**: OpenAI GPT integration
- **Payments**: Stripe
- **Email**: SMTP service
- **Deployment**: Railway, Vercel ready

## Total Files: ~50 main project files (excluding node_modules dependencies)