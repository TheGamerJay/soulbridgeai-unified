# SoulBridge AI - Claude Code Reference

## Complete SoulBridge AI Tier System

### FREE TIER (Default)
**Status**: Always available, runs with ads
**Features**: Basic features only
- Decoder: 3 daily uses
- Fortune: 2 daily uses  
- Horoscope: 3 daily uses
- Creative Writer: 2 daily uses
- Credits: 0 monthly (no trainer time)
- Premium features: LOCKED (AI images, voice journaling, etc.)
- Mini Studio: LOCKED
- Companion Access: Free tier companions only
- Ads: YES - displays ads during usage

### 5-HOUR TRIAL (Free Users Only)
**Purpose**: Let free users taste Growth/Max tiers temporarily
**Who Can Use**: Only FREE tier users (Growth/Max don't need it)
**What Changes When Activated**:
- ✅ **Gives 60 trainer time credits** - can spend on credit-based features
- ✅ **Unlocks Growth tier access** - can use Growth companions & features for 5 hours
- ✅ **Unlocks Max tier access** - can use Max companions & features for 5 hours
- ✅ **Growth/Max limits stay the same** - their features/limits don't change
- ❌ **Free tier stays the same** - still 3/2/3 limits, still has ads, still "free" plan
- ❌ **No extra monthly credits** - only the 60 trial credits

**Trial Behavior**:
- If you use up 60 credits before 5hrs end → credit features lock, chat/basic features still work
- After 5hrs → all Growth/Max access locks again, back to free tier only
- One-time only per user

### GROWTH TIER (Subscription)
**Cost**: $12.99/month or $117/year (25% savings)
**Features**: Enhanced limits + credit features
- Decoder: 15 daily uses
- Fortune: 8 daily uses
- Horoscope: 10 daily uses  
- Creative Writer: 20 daily uses
- Credits: 100 monthly trainer time (resets each billing cycle, NO ROLLOVER)
- Premium features: UNLOCKED (AI images, voice journaling, relationship profiles, meditations)
- Mini Studio: LOCKED (Max tier exclusive)
- Companion Access: Free + Growth tier companions
- Ads: REMOVED - no ads for subscribers
- **Extra Credits**: Can purchase additional trainer time when monthly/yearly allocation runs out
- **Cancellation**: Keep benefits until billing period ends, then revert to free tier

### MAX TIER (Subscription) 
**Cost**: $19.99/month or $180/year (25% savings)
**Features**: Unlimited everything + exclusive features
- Decoder: UNLIMITED daily uses
- Fortune: UNLIMITED daily uses
- Horoscope: UNLIMITED daily uses
- Creative Writer: UNLIMITED daily uses
- Credits: 500 monthly trainer time (resets each billing cycle, NO ROLLOVER)
- Premium features: UNLOCKED (all of them)
- Mini Studio: UNLOCKED (Max exclusive feature)
- Companion Access: Free + Growth + Max tier companions  
- Ads: REMOVED - no ads for subscribers
- **Extra Credits**: Can purchase additional trainer time when monthly/yearly allocation runs out
- **Cancellation**: Keep benefits until billing period ends, then revert to free tier

### AD-FREE UPGRADE (Optional for Free Users)
**Cost**: $5/month
**Purpose**: Remove ads from free tier without upgrading features
- Removes ads from free tier experience
- Keeps all free tier limits (3/2/3)
- No additional features or credits
- Alternative to full Growth/Max subscription

### Key Trial Design Principles:
1. **Trial is for FREE users only** - Growth/Max don't need to trial their own tiers
2. **Trial unlocks ACCESS, not BENEFITS** - can taste tiers but limits stay the same
3. **No false hope** - Growth/Max keep their actual limits during trial
4. **Credit system** - 60 trial credits let users taste credit features
5. **Time limited** - 5 hours to explore, then back to free tier
6. **One-time only** - prevents abuse

### Credit Purchase System:
**Who Can Buy**: Growth and Max tier subscribers only (monthly OR yearly)
**Purpose**: Get additional trainer time when monthly/yearly allocation runs out
**Pricing**: TBD (likely $5-10 for 50-100 additional credits)
**Behavior**: 
- Purchased credits add to current balance
- Used before monthly credits reset
- Only available to active subscribers (prevents cancelled users from purchasing)
- Accessible through dedicated credits purchase page
- **NO ROLLOVER**: All unused credits (monthly + purchased) are lost at billing cycle reset

### Subscription & Cancellation Policy:
**Payment**: Pay first - charged immediately upon subscribing (monthly or yearly)
**Cancellation**: No refunds - you keep access for the full period you paid for
**Monthly Subs**: Cancel anytime, keep benefits until your month ends, then revert to free tier
**Yearly Subs**: Cancel anytime, keep benefits until your year ends, then revert to free tier  
**Credit Purchasing**: Blocked once subscription is cancelled (even during remaining paid period)
**Auto-Renewal**: Subscriptions auto-renew unless cancelled before billing period ends

### Implementation Notes:
- `get_effective_plan()` - Returns "max" for free trial users (companion access only)
- `get_feature_limit()` - Always uses actual user_plan (never trial effective_plan)  
- Trial users can access Growth/Max companions but see their actual tier limits
- Credit depletion locks credit features but chat/basic features remain available
- Subscription benefits are permanent until cancelled
- Credit purchasing requires active Growth/Max subscription verification

### Commands to remember:
- `npm run lint` - Check code quality
- `npm run typecheck` - Verify TypeScript  
- Always commit changes when user asks to "push all changes"