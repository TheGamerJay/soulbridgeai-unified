# Current SoulBridge API → Proposed v1 API Mapping

## ✅ **Existing Endpoints That Map Well**

### AUTH / USER
```
Current: /api/user-info
Proposed: GET /v1/me
Status: ✅ EXISTS - needs response format update
```

### ENTITLEMENTS (needs consolidation)
```
Current: Multiple scattered endpoints
- /api/user-status
- /api/trial-status  
- /api/user-plan
- /api/tier-limits
- /api/user/tier-status

Proposed: GET /v1/entitlements
Status: 🔄 NEEDS CONSOLIDATION - create single endpoint
```

### TRIAL
```
Current: /api/start-trial
Proposed: POST /v1/trial/start
Status: ✅ EXISTS - needs response format update

Current: /api/trial-status
Proposed: Part of /v1/entitlements
Status: 🔄 MERGE into entitlements
```

### SUBSCRIPTIONS
```
Current: /api/select-plan + /api/create-checkout-session
Proposed: POST /v1/subscriptions/subscribe
Status: 🔄 NEEDS CONSOLIDATION

Current: No cancel endpoint
Proposed: POST /v1/subscriptions/cancel
Status: ❌ MISSING - needs implementation

Current: No webhook handler
Proposed: POST /v1/webhooks/billing
Status: ❌ MISSING - critical for production
```

### CREDITS
```
Current: No centralized credits endpoint
Proposed: GET /v1/credits
Status: ❌ MISSING - extract from unified_tier_system.py

Current: /api/buy-credits (basic)
Proposed: POST /v1/credits/purchase
Status: 🔄 NEEDS ENHANCEMENT

Current: No spend tracking API
Proposed: POST /v1/credits/spend
Status: ❌ MISSING - currently internal deduct_credits()
```

### FEATURE CALLS
```
Current: /api/ai-image-generation/generate
Proposed: POST /v1/ai/advanced/generate
Status: 🔄 NEEDS RESTRUCTURE for credit spending

Current: Multiple feature endpoints scattered
Proposed: Unified credit-spending pattern
Status: 🔄 NEEDS PATTERN STANDARDIZATION
```

### ADS
```
Current: /api/create-addon-checkout (ad-free)
Proposed: POST /v1/ads/remove
Status: ✅ EXISTS - needs response format update

Current: No ads status endpoint
Proposed: GET /v1/ads/status
Status: ❌ MISSING - part of entitlements
```

## 🚀 **Implementation Roadmap**

### Phase 1: Core Consolidation (Week 1)
1. **Create `/v1/entitlements` endpoint** - consolidate all user permission logic
2. **Standardize `/v1/me`** - clean user info endpoint
3. **Create `/v1/credits`** - centralized credit management

### Phase 2: Credit System Refactor (Week 2)
1. **Implement `/v1/credits/spend`** - centralized spending API
2. **Update all feature endpoints** - use standard credit spending pattern
3. **Add audit logging** - track all credit transactions

### Phase 3: Subscription Management (Week 3)
1. **Create `/v1/subscriptions/cancel`** - proper cancellation flow
2. **Implement `/v1/webhooks/billing`** - Stripe webhook handler
3. **Add subscription status tracking** - grace periods, failed payments

### Phase 4: API Versioning & Documentation (Week 4)
1. **Add v1 prefix** - version all new endpoints
2. **Maintain backward compatibility** - keep old endpoints working
3. **Generate OpenAPI docs** - document the new API structure

## 🎯 **Critical Missing Pieces**

### 1. Webhook Handler (Most Important)
```python
@app.route("/v1/webhooks/billing", methods=["POST"])
def handle_billing_webhook():
    # Handle Stripe events:
    # - invoice.payment_succeeded (reset monthly credits)
    # - invoice.payment_failed (mark past_due)
    # - customer.subscription.deleted (cancel subscription)
```

### 2. Credit Spending Abstraction
```python
def spend_credits_api(user_id: int, amount: int, reason: str):
    # Centralized credit spending with audit trail
    # Order: monthly → topups → trial
    # Log every transaction for support/debugging
```

### 3. Entitlements Calculator
```python
def get_user_entitlements(user_id: int):
    # Single source of truth for ALL permissions
    # Combines: subscription status, trial state, credit balances
    # Returns: plan, features, limits, ads, etc.
```

## 📊 **Migration Strategy**

1. **Gradual Migration**: Keep old endpoints working during transition
2. **Feature Flags**: Use entitlements endpoint to control rollout
3. **Testing**: Create comprehensive test suite for new API
4. **Documentation**: Update frontend to use new consolidated endpoints

This mapping shows your API design would significantly improve the current architecture by consolidating scattered logic into clean, RESTful endpoints.