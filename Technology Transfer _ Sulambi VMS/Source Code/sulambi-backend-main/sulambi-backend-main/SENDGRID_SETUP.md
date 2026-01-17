# SendGrid Email Setup Guide

This guide will help you set up SendGrid for email sending in the Sulambi VMS application. SendGrid is recommended for Render free tier deployments since Render blocks SMTP ports (25, 465, 587) on free services.

## Why SendGrid?

- ✅ Works on Render free tier (uses HTTP API, not SMTP ports)
- ✅ Free tier: 100 emails/day
- ✅ Reliable delivery and tracking
- ✅ Easy integration with Python SDK

## Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Click "Start for free"
3. Sign up with your email address
4. Verify your email address
5. Complete the onboarding process

## Step 2: Create API Key

1. In SendGrid Dashboard, go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Give it a name: `Sulambi VMS Production` (or any name you prefer)
4. Select **Full Access** permissions (or at minimum: **Mail Send**)
5. Click **Create & View**
6. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - It will look like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 3: Verify Sender Identity

SendGrid requires you to verify your sender email address:

1. Go to **Settings** → **Sender Authentication**
2. Choose one of the following:

### Option A: Single Sender Verification (Easiest - for testing)
1. Click **Verify a Single Sender**
2. Fill in your details:
   - **From Email**: Your email address (e.g., `your-email@gmail.com`)
   - **From Name**: Your name (e.g., `Sulambi VOSA`)
   - **Reply To**: Same as From Email (or different if you want)
   - **Company Address**: Your organization's address
3. Click **Create**
4. Check your email and click the verification link
5. Your sender is now verified ✅

### Option B: Domain Authentication (Recommended for production)
1. Click **Authenticate Your Domain**
2. Follow the DNS setup instructions
3. Add the required DNS records to your domain
4. Once verified, you can send from any email address on that domain

## Step 4: Configure Environment Variables

### For Local Development (.env file)

Add to your `.env` file:

```env
# SendGrid Configuration (preferred for Render free tier)
SENDGRID_API_KEY=SG.your-api-key-here
SENDGRID_FROM_EMAIL=your-email@gmail.com

# Optional: Keep SMTP as fallback (not needed if using SendGrid)
# AUTOMAILER_EMAIL=your-email@gmail.com
# AUTOMAILER_PASSW=your-app-password
```

### For Render Deployment

1. Go to your **Backend Service** → **Environment** tab in Render Dashboard
2. Add the following environment variables:

| Variable | Value | Example |
|----------|-------|---------|
| `SENDGRID_API_KEY` | Your SendGrid API key | `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `SENDGRID_FROM_EMAIL` | Your verified sender email | `your-email@gmail.com` |

**Important Notes:**
- `SENDGRID_FROM_EMAIL` must be the same email you verified in Step 3
- The API key must have "Mail Send" permissions
- You can remove `AUTOMAILER_EMAIL` and `AUTOMAILER_PASSW` if you're only using SendGrid

## Step 5: Test the Configuration

### Option A: Use the Test Email Endpoint

After deployment, test the email configuration:

```
GET https://your-backend.onrender.com/api/auth/test-email?email=your-test-email@gmail.com
```

This will:
- Check if SendGrid is configured
- Test the API key
- Send a test email if everything is valid

### Option B: Test Locally

1. Make sure `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` are in your `.env` file
2. Restart your backend server
3. Call the test email endpoint:
   ```bash
   curl http://localhost:5000/api/auth/test-email?email=your-test-email@gmail.com
   ```

## How It Works

The application will automatically:

1. **Check SendGrid first** - If `SENDGRID_API_KEY` is configured, it uses SendGrid
2. **Fall back to SMTP** - If SendGrid is not configured, it tries SMTP (Gmail, etc.)
3. **Log which provider is used** - Check logs for `[EMAIL SUCCESS] Email sent via SendGrid` or `via SMTP`

## Troubleshooting

### Error: "SendGrid API key validation failed"
- **Solution**: Check that your API key is correct and has "Mail Send" permissions
- Verify the key starts with `SG.` and has no extra spaces

### Error: "Sender email not verified"
- **Solution**: Complete Step 3 (Verify Sender Identity) in SendGrid dashboard
- Make sure `SENDGRID_FROM_EMAIL` matches the verified email

### Error: "Email sent but not received"
- **Solution**: 
  - Check SendGrid dashboard → **Activity** tab to see email status
  - Check spam/junk folder
  - Verify recipient email is valid

### Still getting SMTP errors on Render free tier?
- **Solution**: Make sure `SENDGRID_API_KEY` is set in Render environment variables
- Remove or comment out `AUTOMAILER_PASSW` to force SendGrid usage

## SendGrid Free Tier Limits

- **100 emails/day** - Reset daily at midnight UTC
- **Unlimited contacts** - Store as many recipients as you need
- **Full API access** - All SendGrid features available
- **Email activity tracking** - View delivery, opens, clicks

## Upgrade to Paid Plans

If you need more than 100 emails/day:

1. Go to SendGrid Dashboard → **Settings** → **Billing**
2. Choose a paid plan:
   - **Essentials**: $19.95/month - 50,000 emails
   - **Pro**: $89.95/month - 100,000 emails
   - **Premier**: Custom pricing - Unlimited emails

## Support

- SendGrid Documentation: https://docs.sendgrid.com/
- SendGrid Support: https://support.sendgrid.com/
- Render SMTP Policy: https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports

---

**Last Updated:** 2025
**Version:** 1.0

