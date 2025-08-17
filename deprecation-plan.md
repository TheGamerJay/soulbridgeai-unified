# API Deprecation Plan - Remove Redundant Endpoints

## 🗑️ **Endpoints to DELETE (Replaced by v1 API)**

### Replaced by `/v1/entitlements`
```python
# DELETE THESE - All consolidated into /v1/entitlements
@app.route("/api/user-status", methods=["GET"])          # ❌ DELETE
@app.route("/api/trial-status", methods=["GET"])         # ❌ DELETE  
@app.route("/api/user-plan", methods=["GET"])            # ❌ DELETE
@app.route("/api/tier-limits", methods=["GET"])          # ❌ DELETE
@app.route("/api/user/tier-status", methods=["GET"])     # ❌ DELETE
@app.route("/api/plan", methods=["GET"])                 # ❌ DELETE
@app.route("/api/get-current-plan", methods=["GET"])     # ❌ DELETE
```

### Replaced by `/v1/me`
```python
# DELETE THIS - Replaced by /v1/me
@app.route("/api/user-info", methods=["GET"])            # ❌ DELETE
```

### Replaced by `/v1/trial/start`
```python
# KEEP but mark deprecated - frontend needs gradual migration
@app.route("/api/start-trial", methods=["POST"])         # ⚠️ DEPRECATE
```

### Replaced by `/v1/credits/*`
```python
# These can be consolidated into v1 credit endpoints
@app.route("/api/decoder/check-limit")                   # ❌ DELETE (use entitlements)
@app.route("/api/fortune/check-limit")                   # ❌ DELETE (use entitlements)  
@app.route("/api/horoscope/check-limit")                 # ❌ DELETE (use entitlements)
```

## 🔄 **Migration Strategy**

### Phase 1: Add v1 endpoints (keep old ones)
```python
# Register v1 API alongside existing endpoints
from v1_api import register_v1_api
register_v1_api(app)

# Add deprecation warnings to old endpoints
@app.route("/api/user-status", methods=["GET"])
def user_status():
    logger.warning("DEPRECATED: /api/user-status - use /v1/entitlements")
    # ... existing logic
```

### Phase 2: Update frontend to use v1 endpoints
```javascript
// Replace old scattered calls
// OLD:
// await fetch('/api/user-status')
// await fetch('/api/trial-status') 
// await fetch('/api/tier-limits')

// NEW: Single call
await fetch('/v1/entitlements')
```

### Phase 3: Remove old endpoints
```python
# After frontend is updated, delete old endpoints completely
# This cleanup will remove ~15 redundant endpoints
```

## 📝 **Cleanup Script**

Let me create a cleanup script to safely remove deprecated endpoints: