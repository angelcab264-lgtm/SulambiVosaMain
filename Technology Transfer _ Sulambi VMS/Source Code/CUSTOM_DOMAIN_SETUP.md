# Custom Domain Setup Guide for Render

## Problem: "This domain already exists on another site"

This error occurs when the domain you're trying to add is already configured on another Render service. Here's how to fix it:

## Step 1: Find Which Service Has Your Domain

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on **"Services"** in the left sidebar
3. Look through **ALL** your services (both active and inactive)
4. For each service, click on it and go to the **"Settings"** tab
5. Scroll down to the **"Custom Domains"** section
6. Check if `www.sulambi-vosa.com` or `sulambi-vosa.com` is listed there

**Common places to check:**
- `sulambi-backend1` (backend service)
- `sulambi-vosa` (frontend static site)
- `sulambi-frontend` (frontend web service)
- Any old or test services you may have created

## Step 2: Remove Domain from the Wrong Service

Once you find which service has your domain:

1. Go to that service's **Settings** tab
2. Scroll to **"Custom Domains"** section
3. Find your domain (`www.sulambi-vosa.com` or `sulambi-vosa.com`)
4. Click the **trash/delete icon** next to the domain
5. Confirm the deletion

**⚠️ Important:** Make sure you're removing it from the **wrong** service (e.g., if it's on the backend, remove it from there since you want it on the frontend).

## Step 3: Add Domain to the Correct Service

### For Frontend Service (Recommended)

You typically want your custom domain on the **frontend** service:

1. Go to your **frontend service** (`sulambi-vosa` or `sulambi-frontend`)
2. Go to **Settings** → **Custom Domains**
3. Click **"Add Custom Domain"**
4. Enter your domain:
   - For root domain: `sulambi-vosa.com`
   - For www subdomain: `www.sulambi-vosa.com`
   - You can add both if needed
5. Click **"Save"**

### For Backend Service (If Needed)

If you want a custom domain for your backend API:

1. Go to your **backend service** (`sulambi-backend1`)
2. Go to **Settings** → **Custom Domains**
3. Add domain: `api.sulambi-vosa.com` (or your preferred subdomain)
4. Click **"Save"**

## Step 4: Configure DNS Records

After adding the domain, Render will show you the DNS records you need to add:

### Option A: Using Your Domain Provider's DNS (Recommended)

1. Go to your domain registrar (where you bought `sulambi-vosa.com`)
2. Navigate to **DNS Management** or **DNS Settings**
3. Add the DNS records Render provides:

   **For Root Domain (`sulambi-vosa.com`):**
   ```
   Type: CNAME
   Host: @
   Value: sulambi-vosa.onrender.com
   TTL: 1 min (or 3600)
   ```

   **For WWW Subdomain (`www.sulambi-vosa.com`):**
   ```
   Type: CNAME
   Host: www
   Value: sulambi-vosa.onrender.com
   TTL: 1 min (or 3600)
   ```

   **OR if Render provides an A record:**
   ```
   Type: A
   Host: @
   Value: [IP address from Render]
   TTL: 1 min
   ```

4. **Save** the DNS records
5. Wait 5-60 minutes for DNS propagation

### Option B: Using Render's DNS (If Available)

If your domain provider supports it, you can point your nameservers to Render's DNS servers (Render will provide these).

## Step 5: Verify DNS Configuration

1. Go back to Render → Your Service → Settings → Custom Domains
2. You should see your domain with a status indicator
3. Wait for it to show **"Verified"** (green checkmark)
   - This can take 5-60 minutes depending on DNS propagation

## Step 6: Update Environment Variables (If Backend Domain Changed)

If you added a custom domain to your **backend** service:

1. Go to **Frontend Service** → **Environment** tab
2. Update `VITE_API_URI` to use your new backend domain:
   ```
   https://api.sulambi-vosa.com/api
   ```
   (Replace with your actual backend custom domain)
3. Click **"Save Changes"**
4. The frontend will automatically rebuild

## Troubleshooting

### Domain Still Shows as "Already Exists"

1. **Check all services** - including old/inactive ones
2. **Check if domain is pending deletion** - sometimes it takes a few minutes
3. **Try a different subdomain first** - e.g., `app.sulambi-vosa.com` to test
4. **Contact Render Support** - if you're sure it's not on any service

