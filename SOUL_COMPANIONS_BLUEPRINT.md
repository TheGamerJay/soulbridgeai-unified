# 🎯 Soul Companions + Artistic Time Credit System Blueprint

## 📋 Overview

**Goal**: Replace Bronze/Silver/Gold tier system with unified "Soul Companions" access + Artistic Time credits

**Key Principles**:
- All users get access to ALL Soul Companions from day one
- Usage is gated by Artistic Time credits, not artificial tier restrictions
- Anti-abuse measures prevent credit farming
- Simple pricing: Free (100 credits) → Soul Companions Pro ($12.99/month + 300 credits)

---

## 🏗️ System Architecture

### 1. Database Schema

#### A. Credit System Tables
```sql
-- User credit balances and signup bonus tracking
CREATE TABLE user_credits (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  credits_remaining INTEGER NOT NULL DEFAULT 0,
  last_reset_at TIMESTAMPTZ,
  signup_bonus_used BOOLEAN NOT NULL DEFAULT FALSE
);

-- Complete audit trail of all credit transactions
CREATE TABLE credit_ledger (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  delta INTEGER NOT NULL,                -- +add or -deduct
  reason TEXT NOT NULL,                  -- 'signup_bonus', 'monthly_reset', 'feature:decoder', etc.
  metadata JSONB DEFAULT '{}'::jsonb,    -- flexible context data
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_credit_ledger_user ON credit_ledger(user_id, created_at);
```

#### B. Anti-Abuse Tables
```sql
-- Track device fingerprints to prevent multiple signups
CREATE TABLE device_fingerprints (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  fingerprint_sha256 TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (fingerprint_sha256)
);

-- Track IP addresses that have received free credits
CREATE TABLE ip_grants (
  id BIGSERIAL PRIMARY KEY,
  ip TEXT NOT NULL,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  granted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_ip_grants_ip ON ip_grants(ip);
```

#### C. Stripe Integration Enhancement
```sql
-- Add subscription cadence tracking
ALTER TABLE stripe_subscriptions 
  ADD COLUMN IF NOT EXISTS cadence TEXT; -- 'monthly'|'yearly'|NULL
```

### 2. Feature Cost Structure

#### A. Current Feature Costs (Artistic Time Credits)
```
Feature                 Cost    Notes
------------------------------------
Decoder                 3       Quick analysis
Fortune Teller          5       Tarot readings
Horoscope              3       Daily insights  
Creative Writer        8       Long-form content
Soul Riddle            4       Mind-bending puzzles & brain games
AI Image Generation    15      High-cost feature
Voice Journaling       10      Audio processing
Meditation Session     5       Audio content
Mini Studio (basic)    20      Premium feature
Mini Studio (advanced) 35      Highest cost
Chat Messages          1       Per message
```

#### B. Credit Packages
```
Package Type           Credits    Price    $/Credit
--------------------------------------------------
Signup Bonus          100        FREE     $0.00
Monthly Subscription   300        $12.99   $0.043
Yearly Subscription    300/mo     $117/yr  $0.033 (25% savings)

Top-up Packs:
Small Pack            50         $2.99    $0.060  (impulse buy)
Medium Pack           120        $5.99    $0.050  (good value)
Large Pack            300        $12.99   $0.043  (same as subscription)
```

**Pricing Strategy:**
- **Small pack**: Impulse purchase territory at $2.99
- **Medium pack**: Sweet spot for regular top-ups  
- **Large pack**: Same $/credit as subscription (fair choice)
- **Progressive savings**: Encourages larger purchases
- **Subscription advantage**: Monthly refills vs one-time purchase

### 3. Soul Companions Unification

#### A. Remove Tier Restrictions
```
OLD SYSTEM:
Bronze: 10 companions (basic ones)
Silver: 18 companions (+ premium ones)
Gold: 26 companions (+ exclusive ones)
Referral: 31 companions (+ referral unlocks)

NEW SYSTEM:
ALL USERS: 31 companions (access to everything)
Usage gated by credits, not companion access
```

#### B. Companion Categories (for UI organization, not restrictions)
```
Categories:
- Creative Companions (Claude, Creative Writer variants)
- Mystical Companions (Fortune tellers, Horoscope readers)  
- Supportive Companions (Blayzica, Violet, nurturing ones)
- Advanced Companions (Technical, analytical ones)
- Exclusive Companions (Special personalities)
```

---

## 🔧 Implementation Plan

### Phase 1: Database Foundation
1. ✅ Add new credit system tables
2. ✅ Add anti-abuse tracking tables  
3. ✅ Extend Stripe tables for subscription cadence
4. ✅ Initialize existing user (ID: 104) with credit balance

### Phase 2: Backend Core System
1. **Credit Management System**
   - `modules/credits/` - Credit logic and decorators
   - `@require_credits(cost, feature_name)` decorator
   - Credit balance tracking and ledger
   
2. **Anti-Abuse System**
   - Device fingerprinting capture
   - IP tracking and limits
   - Signup bonus eligibility checking
   
3. **Authentication Enhancement**
   - Email verification grants signup bonus
   - Anti-abuse checks during bonus grant

### Phase 3: Feature Integration
1. **Replace Tier Checks with Credit Checks**
   - Update all feature endpoints to use `@require_credits`
   - Remove Bronze/Silver/Gold gating logic
   - Unified error handling for insufficient credits

2. **Companion System Updates**
   - Remove tier restrictions from companion data
   - Show all companions to all users
   - Update companion selection logic

