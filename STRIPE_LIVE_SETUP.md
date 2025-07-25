# 🚀 SoulBridge AI - Live Payment Setup Guide

## ✅ Current Payment System Status
The payment system is **ready for live mode**! Here's what's already implemented:

### 🏗️ **Features Already Built:**
- ✅ **Free Tier**: Full functionality with limitations (5 decoder uses/day, basic characters)
- ✅ **3-Tier Pricing**: Growth ($12.99/month), Transformation ($19.99/month)
- ✅ **Stripe Integration**: Complete checkout flow with webhooks
- ✅ **Subscription Validation**: Real-time verification system
- ✅ **Premium Features**: Voice chat, unlimited decoder, premium characters
- ✅ **Auto-Detection**: Automatically switches between test/live mode

### 🔧 **To Go Live - Environment Variables Needed:**

```bash
# === REQUIRED FOR LIVE PAYMENTS ===
STRIPE_SECRET_KEY=sk_live_your_live_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# === OPTIONAL BUT RECOMMENDED ===
DATABASE_URL=your_production_database_url
SECRET_KEY=your_secure_session_secret
```

## 🎯 **Step-by-Step Live Setup:**

### **1. Get Stripe Live Keys**
1. Log into your [Stripe Dashboard](https://dashboard.stripe.com)
2. Switch to **Live mode** (toggle in top-left)
3. Go to **Developers** → **API keys**
4. Copy your **Live** secret key (starts with `sk_live_`)
5. Copy your **Live** publishable key (starts with `pk_live_`)

### **2. Set Up Webhook Endpoint**
1. In Stripe Dashboard → **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://yourdomain.com/api/stripe-webhook`
4. Select events: `checkout.session.completed`
5. Copy the **Signing secret** (starts with `whsec_`)

### **3. Update Environment Variables**
```bash
# Replace these with your actual live keys:
export STRIPE_SECRET_KEY="sk_live_your_actual_key"
export STRIPE_PUBLISHABLE_KEY="pk_live_your_actual_key"  
export STRIPE_WEBHOOK_SECRET="whsec_your_actual_secret"
```

### **4. Test the Setup**
```bash
# Check if live mode is detected
curl -X GET https://yourdomain.com/health
# Should show: "Stripe configured in LIVE mode"
```

## 🎨 **Current Pricing Structure:**

| Plan | Monthly | Yearly | Features |
|------|---------|--------|----------|
| **Foundation** | Free | Free | 50 msgs/session, 2 sessions/day, 5 decoder uses/day |
| **Growth** | $12.99 | $99 | Unlimited messages, premium characters, voice chat |
| **Transformation** | $19.99 | $179 | Everything + advanced features |

## 🔒 **Security Features Already Implemented:**
- ✅ **Webhook Signature Verification**: Prevents fake payment notifications
- ✅ **Session Management**: Secure authentication with timeouts
- ✅ **Subscription Validation**: Real-time checks against database
- ✅ **Auto-Logout**: Removes access when subscription expires
- ✅ **Rate Limiting**: Prevents API abuse

## 🚦 **How Auto-Detection Works:**

The system automatically detects mode based on your Stripe keys:

```python
# Test Mode (Development)
if STRIPE_SECRET_KEY starts with "sk_test_":
    - Shows "Simulate Payment" buttons
    - Bypasses real Stripe checkout
    - Free testing environment

# Live Mode (Production)  
if STRIPE_SECRET_KEY starts with "sk_live_":
    - Real Stripe checkout
    - Actual payment processing
    - Live webhook handling
```

## 🎯 **What Happens When You Go Live:**

1. **Free Users**: Continue using Foundation tier (unchanged)
2. **New Subscriptions**: Real payments through Stripe
3. **Premium Features**: Automatically unlock with valid subscription
4. **Webhook Events**: Update user access in real-time

## 📊 **Payment Flow:**

```
User clicks "Choose Growth" 
    ↓
Stripe Checkout (live payment)
    ↓
Webhook confirms payment
    ↓
Database updated with subscription
    ↓
Premium features unlock automatically
```

## ⚡ **Quick Launch Checklist:**

- [ ] Add live Stripe keys to environment
- [ ] Configure webhook endpoint URL
- [ ] Test a small payment ($1 test)
- [ ] Verify premium features unlock
- [ ] Monitor webhook events in Stripe dashboard

## 🆘 **Troubleshooting:**

**Issue**: Payment not working
**Fix**: Check webhook URL is accessible and secret is correct

**Issue**: Features not unlocking  
**Fix**: Verify webhook events are being received at `/api/stripe-webhook`

**Issue**: Still in test mode
**Fix**: Ensure `STRIPE_SECRET_KEY` starts with `sk_live_` not `sk_test_`

---

## 🎉 **Ready to Launch!**

Your payment system is **production-ready**. Just add the live environment variables and you're good to go! 

The free tier ensures users can try SoulBridge AI without any barriers, while the premium tiers provide advanced features for paying customers.