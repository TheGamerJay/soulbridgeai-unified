# Bronze/Silver/Gold Stripe Setup Guide

## Overview
This guide helps you configure Stripe products and pricing for the new Bronze/Silver/Gold tier system.

## 1. Create Products in Stripe Dashboard

### Step 1: Log into Stripe Dashboard
1. Go to [https://dashboard.stripe.com](https://dashboard.stripe.com)
2. Make sure you're in the correct environment (Test vs Live)

### Step 2: Create Silver Subscription Product
1. Navigate to **Products** → **Add product**
2. **Product Information:**
   - **Name**: `SoulBridge AI Silver Plan`
   - **Description**: `Enhanced AI features with 100 monthly trainer credits, no ads, and premium tools`
   - **Statement descriptor**: `SOULBRIDGE SILVER`

3. **Pricing:**
   - Create **TWO** prices for this product:
   
   **Monthly Price:**
   - **Price**: `$12.99`
   - **Billing period**: `Monthly`
   - **Currency**: `USD`
   - **Price description**: `Silver Monthly`
   - Copy the **Price ID** (starts with `price_`) → This is `PRICE_SILVER_MONTHLY`
   
   **Yearly Price:**
   - **Price**: `$117.00` (25% savings: $12.99 × 12 × 0.75)
   - **Billing period**: `Yearly`
   - **Currency**: `USD`
   - **Price description**: `Silver Yearly (25% off)`
   - Copy the **Price ID** (starts with `price_`) → This is `PRICE_SILVER_YEARLY`

### Step 3: Create Gold Subscription Product
1. Navigate to **Products** → **Add product**
2. **Product Information:**
   - **Name**: `SoulBridge AI Gold Plan`
   - **Description**: `Unlimited AI features with 500 monthly trainer credits, Mini Studio access, and all premium tools`
   - **Statement descriptor**: `SOULBRIDGE GOLD`

3. **Pricing:**
   - Create **TWO** prices for this product:
   
   **Monthly Price:**
   - **Price**: `$19.99`
   - **Billing period**: `Monthly`
   - **Currency**: `USD`
   - **Price description**: `Gold Monthly`
   - Copy the **Price ID** (starts with `price_`) → This is `PRICE_GOLD_MONTHLY`
   
   **Yearly Price:**
   - **Price**: `$180.00` (25% savings: $19.99 × 12 × 0.75)
   - **Billing period**: `Yearly`
   - **Currency**: `USD`
   - **Price description**: `Gold Yearly (25% off)`
   - Copy the **Price ID** (starts with `price_`) → This is `PRICE_GOLD_YEARLY`

### Step 4: Verify Ad-Free Product (Optional)
If you don't already have an ad-free product:

1. Navigate to **Products** → **Add product**
2. **Product Information:**
   - **Name**: `SoulBridge AI Ad-Free`
   - **Description**: `Remove ads from Bronze tier experience`
   - **Statement descriptor**: `SOULBRIDGE ADFREE`

3. **Pricing:**
   - **Price**: `$5.00`
   - **Billing period**: `Monthly`
   - **Currency**: `USD`
   - **Price description**: `Ad-Free Monthly`
   - Copy the **Price ID** → Update `PRICE_ADFREE` if needed

## 2. Configure Webhook Endpoint

### Step 1: Set Up Webhook
1. Navigate to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**: `https://soulbridgeai.com/api/stripe/webhook`
4. **Events to send**:
   ```
   checkout.session.completed
   customer.subscription.created
   customer.subscription.updated
   customer.subscription.deleted
   invoice.payment_succeeded
   invoice.payment_failed
   ```

### Step 2: Get Webhook Secret
1. After creating the webhook, click on it
2. Copy the **Signing secret** (starts with `whsec_`)
3. This is your `STRIPE_WEBHOOK_SECRET`

## 3. Environment Variables Configuration

Add these environment variables to your Railway deployment:

```bash
# Existing (you should already have these)
STRIPE_SECRET_KEY=sk_live_your_actual_secret_key
APP_DOMAIN=https://soulbridgeai.com

# New Bronze/Silver/Gold Price IDs
PRICE_SILVER_MONTHLY=price_your_silver_monthly_id
PRICE_SILVER_YEARLY=price_your_silver_yearly_id
PRICE_GOLD_MONTHLY=price_your_gold_monthly_id
PRICE_GOLD_YEARLY=price_your_gold_yearly_id

# Webhook Secret
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Existing Ad-Free (update if needed)
PRICE_ADFREE=price_your_adfree_id
```

### Setting Environment Variables in Railway:
1. Go to your Railway project dashboard
2. Click on your service
3. Go to **Variables** tab
4. Add each variable individually
5. Deploy the changes

## 4. Test the Integration

### Test Checklist:
- [ ] `/api/me` endpoint returns access data
- [ ] `/api/stripe/checkout` creates checkout sessions
- [ ] Webhook receives and processes events
- [ ] Database plan updates work correctly
- [ ] Trial system activates for Bronze users

### Test Commands:
```bash
# Test /api/me endpoint
curl -X GET https://soulbridgeai.com/api/me \
  -H "Cookie: session=your_session_cookie"

# Test checkout creation
curl -X POST https://soulbridgeai.com/api/stripe/checkout \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{"plan": "silver", "billing_cycle": "monthly"}'
```

## 5. Frontend Integration Examples

### Check User Access:
```javascript
const response = await fetch('/api/me');
const data = await response.json();

if (data.success) {
  const canAccessGold = data.access.unlocked_tiers.includes('gold');
  const isTrialActive = data.access.trial_live;
  const limits = data.access.limits;
}
```

### Create Checkout Session:
```javascript
async function upgradeToSilver() {
  const response = await fetch('/api/stripe/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      plan: 'silver', 
      billing_cycle: 'yearly' // or 'monthly'
    })
  });
  
  const data = await response.json();
  if (data.ok) {
    window.location.href = data.url; // Redirect to Stripe Checkout
  }
}
```

## 6. Pricing Summary

| Plan | Monthly | Yearly | Features |
|------|---------|--------|----------|
| **Bronze** | Free | Free | 3/2/3 limits, ads, basic features |
| **Silver** | $12.99 | $117 (25% off) | 15/8/10 limits, no ads, 100 credits |
| **Gold** | $19.99 | $180 (25% off) | Unlimited, Mini Studio, 500 credits |
| **Ad-Free** | $5.00 | - | Bronze + no ads |

## 7. Trial System Details

- **Who**: Bronze users only
- **Duration**: 5 hours
- **Access**: Unlocks Silver/Gold tier access
- **Limits**: Stay at Bronze levels (3/2/3)
- **Credits**: 60 trainer time credits
- **One-time**: Can only be used once per user

## Troubleshooting

### Common Issues:

1. **Webhook not receiving events**:
   - Check webhook URL is correct
   - Verify endpoint is publicly accessible
   - Check webhook secret matches environment variable

2. **Checkout sessions failing**:
   - Verify price IDs are correct
   - Check Stripe secret key is valid
   - Ensure products are active in Stripe

3. **Database migrations not running**:
   - Check logs for migration errors
   - Verify database permissions
   - Run migrations manually if needed

### Support:
- Stripe Documentation: [https://stripe.com/docs](https://stripe.com/docs)
- Railway Environment Variables: [https://docs.railway.app/develop/variables](https://docs.railway.app/develop/variables)