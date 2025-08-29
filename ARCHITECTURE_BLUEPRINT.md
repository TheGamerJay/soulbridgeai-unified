# 🏗️ SoulBridge AI - Architecture Blueprint
**Version:** 2.0 - Modular Rewrite
**Date:** August 29, 2025
**Status:** Planning Phase

---

## 📋 **Current State Assessment**

### **Problems with Current Architecture**
```
Current: MONOLITHIC DISASTER
├── app.py (19,284 lines) ❌
│   ├── Authentication logic
│   ├── Companion system
│   ├── Tier management  
│   ├── Community features
│   ├── Studio functionality
│   ├── API endpoints
│   ├── Template rendering
│   └── Database operations
└── Result: Change one thing → Break everything
```

### **Critical Issues Identified**
- **Tight Coupling:** Terms system breaks when changing tier names
- **Hidden Dependencies:** Shared session logic creates unexpected failures  
- **Maintenance Nightmare:** 19K lines in single file
- **Testing Impossible:** Can't isolate systems for testing
- **Developer Paralysis:** Fear of changing anything

---

## 🎯 **Target Architecture**

### **Core Design Principles**
1. **Single Responsibility:** Each module does ONE thing well
2. **Loose Coupling:** Modules communicate via clean interfaces
3. **High Cohesion:** Related functionality stays together
4. **Dependency Injection:** No hard-coded dependencies
5. **Testability:** Each module can be tested independently

### **New Modular Structure**
```
backend/
├── app.py (100-200 lines MAX - just orchestration)
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── database.py
├── auth/
│   ├── __init__.py
│   ├── models.py        # User, Session models
│   ├── services.py      # Login/logout logic
│   ├── middleware.py    # Authentication checks
│   ├── routes.py        # Auth routes (/login, /logout)
│   └── decorators.py    # @require_login, etc.
├── companions/
│   ├── __init__.py
│   ├── models.py        # Companion definitions
│   ├── services.py      # Selection & access logic
│   ├── routes.py        # Companion routes
│   └── tier_access.py   # Tier-based access rules
├── tiers/
│   ├── __init__.py
│   ├── models.py        # Tier definitions (Bronze/Silver/Gold)
│   ├── services.py      # Subscription logic
│   ├── routes.py        # Tier management routes
│   ├── billing.py       # Payment processing
│   └── trials.py        # Trial system
├── community/
│   ├── __init__.py
│   ├── models.py        # Community data models
│   ├── services.py      # Community logic
│   ├── routes.py        # Community routes
│   └── avatars.py       # Avatar management
├── studio/
│   ├── __init__.py
│   ├── models.py        # Studio data models
│   ├── services.py      # Music creation logic
│   ├── routes.py        # Studio routes
│   └── api.py          # Studio API endpoints
├── api/
│   ├── __init__.py
│   ├── v1/             # API versioning
│   │   ├── companions.py
│   │   ├── tiers.py
│   │   └── studio.py
│   └── shared/
│       ├── responses.py # Standardized API responses
│       └── validators.py # Input validation
└── shared/
    ├── __init__.py
    ├── database.py      # Database connections
    ├── utils.py         # Common utilities
    ├── exceptions.py    # Custom exceptions
    └── logging.py       # Centralized logging
```

---

## 🔌 **Module Interfaces & Dependencies**

### **Dependency Flow (Clean Architecture)**
```
Routes Layer (HTTP)
    ↓
Services Layer (Business Logic)
    ↓  
Models Layer (Data)
    ↓
Database Layer (Persistence)
```

### **Module Communication Rules**
```python
# ✅ ALLOWED: Service-to-Service communication
from companions.services import CompanionService
from tiers.services import TierService

# ✅ ALLOWED: Shared utilities
from shared.database import get_db_connection

# ❌ FORBIDDEN: Direct model access across modules  
from companions.models import Companion  # NO!

# ❌ FORBIDDEN: Route-to-Route dependencies
from companions.routes import companion_selection  # NO!
```

### **Interface Contracts**
```python
# Each module exposes clean public interfaces
class CompanionService:
    def get_accessible_companions(user_id: str, tier: str) -> List[Companion]
    def select_companion(user_id: str, companion_id: str) -> bool
    def get_user_companion(user_id: str) -> Optional[Companion]

class TierService:  
    def get_user_tier(user_id: str) -> str
    def has_tier_access(user_id: str, required_tier: str) -> bool
    def upgrade_user_tier(user_id: str, new_tier: str) -> bool
```

