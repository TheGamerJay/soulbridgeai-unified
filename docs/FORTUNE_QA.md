# 🔮 Fortune Teller QA Checklist

Quick validation script for fortune tier system - run this after each release to ensure tier limits and models work correctly.

## Prerequisites
- Must be logged in to SoulBridge AI
- Open browser console on the site
- Dev endpoints must be enabled (`DEBUG_MODE=true`)

## Complete Test Script

### 1. Reset Usage
```javascript
await fetch('/api/dev/reset-fortune-today', { credentials:'include' })
  .then(r=>r.json()).then(console.log);
```

### 2. Bronze Plan (limit 3, model gpt-3.5-turbo)
```javascript
await fetch('/api/dev/set-plan/bronze', { credentials:'include' }).then(r=>r.json()).then(console.log);
await fetch('/api/fortune/limits', { credentials:'include' }).then(r=>r.json()).then(console.log);
// Expected: {"success":true,"plan":"bronze","limit":3,"used":0}

// Test limit enforcement - do 4 draws, 4th should return 429
for(let i=1; i<=4; i++) {
  console.log(`--- Bronze Draw ${i} ---`);
  const result = await fetch('/api/fortune/tarot', {
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    credentials:'include',
    body: JSON.stringify({spread:'one', question:`bronze test ${i}`, seed: i})
  }).then(r=>r.json());
  console.log(result.success ? `✅ Success: ${result.today.used}/${result.today.limit}` : `❌ Error: ${result.error}`);
}
// Expected: First 3 succeed, 4th fails with "Daily fortune limit reached (3 for bronze tier)"
```

### 3. Silver Plan (limit 8, model gpt-4.0)
```javascript
await fetch('/api/dev/reset-fortune-today', { credentials:'include' });
await fetch('/api/dev/set-plan/silver', { credentials:'include' }).then(r=>r.json()).then(console.log);
await fetch('/api/fortune/limits', { credentials:'include' }).then(r=>r.json()).then(console.log);
// Expected: {"success":true,"plan":"silver","limit":8,"used":0}

// Test limit enforcement - do 9 draws, 9th should return 429
for(let i=1; i<=9; i++) {
  console.log(`--- Silver Draw ${i} ---`);
  const result = await fetch('/api/fortune/tarot', {
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    credentials:'include',
    body: JSON.stringify({spread:'one', question:`silver test ${i}`, seed: i})
  }).then(r=>r.json());
  console.log(result.success ? `✅ Success: ${result.today.used}/${result.today.limit}` : `❌ Error: ${result.error}`);
  if (i <= 8 && !result.success) break; // Stop if unexpected failure
}
// Expected: First 8 succeed, 9th fails with "Daily fortune limit reached (8 for silver tier)"
```

### 4. Gold Plan (unlimited, model gpt-5)
```javascript
await fetch('/api/dev/reset-fortune-today', { credentials:'include' });
await fetch('/api/dev/set-plan/gold', { credentials:'include' }).then(r=>r.json()).then(console.log);
await fetch('/api/fortune/limits', { credentials:'include' }).then(r=>r.json()).then(console.log);
// Expected: {"success":true,"plan":"gold","limit":null,"used":0}

// Test unlimited access - do multiple draws, should never get 429
for(let i=1; i<=5; i++) {
  console.log(`--- Gold Draw ${i} ---`);
  const result = await fetch('/api/fortune/tarot', {
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    credentials:'include',
    body: JSON.stringify({spread:'one', question:`gold test ${i}`, seed: i})
  }).then(r=>r.json());
  console.log(result.success ? `✅ Success: ${result.today.used}/${result.today.limit || '∞'}` : `❌ Error: ${result.error}`);
}
// Expected: All succeed, limit shows null (displayed as ∞ in UI)
```

### 5. Model Verification
```javascript
// Check Bronze
await fetch('/api/dev/set-plan/bronze', { credentials:'include' });
await fetch('/api/dev/fortune-model', { credentials:'include' })
  .then(r=>r.json()).then(console.log);
// Expected: {"model":"gpt-3.5-turbo","plan":"bronze"}

// Check Silver  
await fetch('/api/dev/set-plan/silver', { credentials:'include' });
await fetch('/api/dev/fortune-model', { credentials:'include' })
  .then(r=>r.json()).then(console.log);
// Expected: {"model":"gpt-4.0","plan":"silver"}

// Check Gold
await fetch('/api/dev/set-plan/gold', { credentials:'include' });
await fetch('/api/dev/fortune-model', { credentials:'include' })
  .then(r=>r.json()).then(console.log);
// Expected: {"model":"gpt-5","plan":"gold"}
```

## Expected Results Summary

| Tier   | Daily Limit | GPT Model      | 429 After |
|--------|-------------|----------------|-----------|
| Bronze | 3           | gpt-3.5-turbo  | 4th draw  |
| Silver | 8           | gpt-4.0        | 9th draw  |
| Gold   | ∞ (null)    | gpt-5          | Never     |

## 🔐 Security Note

**Before deploying to production**, either remove `/api/dev/*` endpoints or guard them:

```python
@app.before_request
def restrict_dev_routes():
    if request.path.startswith("/api/dev/"):
        if session.get("user_email") not in {"admin@yourdomain.com"}:
            return {"ok": False, "error": "FORBIDDEN"}, 403
```

## Troubleshooting

- **"AUTH_REQUIRED" errors**: Make sure you're logged in to SoulBridge AI
- **"FORBIDDEN" errors**: Dev endpoints are restricted to admin users
- **Unexpected limits**: Run reset endpoint first to clear previous usage
- **Wrong models**: Check if `unified_tier_system` or `tarot_engine` has model mappings
- **Frontend shows wrong limits**: Check browser console for API errors

---

**Time to complete**: ~2 minutes  
**Frequency**: After each release or fortune-related changes  
**Owner**: QA Team / Release Manager