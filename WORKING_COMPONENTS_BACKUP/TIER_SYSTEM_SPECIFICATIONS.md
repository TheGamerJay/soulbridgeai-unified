# 🏆 SoulBridge AI Tier System Complete Specifications
**Backup Date:** August 29, 2025  
**Purpose:** Preserve complete tier definitions, limits, features, and pricing for modular refactor

---

## 🎯 **Tier System Overview**

### **Naming Convention**
- **Internal System**: bronze/silver/gold (standardized)
- **Display Names**: Bronze Tier / Silver Tier / Gold Tier  
- **Legacy Names**: free → bronze, growth → silver, max → gold
- **Database Values**: "bronze", "silver", "gold"

---

## 🥉 **TIER 1: BRONZE (Default)**

### **Core Properties**
```json
{
  "tier_id": 1,
  "tier_name": "bronze", 
  "display_name": "Bronze Tier",
  "price": 0,
  "billing_cycle": null,
  "default_tier": true,
  "has_ads": true
}
```

### **Feature Limits**
```json
{
  "decoder_daily": 3,
  "fortune_daily": 2,
  "horoscope_daily": 3,
  "creative_writer_daily": 2,
  "artistic_time_monthly": 0,
  "companion_messages_daily": 5
}
```

### **Available Features**
- ✅ **Basic Chat Features**
  - Decoder: 3 daily uses
  - Fortune: 2 daily uses
  - Horoscope: 3 daily uses
  - Creative Writer: 2 daily uses
  - Companion Messages: 5 daily

- ❌ **Premium Features LOCKED**
  - AI Image Generation: LOCKED
  - Voice Journaling: LOCKED
  - Relationship Profiles: LOCKED
  - Meditations: LOCKED
  - Mini Studio: LOCKED

- ✅ **Companion Access**
  - Bronze tier companions only
  - Limited companion selection

- ⚠️ **Ad Experience**
  - Displays ads during usage
  - Ad-supported experience

### **5-Hour Trial Access**
```json
{
  "trial_duration_hours": 5,
  "trial_credits": 60,
  "unlocks_silver_access": true,
  "unlocks_gold_access": true,
  "one_time_only": true,
  "available_to": "bronze_users_only"
}
```

---

## 🥈 **TIER 2: SILVER (Subscription)**

### **Core Properties**
```json
{
  "tier_id": 2,
  "tier_name": "silver",
  "display_name": "Silver Tier", 
  "monthly_price": 12.99,
  "yearly_price": 117.00,
  "yearly_savings": "25%",
  "has_ads": false
}
```

### **Feature Limits**
```json
{
  "decoder_daily": 15,
  "fortune_daily": 8,
  "horoscope_daily": 10,
  "creative_writer_daily": 20,
  "artistic_time_monthly": 200,
  "companion_messages_daily": 25,
  "rollover_credits": false
}
```

### **Available Features**
- ✅ **Enhanced Chat Features**
  - Decoder: 15 daily uses
  - Fortune: 8 daily uses
  - Horoscope: 10 daily uses
  - Creative Writer: 20 daily uses
  - Companion Messages: 25 daily

- ✅ **Premium Features UNLOCKED**
  - AI Image Generation: 10 monthly
  - Voice Journaling: UNLOCKED
  - Relationship Profiles: UNLOCKED
  - Meditations: UNLOCKED

- ❌ **Gold Exclusive Features**
  - Mini Studio: LOCKED (Gold only)

- ✅ **Companion Access**
  - Bronze + Silver tier companions
  - Expanded companion selection

- ✅ **Ad-Free Experience**
  - No ads during usage
  - Premium user experience

### **Credit System**
- **Monthly Allocation**: 200 artistic time credits
- **Reset Cycle**: Every billing cycle (monthly/yearly)
- **Rollover**: NO - unused credits are lost
- **Additional Purchases**: Available when subscription active

---

## 🥇 **TIER 3: GOLD (Premium Subscription)**

### **Core Properties**
```json
{
  "tier_id": 3,
  "tier_name": "gold",
  "display_name": "Gold Tier",
  "monthly_price": 19.99,
  "yearly_price": 180.00,
  "yearly_savings": "25%",
  "has_ads": false
}
```

### **Feature Limits**
```json
{
  "decoder_daily": "unlimited",
  "fortune_daily": "unlimited", 
  "horoscope_daily": "unlimited",
  "creative_writer_daily": "unlimited",
  "artistic_time_monthly": 500,
  "companion_messages_daily": "unlimited",
  "rollover_credits": false
}
```

### **Available Features**
- ✅ **Unlimited Chat Features**
  - Decoder: UNLIMITED daily uses
  - Fortune: UNLIMITED daily uses
  - Horoscope: UNLIMITED daily uses
  - Creative Writer: UNLIMITED daily uses
  - Companion Messages: UNLIMITED daily

- ✅ **All Premium Features UNLOCKED**
  - AI Image Generation: UNLIMITED
  - Voice Journaling: UNLOCKED
  - Relationship Profiles: UNLOCKED
  - Meditations: UNLOCKED

- ✅ **Gold Exclusive Features**
  - Mini Studio: UNLOCKED
  - Advanced music creation tools
  - Professional audio features