---

## 📊 **Data Flow Architecture**

### **Authentication Flow**
```
User Login Request
    ↓
auth/routes.py → auth/services.py → auth/models.py
    ↓
Session Created → Stored in Database
    ↓
All other modules check auth via auth/middleware.py
```

### **Companion Selection Flow**  
```
Companion Selection Request
    ↓
companions/routes.py → companions/services.py
    ↓
Check Access: companions/tier_access.py → tiers/services.py
    ↓
Valid? → companions/models.py → Database Update
    ↓
Response: Success/Failure
```

### **Tier Validation Flow**
```
Feature Access Request
    ↓
Any Module → tiers/services.py
    ↓
tiers/models.py → Database Query
    ↓
Return: Access Granted/Denied
```

---

## 🧪 **Testing Strategy**

### **Unit Tests (Per Module)**
```python
# companions/tests/test_services.py
def test_companion_access_bronze_user():
    tier_service = MockTierService(return_tier="bronze") 
    companion_service = CompanionService(tier_service)
    
    companions = companion_service.get_accessible_companions("user123", "bronze")
    assert len(companions) == 5  # Only bronze companions
    assert all(c.tier == "bronze" for c in companions)

# tiers/tests/test_services.py  
def test_tier_upgrade():
    tier_service = TierService()
    result = tier_service.upgrade_user_tier("user123", "silver")
    assert result == True
    assert tier_service.get_user_tier("user123") == "silver"
```

### **Integration Tests**
```python
# tests/integration/test_companion_selection.py
def test_full_companion_selection_flow():
    # Test complete flow: Login → Select Companion → Verify Access
    client = TestClient()
    
    # Login as bronze user
    response = client.post("/login", json={"email": "test@example.com"})
    assert response.status_code == 200
    
    # Try to select silver companion (should fail)
    response = client.post("/companions/select", json={"companion_id": "silver_companion"})
    assert response.status_code == 403
    
    # Select bronze companion (should succeed)
    response = client.post("/companions/select", json={"companion_id": "bronze_companion"}) 
    assert response.status_code == 200
```

---

## 🚀 **Migration Strategy**

### **Phase 1: Extract Core Services (Day 1)**
1. Create module structure
2. Extract `auth/` module first (most critical)
3. Extract `companions/` module second
4. **Test:** Login + Companion selection works

### **Phase 2: Extract Business Logic (Day 2)**
1. Extract `tiers/` module
2. Extract `community/` module  
3. Extract `studio/` module
4. **Test:** All major features work independently

### **Phase 3: Clean Integration (Day 3)**
1. Refactor `app.py` to orchestrator only
2. Fix any circular dependencies
3. Comprehensive testing
4. **Test:** Full system works seamlessly

### **Rollback Plan**
- Work in separate git branch
- Keep original `app.py` as backup
- Can rollback at any phase if issues arise
- Deploy only when fully tested

---

## 🎯 **Success Criteria**

### **Technical Metrics**
- [ ] `app.py` reduced from 19,284 to <200 lines
- [ ] Each module <1,000 lines  
- [ ] Zero circular dependencies
- [ ] 90%+ test coverage for core modules
- [ ] All current functionality preserved

### **Developer Experience**
- [ ] Can modify companions without touching auth
- [ ] Can update tiers without breaking community
- [ ] Clear error messages and logging
- [ ] Easy to add new features
- [ ] Fast development iterations

### **System Reliability**
- [ ] No more mysterious redirect loops
- [ ] Predictable behavior when changing code
- [ ] Isolated failures (one module crash doesn't kill everything)
- [ ] Easy debugging and troubleshooting

---

## 📝 **Implementation Checklist**

### **Pre-Development**
- [ ] Review and approve this blueprint
- [ ] Set up development branch: `feature/modular-architecture`
- [ ] Backup current working state
- [ ] Set up testing environment

### **Development Phases**
- [ ] **Phase 1:** Core Services Extraction
- [ ] **Phase 2:** Business Logic Migration  
- [ ] **Phase 3:** Integration & Testing
- [ ] **Phase 4:** Documentation & Deployment

### **Quality Gates**
- [ ] Code review for each module
- [ ] Unit tests passing
- [ ] Integration tests passing  
- [ ] Performance benchmarks maintained
- [ ] Security review completed

---

**This blueprint ensures we build a maintainable, scalable architecture that won't fight us every step of the way. Ready to start construction?** 🏗️