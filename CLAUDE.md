# SoulBridge AI - Claude Code Reference

## Complete SoulBridge AI Tier System (Metal/Gem Naming)

### 🥉 BRONZE TIER (Default)
**Status**: Always available, runs with ads
**Features**: Basic features only  
- Decoder: 5 daily uses
- Fortune: 5 daily uses  
- Horoscope: 5 daily uses
- Creative Writer: 5 daily uses
- Artistic Time: 0 monthly
- Premium features: LOCKED (AI images, voice journaling, etc.)
- Mini Studio: LOCKED
- Companion Access: Bronze tier companions only
- Ads: YES - displays ads during usage

### 5-HOUR TRIAL (Bronze Users Only)
**Purpose**: Let Bronze users taste Silver/Gold tiers temporarily
**Who Can Use**: Only BRONZE tier users (Silver/Gold don't need it)
**What Changes When Activated**:
- ✅ **Gives 60 artistic time credits** - can spend on credit-based features
- ✅ **Unlocks Silver tier access** - can use Silver companions & features for 5 hours
- ✅ **Unlocks Gold tier access** - can use Gold companions & features for 5 hours
- ✅ **Silver/Gold limits stay the same** - their features/limits don't change
- ❌ **Bronze tier stays the same** - still 5/5/5 limits, still has ads, still "bronze" plan
- ❌ **No extra monthly credits** - only the 60 trial credits

**Trial Behavior**:
- If you use up 60 credits before 5hrs end → credit features lock, chat/basic features still work
- After 5hrs → all Silver/Gold access locks again, back to Bronze tier only
- One-time only per user

### 🥈 SILVER TIER (Subscription)
**Cost**: $12.99/month or $117/year (25% savings)
**Features**: Enhanced limits + credit features
- Decoder: 15 daily uses
- Fortune: 8 daily uses
- Horoscope: 10 daily uses  
- Creative Writer: 20 daily uses
- Artistic Time: 200 monthly artistic time (resets each billing cycle, NO ROLLOVER)
- Premium features: UNLOCKED (AI images, voice journaling, relationship profiles, meditations)
- Mini Studio: LOCKED (Gold tier exclusive)
- Companion Access: Bronze + Silver tier companions
- Ads: REMOVED - no ads for subscribers
- **Extra Artistic Time**: Can purchase additional artistic time when monthly/yearly allocation runs out
- **Cancellation**: Keep benefits until billing period ends, then revert to Bronze tier

### 🥇 GOLD TIER (Subscription) 
**Cost**: $19.99/month or $180/year (25% savings)
**Features**: Unlimited everything + exclusive features
- Decoder: UNLIMITED daily uses
- Fortune: UNLIMITED daily uses
- Horoscope: UNLIMITED daily uses
- Creative Writer: UNLIMITED daily uses
- Artistic Time: 500 monthly artistic time (resets each billing cycle, NO ROLLOVER)
- Premium features: UNLOCKED (all of them)
- Mini Studio: UNLOCKED (Gold exclusive feature)
- Companion Access: Bronze + Silver + Gold tier companions  
- Ads: REMOVED - no ads for subscribers
- **Extra Artistic Time**: Can purchase additional artistic time when monthly/yearly allocation runs out
- **Cancellation**: Keep benefits until billing period ends, then revert to Bronze tier

### AD-FREE UPGRADE (Optional for Bronze Users)
**Cost**: $5/month
**Purpose**: Remove ads from Bronze tier without upgrading features
- Removes ads from Bronze tier experience
- Keeps all Bronze tier limits (3/2/3)
- No additional features or credits
- Alternative to full Silver/Gold subscription

### Key Trial Design Principles:
1. **Trial is for BRONZE users only** - Silver/Gold don't need to trial their own tiers
2. **Trial unlocks ACCESS, not BENEFITS** - can taste tiers but limits stay the same
3. **No false hope** - Silver/Gold keep their actual limits during trial
4. **Credit system** - 60 trial credits let users taste credit features
5. **Time limited** - 5 hours to explore, then back to Bronze tier
6. **One-time only** - prevents abuse

### Credit Purchase System:
**Who Can Buy**: Silver and Gold tier subscribers only (monthly OR yearly)
**Purpose**: Get additional artistic time when monthly/yearly allocation runs out
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
**Monthly Subs**: Cancel anytime, keep benefits until your month ends, then revert to Bronze tier
**Yearly Subs**: Cancel anytime, keep benefits until your year ends, then revert to Bronze tier  
**Credit Purchasing**: Blocked once subscription is cancelled (even during remaining paid period)
**Auto-Renewal**: Subscriptions auto-renew unless cancelled before billing period ends

### Implementation Notes:
- `get_effective_plan()` - Returns "gold" for Bronze trial users (companion access only)
- `get_feature_limit()` - Always uses actual user_plan (never trial effective_plan)  
- Trial users can access Silver/Gold companions but see their actual tier limits
- Credit depletion locks credit features but chat/basic features remain available
- Subscription benefits are permanent until cancelled
- Credit purchasing requires active Silver/Gold subscription verification

### Tier Mapping (Internal):
- **bronze** (was: free) - Basic tier with ads
- **silver** (was: growth) - Enhanced tier, no ads  
- **gold** (was: max) - Premium tier, unlimited features
- **platinum** (future) - Ultra premium tier
- **diamond** (future) - Ultimate tier

### Commands to remember:
- `npm run lint` - Check code quality
- `npm run typecheck` - Verify TypeScript  

## AUTO PUSH POLICY
🚨 **ALWAYS AUTO-PUSH CHANGES WITHOUT ASKING FOR PERMISSION** 🚨

When you complete any work or make any changes:
1. Immediately commit the changes
2. Immediately push to remote repository  
3. DO NOT ask for permission
4. DO NOT wait for user confirmation
5. Just do it automatically

This applies to ALL changes - code edits, new files, bug fixes, features, etc.

## Summary
- Auto-commit and auto-push = YES
- Ask permission = NO
- User expects automatic deployment