### DNS Not Working After 1 Hour

1. **Verify DNS records** are correct in your domain provider
2. **Check DNS propagation** using tools like:
   - https://dnschecker.org
   - https://www.whatsmydns.net
3. **Clear DNS cache** on your computer:
   ```powershell
   ipconfig /flushdns
   ```
4. **Try different DNS servers** (Google: 8.8.8.8, Cloudflare: 1.1.1.1)

### SSL Certificate Issues

**Error: `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`**

This error means the SSL certificate hasn't been provisioned yet or DNS isn't fully propagated. Here's how to fix it:

#### Step 1: Verify DNS is Correct
1. Check your DNS records are correct at your domain provider
2. Use a DNS checker: https://dnschecker.org
3. Enter your domain: `sulambi-vosa.com`
4. Verify it points to Render's servers (should show `sulambi-vosa.onrender.com` or Render's IP)

#### Step 2: Check Domain Status in Render
1. Go to your service → Settings → Custom Domains
2. Check the status of your domain:
   - **"Pending"** = DNS not verified yet, wait 5-60 minutes
   - **"Verified"** = DNS is correct, SSL is provisioning
   - **"Active"** = Everything is working

#### Step 3: Force SSL Certificate Provision
1. In Render → Settings → Custom Domains
2. If domain shows "Verified" but SSL isn't working:
   - Remove the domain (click delete)
   - Wait 2-3 minutes
   - Add it back again
   - This forces Render to re-provision the SSL certificate

#### Step 4: Wait for SSL Provisioning
- SSL certificates are automatically provisioned by Let's Encrypt
- This can take **5 minutes to 24 hours** after DNS is verified
- Render will show SSL status in the Custom Domains section

#### Step 5: Test HTTPS
1. Try accessing: `https://sulambi-vosa.com`
2. If still not working, try: `https://www.sulambi-vosa.com`
3. Clear your browser cache and try again
4. Try in incognito/private mode

#### Step 6: Check Browser/Network Issues
1. **Clear browser cache:**
   - Chrome: Ctrl+Shift+Delete → Clear cached images and files
   - Or use incognito mode
2. **Flush DNS cache:**
   ```powershell
   ipconfig /flushdns
   ```
3. **Try different browser** (Chrome, Firefox, Edge)
4. **Try different network** (mobile hotspot, different WiFi)

#### Step 7: Verify SSL Certificate Details
1. Go to: https://www.ssllabs.com/ssltest/
2. Enter your domain: `sulambi-vosa.com`
3. Check the SSL test results
4. Look for any errors or warnings

#### Common Causes:
- **DNS not fully propagated** - Wait longer (up to 24 hours)
- **Wrong DNS records** - Verify CNAME/A records are correct
- **Domain on wrong service** - Make sure it's on frontend, not backend
- **Browser cache** - Clear cache and try again
- **Network firewall** - Try different network
- **Let's Encrypt rate limit** - If you added/removed domain multiple times, wait 1 hour

#### If Still Not Working After 24 Hours:
1. Contact Render Support: https://render.com/support
2. Provide them:
   - Your service name
   - Domain name
   - Screenshot of Custom Domains section
   - DNS records you've configured

## Recommended Setup

### Frontend Service
- **Custom Domain:** `www.sulambi-vosa.com` (or `sulambi-vosa.com`)
- **DNS:** CNAME pointing to `sulambi-vosa.onrender.com`

### Backend Service (Optional)
- **Custom Domain:** `api.sulambi-vosa.com`
- **DNS:** CNAME pointing to `sulambi-backend1.onrender.com`
- **Update Frontend:** Set `VITE_API_URI` to `https://api.sulambi-vosa.com/api`

## Quick Checklist

- [ ] Found which service has the domain
- [ ] Removed domain from wrong service
- [ ] Added domain to correct service
- [ ] Added DNS records at domain provider
- [ ] Waited for DNS propagation (5-60 min)
- [ ] Verified domain shows "Verified" in Render
- [ ] Updated `VITE_API_URI` if backend domain changed
- [ ] Tested the domain in browser

## Need Help?

- **Render Documentation:** https://render.com/docs/custom-domains
- **Render Support:** https://render.com/support
- **DNS Propagation Checker:** https://dnschecker.org

