# SoulBridge AI - Modular Architecture

🚀 **Clean, maintainable, isolated modules replacing the 19,284-line monolith!**

## 🏗️ Architecture Overview

This is the **modular refactor** of SoulBridge AI, designed to eliminate cascade failures and provide maintainable, isolated functionality.

### 📁 Module Structure

```
soulbridge_modular/
├── auth/                    # Authentication & User Management
│   ├── models.py           # User data models
│   ├── routes.py           # Auth endpoints
│   └── services.py         # Business logic
├── companions/             # AI Companions (Coming Soon)
├── tiers/                  # Subscription & Billing (Coming Soon)
├── community/              # Social Features (Coming Soon)
├── studio/                 # Music Creation (Coming Soon)
├── shared/                 # Common Infrastructure
│   ├── database/           # Database connection
│   ├── config/             # Configuration management
│   ├── middleware/         # Session management
│   └── utils/              # Helper functions
└── templates/              # Clean, reusable templates
```

## 🎯 Key Improvements

### ✅ **Eliminated Cascade Failures**
- **Old**: Changing tier names broke unrelated terms system
- **New**: Modules are isolated - auth changes don't break companions

### ✅ **Clean Separation of Concerns**
- **Authentication**: User login, registration, session management
- **Shared Utils**: Database, configuration, common helpers
- **Modular Routes**: Each module handles its own endpoints

### ✅ **Maintainable Codebase**
- **Single Responsibility**: Each module does one thing well
- **Clear Interfaces**: Modules communicate through defined APIs
- **Easy Testing**: Modules can be tested in isolation

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# - Add your OpenAI API key
# - Add your Stripe keys
# - Configure database URL
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 📊 Tier System

### 🥉 Bronze Tier (Free)
- Basic AI companions
- Limited daily uses (3/2/3/2)
- Ad-supported
- **5-Hour Gold Trial Available!**

### 🥈 Silver Tier ($12.99/month)
- Enhanced features
- Higher limits (15/8/10/20)
- Premium features unlocked
- No ads

### 🥇 Gold Tier ($19.99/month)
- Unlimited daily uses
- All premium features
- Mini Studio access
- Priority support

## 🔧 Development

### Module Development Guidelines

1. **Isolation**: Each module should be self-contained
2. **Interfaces**: Use shared utilities for common functionality
3. **Testing**: Write tests for each module independently
4. **Documentation**: Document module APIs and dependencies

### Adding New Modules

1. Create module directory: `mkdir new_module`
2. Add `__init__.py`, `routes.py`, `models.py`, `services.py`
3. Register blueprint in `app.py`
4. Update this README

## 📝 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout
- `POST /auth/activate-trial` - Activate 5-hour trial
- `GET /auth/check-session` - Check session status

### Core
- `GET /` - Home page
- `GET /health` - Health check
- `GET /about` - About page

## 🧪 Testing

```bash
# Run health check
curl http://localhost:5000/health

# Test authentication
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

## 📈 Migration Status

### ✅ Phase 1 Complete
- [x] Shared infrastructure (database, config, session)
- [x] Authentication module
- [x] Main application entry point
- [x] Clean templates and static assets

### 🔄 Phase 2 (Next)
- [ ] Companions module
- [ ] Tiers & billing module
- [ ] Basic chat functionality

### 📋 Phase 3 (Future)
- [ ] Community features
- [ ] Studio module
- [ ] Advanced features

## 🔒 Security

- **Password Hashing**: Secure SHA-256 with salt
- **Session Management**: Centralized session handling
- **Input Validation**: Sanitization and validation
- **Environment Isolation**: Secrets in environment variables

## 🌟 Benefits Achieved

1. **Maintainability**: Easy to understand and modify
2. **Scalability**: Add new features without breaking existing ones
3. **Testability**: Test modules independently
4. **Reliability**: No more cascade failures
5. **Developer Experience**: Clean, organized code

---

**🎉 The monolithic nightmare is over! Welcome to clean, modular architecture!**