- ✅ **Full Companion Access**
  - Bronze + Silver + Gold tier companions
  - Complete companion selection
  - Premium companion interactions

- ✅ **Premium Ad-Free Experience**
  - No ads during usage
  - Luxury user experience

### **Credit System**
- **Monthly Allocation**: 500 artistic time credits
- **Reset Cycle**: Every billing cycle (monthly/yearly)
- **Rollover**: NO - unused credits are lost
- **Additional Purchases**: Available when subscription active

---

## 💳 **Billing & Payment System**

### **Stripe Price IDs (Production)**
```json
{
  "silver_monthly": "price_1RxcFwBR4omRdqnXPW1Sx34k",
  "silver_yearly": "price_1RxcJjBR4omRdqnXgtbnvF2A", 
  "gold_monthly": "price_1RxcSPBR4omRdqnXNvqJCAbB",
  "gold_yearly": "price_1RxcbwBR4omRdqnXTxU9jtES"
}
```

### **Payment Policy**
- **Payment Model**: Pay first - charged immediately upon subscribing
- **Billing Cycles**: Monthly or Yearly (25% savings on yearly)
- **Cancellation Policy**: No refunds - keep access for full paid period
- **Auto-Renewal**: Subscriptions auto-renew unless cancelled
- **Downgrade**: Automatic revert to Bronze tier after billing period ends

### **Additional Credit Purchases**
- **Availability**: Silver and Gold subscribers only
- **Pricing**: TBD (estimated $5-10 for 50-100 credits)
- **Restrictions**: Must have active subscription
- **Usage Priority**: Purchased credits used before monthly allocation
- **Rollover**: NO - all credits lost at billing cycle reset

---

## 🔄 **Tier Logic Implementation**

### **Effective Plan Calculation**
```python
def get_effective_plan(user_plan, trial_active):
    """Get effective plan - Bronze users with active trial get Gold access"""
    if trial_active and user_plan == "bronze":
        return "gold"  # Trial gives Gold access
    return user_plan
```

### **Feature Access Validation**
```python
def has_feature_access(user_plan, trial_active, feature):
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Feature tier requirements
    feature_tiers = {
        "ai_images": "silver",
        "voice_journal": "silver", 
        "meditations": "silver",
        "mini_studio": "gold"
    }
    
    required_tier = feature_tiers.get(feature, "bronze")
    tier_hierarchy = {"bronze": 1, "silver": 2, "gold": 3}
    
    return tier_hierarchy[effective_plan] >= tier_hierarchy[required_tier]
```

### **Companion Access Logic**
```python
def get_accessible_companions(user_plan, trial_active):
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    companions = {
        "bronze": ["Blayzo", "Sapphire"],
        "silver": ["Blayzo", "Sapphire", "Violet", "Crimson"],
        "gold": ["Blayzo", "Sapphire", "Violet", "Crimson", "Blayzion", "Blayzia"]
    }
    
    return companions.get(effective_plan, companions["bronze"])
```

---

## 🎨 **Tier Visual Identity**

### **Color Schemes**
```css
.tier-bronze {
  --primary-color: #CD7F32;
  --accent-gradient: linear-gradient(135deg, #CD7F32, #B8860B);
  --tier-badge: "🥉";
}

.tier-silver {
  --primary-color: #C0C0C0;
  --accent-gradient: linear-gradient(135deg, #C0C0C0, #708090);
  --tier-badge: "🥈";
}

.tier-gold {
  --primary-color: #FFD700;
  --accent-gradient: linear-gradient(135deg, #FFD700, #FFA500);
  --tier-badge: "🥇";
}
```

### **Lock UI Patterns**
```css
.locked-feature {
  position: relative;
  opacity: 0.6;
  pointer-events: none;
}

.tier-lock-overlay {
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(4px);
  /* Lock icon and upgrade prompts */
}
```

---

## 🔮 **Future Tier Expansion**

### **Planned Tiers**
```json
{
  "platinum": {
    "tier_id": 4,
    "position": "above_gold",
    "features": "TBD - Ultra premium"
  },
  "diamond": {
    "tier_id": 5, 
    "position": "ultimate_tier",
    "features": "TBD - Exclusive features"
  }
}
```

---

## ⚙️ **Configuration Variables**

### **Environment Variables**
```bash
# Daily Limits
COMP_MSG_LIMIT_BRONZE=5
COMP_MSG_LIMIT_SILVER=25  
COMP_MSG_LIMIT_GOLD=999

# Monthly Credits
ARTISTIC_TIME_SILVER=200
ARTISTIC_TIME_GOLD=500

# Trial Settings
TRIAL_DURATION_HOURS=5
TRIAL_CREDITS=60
```

### **Database Schema**
```sql
-- Users table tier fields
user_plan VARCHAR(20) DEFAULT 'bronze'
trial_active BOOLEAN DEFAULT FALSE
trial_expires_at TIMESTAMP
artistic_time INTEGER DEFAULT 0
trial_credits INTEGER DEFAULT 0
```

**Complete tier system specifications preserved! All limits, features, pricing, and logic documented for modular refactor.** 🚀