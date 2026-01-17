# Resend Email Setup Guide

This guide will help you set up Resend for email sending in the Sulambi VMS application. Resend is recommended for Render free tier deployments since Render blocks SMTP ports (25, 465, 587) on free services.

## Why Resend?

- ✅ Works on Render free tier (uses HTTP API, not SMTP ports)
- ✅ Free tier: **3,000 emails/month** (~100/day) - better than SendGrid!
- ✅ Modern, developer-friendly API
- ✅ Reliable delivery and tracking
- ✅ Easy integration with Python SDK

## Step 1: Create Resend Account

1. Go to https://resend.com/
2. Click "Get Started" or "Sign Up"
3. Sign up with your email address (GitHub sign-in also available)
4. Verify your email address
5. Complete the onboarding process

## Step 2: Get API Key

1. In Resend Dashboard, go to **API Keys**
2. Click **Create API Key**
3. Give it a name: `Sulambi VMS Production` (or any name you prefer)
4. Select permissions:
   - **Sending access** (required for sending emails)
   - Or **Full access** if you want all permissions
5. Click **Add** or **Create**
6. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - It will look like: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 3: Verify Domain (Recommended)

Resend allows you to send from a verified domain for better deliverability:

1. Go to **Domains** in Resend Dashboard
2. Click **Add Domain**
3. Enter your domain (e.g., `yourdomain.com`)
4. Follow the DNS setup instructions:
   - Add the required DNS records (SPF, DKIM, DMARC) to your domain's DNS settings
   - Resend will verify these records automatically
5. Once verified, you can send from any email address on that domain

**Note:** For testing, you can use the default Resend domain (`onboarding@resend.dev`), but it's limited and less reliable. Domain verification is recommended for production.

## Step 4: Configure Environment Variables

### For Local Development (.env file)

Add to your `.env` file:

```env
# Resend Configuration (preferred for Render free tier)
RESEND_API_KEY=re_your-api-key-here
RESEND_FROM_EMAIL=your-verified-email@yourdomain.com

# Optional: Keep SMTP as fallback (not needed if using Resend)
# AUTOMAILER_EMAIL=your-email@gmail.com
# AUTOMAILER_PASSW=your-app-password
```

**Important Notes:**
- `RESEND_FROM_EMAIL` must be either:
  - An email address on a verified domain, OR
  - The default Resend domain for testing: `onboarding@resend.dev`
- If you don't set `RESEND_FROM_EMAIL`, it will use `AUTOMAILER_EMAIL` as fallback

### For Render Deployment

1. Go to your **Backend Service** → **Environment** tab in Render Dashboard
2. Add the following environment variables:

| Variable | Value | Example |
|----------|-------|---------|
| `RESEND_API_KEY` | Your Resend API key | `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `RESEND_FROM_EMAIL` | Your verified sender email | `your-email@yourdomain.com` or `onboarding@resend.dev` |

**Important Notes:**
- `RESEND_FROM_EMAIL` must be the same email you're authorized to send from
- The API key must start with `re_`
- You can remove `AUTOMAILER_EMAIL` and `AUTOMAILER_PASSW` if you're only using Resend

## Step 5: Test the Configuration

### Option A: Use the Test Email Endpoint

After deployment, test the email configuration:

```
GET https://your-backend.onrender.com/api/auth/test-email?email=your-test-email@gmail.com
```

This will:
- Check if Resend is configured
- Test the API key format
- Send a test email if everything is valid

The response will show:
- `"provider": "Resend"` if Resend is configured correctly
- `"provider": "SMTP"` if using SMTP fallback

### Option B: Test Locally

1. Make sure `RESEND_API_KEY` and `RESEND_FROM_EMAIL` are in your `.env` file
2. Restart your backend server
3. Call the test email endpoint:
   ```bash
   curl http://localhost:5000/api/auth/test-email?email=your-test-email@gmail.com
   ```

## How It Works

The application will automatically:

1. **Check Resend first** - If `RESEND_API_KEY` is configured, it uses Resend
2. **Fall back to SMTP** - If Resend is not configured, it tries SMTP (Gmail, etc.)
3. **Log which provider is used** - Check logs for `[EMAIL SUCCESS] Email sent via Resend` or `via SMTP`

## Troubleshooting

### Error: "Resend API key format is invalid"
- **Solution**: Make sure your API key starts with `re_`
- Verify there are no extra spaces before or after the key
- Check that you copied the entire API key from Resend dashboard

### Error: "Failed to send email via Resend"
- **Solution**: 
  - Check Resend dashboard → **Logs** tab to see email status
  - Verify `RESEND_FROM_EMAIL` is a verified email address or `onboarding@resend.dev`
  - Make sure your API key has "Sending access" permissions
  - Check that you haven't exceeded your free tier limit (3,000 emails/month)

### Error: "Sender email not verified"
- **Solution**: 
  - Use `onboarding@resend.dev` for testing, OR
  - Verify your domain in Resend dashboard → **Domains**
  - Use an email address from a verified domain in `RESEND_FROM_EMAIL`

### Error: "Email sent but not received"
- **Solution**: 
  - Check Resend dashboard → **Logs** tab to see delivery status
  - Check spam/junk folder
  - Verify recipient email is valid
  - Domain verification improves deliverability significantly

### Still getting SMTP errors on Render free tier?
- **Solution**: Make sure `RESEND_API_KEY` is set in Render environment variables
- Remove or comment out `AUTOMAILER_PASSW` to force Resend usage
- Check that `RESEND_FROM_EMAIL` is also set

## Resend Free Tier Limits

- **3,000 emails/month** - Reset monthly
- **One domain** - Free tier allows one verified domain
- **Full API access** - All Resend features available
- **Email activity logs** - View delivery, opens, clicks
- **No regional sending** - Fixed region (can't choose)

## Upgrade to Paid Plans

If you need more than 3,000 emails/month:

1. Go to Resend Dashboard → **Settings** → **Billing**
2. Choose a paid plan:
   - **Pro**: $20/month - 50,000 emails/month
   - **Scale**: Custom pricing - Higher volumes
   - **Enterprise**: Custom pricing - Dedicated IPs and support

## Comparison: Resend vs SendGrid vs SMTP

| Feature | Resend | SendGrid | SMTP |
|---------|--------|----------|------|
| **Free Tier** | 3,000/month | 100/day | Varies |
| **Works on Render Free** | ✅ Yes (HTTP API) | ✅ Yes (HTTP API) | ❌ No (blocked ports) |
| **Setup Complexity** | Very Easy | Moderate | Complex |
| **Deliverability** | Excellent | Excellent | Varies |
| **Developer Experience** | Modern & Clean | Established | Traditional |

## Support

- Resend Documentation: https://resend.com/docs
- Resend Support: https://resend.com/support
- Resend Status: https://status.resend.com/
- Render SMTP Policy: https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports

---

**Last Updated:** 2025
**Version:** 1.0