### Phase 4: Stripe Integration
1. **Subscription Management**
   - Monthly subscriptions grant 300 credits on billing cycle
   - Yearly subscriptions grant 300 credits monthly (via cron)
   - Enhanced webhook handling for credit grants

2. **Top-up System** 
   - One-time credit purchases
   - Instant credit delivery via webhook
   - Multiple package sizes

### Phase 5: Frontend Experience
1. **Credit Display System**
   - Header credit counter
   - Real-time balance updates
   - Credit usage feedback

2. **Purchase Flow**
   - Subscription signup flow
   - Top-up modal for instant credits
   - Empty credits upgrade prompts

3. **Companion Interface**
   - Unified companion gallery (all 31 companions)
   - Remove tier badges and restrictions
   - Credit cost preview for features

---

## 🛡️ Anti-Abuse Strategy

### 1. Signup Abuse Prevention
```
Limits:
- Max 2 free credit grants per IP address
- Max 1 free credit grant per device fingerprint  
- Email verification required before credit grant
- Disposable email domain blocking
```

### 2. Device Fingerprinting
```javascript
// Frontend: Generate deterministic device fingerprint
function getDeviceFingerprint() {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.textBaseline = 'top';
  ctx.font = '14px Arial';
  ctx.fillText('SoulBridge fingerprint', 2, 2);
  
  const fingerprint = navigator.userAgent + 
                     navigator.language + 
                     screen.width + 'x' + screen.height +
                     canvas.toDataURL();
                     
  return sha256(fingerprint);
}
```

### 3. Rate Limiting
```
Signup rate limits:
- 5 signups per IP per hour
- 10 signups per IP per day
- Progressive delays for repeated attempts
```

---

## 💰 Revenue Model

### Current State Analysis
```
Current Tiers:
Bronze (Free): Limited features, ads
Silver ($12.99): Enhanced limits, no ads  
Gold ($19.99): Premium limits, exclusive features

Problems:
- Artificial feature restrictions confuse users
- Tier upgrades feel punitive ("pay to unlock basic features")
- Complex limit tracking across multiple dimensions
```

### New Revenue Model
```
Soul Companions (Free): 100 credits, all companions
Soul Companions Pro ($12.99/month): 300 monthly credits

Benefits:
- Clearer value proposition ("more usage")
- Users can try everything with free credits
- Natural upgrade pressure when credits run low
- Simpler pricing story
```

### Revenue Optimization
```
Key Metrics to Track:
- Credit burn rate by user segment
- Conversion from free credits to subscription
- Top-up purchase patterns
- Feature usage distribution

Optimization Levers:
- Adjust feature costs based on usage data
- Modify free credit amount for signup conversion
- Test different top-up pricing strategies
- A/B test subscription credit amounts
```

---

## 📊 Success Metrics

### 1. User Experience
- ✅ Reduced support tickets about tier restrictions
- ✅ Increased companion usage diversity  
- ✅ Higher feature adoption rates
- ✅ Clearer upgrade path understanding

### 2. Business Metrics  
- 📈 Conversion rate from free to paid
- 📈 Average revenue per user (ARPU)
- 📈 User engagement (features used per session)
- 📉 Churn rate improvement

### 3. Technical Metrics
- ✅ Credit system accuracy (ledger reconciliation)
- ✅ Anti-abuse effectiveness (blocked farming attempts)
- ✅ System performance (fast credit checks)
- ✅ Webhook reliability (Stripe integration)

---

## 🚀 Migration Strategy

### For New System (No Existing Users)
1. **Clean Implementation**
   - Build credit system as primary monetization
   - Remove tier complexity entirely
   - Launch with unified Soul Companions

2. **Launch Checklist**
   - [ ] Database schema deployed
   - [ ] Credit system tested end-to-end  
   - [ ] Anti-abuse measures active
   - [ ] Stripe webhooks configured
   - [ ] Frontend credit UI implemented
   - [ ] All companions accessible to everyone
   - [ ] Feature costs optimized for engagement

### Environment Configuration
```env
# Credit System
ARTISTIC_TIME_ENABLED=true
ARTISTIC_SIGNUP_CREDITS=100
ARTISTIC_MONTHLY_CREDITS=300
ARTISTIC_YEARLY_CREDITS=300

# Anti-Abuse
ABUSE_MAX_FREE_PER_IP=2
ABUSE_MAX_FREE_PER_DEVICE=1
RATE_LIMIT_SIGNUP_PER_IP_PER_HOUR=5

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_monthly_id
STRIPE_PRICE_YEARLY=price_yearly_id
STRIPE_PRICE_TOPUP_SMALL=price_small_id
STRIPE_PRICE_TOPUP_MED=price_med_id
STRIPE_PRICE_TOPUP_LARGE=price_large_id

# Yearly Reset Cron
CRON_AUTH_TOKEN=secure_random_token
YEARLY_PRICE_IDS=price_yearly_id
```

---

## 🎯 Next Steps

1. **Start Implementation** ✋ *Ready when you are!*
2. **Database Migration** - Create tables and initialize system
3. **Backend Core** - Credit management and anti-abuse
4. **Feature Integration** - Replace tier checks with credit checks  
5. **Frontend Experience** - Credit display and purchase flows
6. **Testing & Launch** - End-to-end validation and go-live

---

*This blueprint provides a complete roadmap for transitioning from the complex tier system to a clean, unified Soul Companions + Artistic Time credit model. The system is designed to be user-friendly, abuse-resistant, and revenue-optimized.*