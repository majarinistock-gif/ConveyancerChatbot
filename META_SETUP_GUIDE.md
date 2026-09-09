# Meta WhatsApp Developer Setup Guide

Complete step-by-step guide to configure Meta WhatsApp for the Conveyancing Chatbot.

## Prerequisites

- Meta Developer Account (free at developers.facebook.com)
- Render deployment URL: `https://conveyancerchatbot.onrender.com`
- Your `.env.local` file with credentials ready

---

## Step 1: Create Meta Developer Account

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click "Get Started" or "Log In"
3. Accept the Meta Developer Terms of Service
4. Create a new app:
   - Select **"Business"** app type
   - Enter app name: `Conveyancing Chatbot`
   - Enter contact email
   - Click "Create App"

---

## Step 2: Add WhatsApp Product to App

1. After creating the app, you'll see the App Dashboard
2. In the "Add Products" section, find **WhatsApp**
3. Click **"Set Up"** or **"Add"** next to WhatsApp
4. WhatsApp will be added to your app

---

## Step 3: Get WhatsApp API Credentials

### 3.1 Get Phone Number ID

1. In the WhatsApp product section, click **"Getting Started"**
2. Scroll to "Send and receive messages"
3. You'll see your **Phone Number ID** (e.g., `1290508100815178`)
4. Copy this to your `.env.local`:
   ```
   META_PHONE_NUMBER_ID=1290508100815178
   ```

### 3.2 Get Access Token

1. In the same WhatsApp section, scroll to "API Setup"
2. Click **"Add a phone number"** if you don't have one
3. Select a phone number (test numbers are free)
4. After selecting, click **"Generate Access Token"**
5. Select permissions needed:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Copy the generated token to `.env.local`:
   ```
   META_ACCESS_TOKEN=EAAX96KOXyQMBSSkup93bjtuCfS02OPh1UcAMNgzxkRqotKQjbU3RyExYFlp1Q29mTrZCt2G0Ocu0tAdonPqZBqLgxZCxwqrglXEnyi1t9Nkxvw2Sg8KbEiZAe7v7nY8k0Uuueh4jNIE7VdbTVqz48smcV7C3G0NdK7tFMscr3noSBFzDHCt9YHCZB77s4XFbIHUABeZAhHbBxe1wGFVjtMCkvuI7yl1FBU8pT5jYGZAezYhfdbDdcPr3KI4WTzitjJuWBMTHZBt21bdVuFcfaKfzZCSd8wZDZD
   ```

### 3.3 Get WABA ID and Business ID

1. In WhatsApp dashboard, note your **WABA ID** (WhatsApp Business Account ID)
2. In the main App Dashboard, find your **App ID** and **Business ID**
3. Add to `.env.local`:
   ```
   META_WABA_ID=1044467861522212
   META_BUSINESS_ID=your_meta_business_id_here
   ```

---

## Step 4: Configure Webhook

### 4.1 Set Webhook URL

1. In WhatsApp product, go to **"Configuration"** tab
2. Scroll to "Webhooks" section
3. Click **"Add"** or **"Edit"** next to Webhook
4. Enter webhook URL:
   ```
   https://conveyancerchatbot.onrender.com/webhook
   ```
5. Enter verify token (must match your `.env.local`):
   ```
   conveyancing_bot_secret_2024
   ```
6. Click **"Verify and Save"**

### 4.2 Subscribe to Webhook Events

After verification, subscribe to these events:
- ✅ `messages` - Required for receiving messages
- ✅ `message_status` - Optional for delivery tracking

1. Click on your webhook
2. Under "Webhook Fields", select:
   - `messages`
   - `message_status`
3. Click **"Manage"** next to each field
4. Subscribe to all sub-events

---

## Step 5: Configure Test Phone Number

1. In WhatsApp dashboard, go to **"Test Numbers"** section
2. Add your test phone number:
   ```
   +15556730054
   ```
3. Verify the number via SMS code
4. This number can now send/receive messages with your bot

---

## Step 6: Update Render Environment Variables

Since your `.env.local` is local, you must add these to Render:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your `conveyancerchatbot` service
3. Go to **"Environment"** tab
4. Add these environment variables:

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `sandbox` |
| `META_ACCESS_TOKEN` | Your access token |
| `META_PHONE_NUMBER_ID` | Your phone number ID |
| `WHATSAPP_VERIFY_TOKEN` | `conveyancing_bot_secret_2024` |
| `META_WABA_ID` | Your WABA ID |
| `META_BUSINESS_ID` | Your business ID |
| `TEST_PHONE_NUMBER` | `+15556730054` |
| `MONGO_URI` | Your MongoDB URI |
| `MONGO_DATABASE` | `conveyancing_bot` |
| `OCR_SPACE_API_KEY` | Your OCR key |
| `PAYNOW_INTEGRATION_ID` | Your Paynow ID |
| `PAYNOW_INTEGRATION_KEY` | Your Paynow key |
| `PAYNOW_RESULT_URL` | `https://conveyancerchatbot.onrender.com/payment/callback` |

5. Click **"Save Changes"**
6. Render will automatically redeploy

---

## Step 7: Test the Bot

### 7.1 Test Webhook

1. In Meta Developer Portal, webhook should show "Active"
2. Send a test message from your Meta test number:
   ```
   hie
   ```
3. Bot should respond with the service menu

### 7.2 Verify Bot Response

Expected response:
```
🏠 Welcome to the Zimbabwe Legal Services Bot!

I can help you with:

*Conveyancing & Property Functions*
1. Deed of Transfer
2. Deeds Office Search
...
```

---

## Step 8: Troubleshooting

### Webhook Verification Fails

- Verify webhook URL is correct: `https://conveyancerchatbot.onrender.com/webhook`
- Check verify token matches exactly in both places
- Ensure Render service is running

### Bot Not Responding

- Check Render logs for errors
- Verify webhook events are subscribed
- Check phone number is verified in Meta
- Ensure MongoDB connection is working

### 401 Unauthorized Error

- Access token may have expired
- Regenerate access token in Meta Developer Portal
- Update in Render environment variables

---

## Step 9: Production Setup (When Ready)

To move from sandbox to production:

1. **Upgrade WhatsApp API**
   - In Meta Developer Portal, upgrade to production access
   - Requires business verification

2. **Use Production Phone Number**
   - Add your business WhatsApp number
   - Remove test number limitations

3. **Update Environment**
   - Change `ENVIRONMENT=production` in Render
   - Update webhook if needed

---

## Quick Reference

**Webhook URL:** `https://conveyancerchatbot.onrender.com/webhook`

**Verify Token:** `conveyancing_bot_secret_2024`

**Required Events:**
- `messages`
- `message_status`

**Environment Variables Required:**
- `META_ACCESS_TOKEN`
- `META_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `META_WABA_ID`
- `META_BUSINESS_ID`

---

## Support Links

- [Meta WhatsApp API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Render Dashboard](https://dashboard.render.com)
- [MongoDB Atlas](https://cloud.mongodb.com)

---

**Last Updated:** September 2026
