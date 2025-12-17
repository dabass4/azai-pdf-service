# 🚀 Railway Deployment Checklist - STEP BY STEP

## ✅ Step 1: Create GitHub Repository (3 minutes)

1. Go to https://github.com/new
2. Repository name: `pdf-service` (or any name you prefer)
3. Description: "PDF processing microservice for AZAI"
4. **Make it Public** (required for Railway free tier) or Private (if you have Railway Pro)
5. **DO NOT** initialize with README (we already have files)
6. Click "Create repository"

## ✅ Step 2: Push Code to GitHub (2 minutes)

GitHub will show you commands. Copy and run these in your terminal:

```bash
cd /app/pdf-service

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/pdf-service.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your GitHub username!**

## ✅ Step 3: Deploy to Railway (5 minutes)

### 3.1 Sign Up / Login
1. Go to https://railway.app
2. Click "Login" or "Start a New Project"
3. **Sign in with GitHub** (easiest option)
4. Authorize Railway to access your GitHub

### 3.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Find and select your `pdf-service` repository
4. Railway will **automatically detect** the Dockerfile
5. Click "Deploy"

### 3.3 Wait for Deployment
- Railway will:
  - ✅ Build Docker image
  - ✅ Install poppler-utils
  - ✅ Deploy to their infrastructure
- This takes **2-3 minutes**
- Watch the deployment logs (they're live!)

## ✅ Step 4: Configure Environment Variables (2 minutes)

1. In Railway dashboard, click on your deployed service
2. Go to "Variables" tab
3. Click "Add Variable"
4. Add this variable:
   ```
   PDF_SERVICE_API_KEY = your-super-secret-key-change-this-123456
   ```
   **Important:** Use a strong, random key! You can generate one with:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Railway will **automatically redeploy** with new variable

## ✅ Step 5: Get Your Service URL (1 minute)

1. In Railway dashboard, click "Settings" tab
2. Scroll to "Domains" section
3. Click "Generate Domain"
4. Railway will give you a URL like:
   ```
   https://pdf-service-production-xxxx.up.railway.app
   ```
5. **Copy this URL** - you'll need it!

## ✅ Step 6: Test Your Service (2 minutes)

### Test 1: Health Check
```bash
curl https://your-railway-url.railway.app/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "poppler_installed": true,
  "poppler_version": "22.12.0"
}
```

### Test 2: Convert a PDF
Create a simple test PDF first:

```bash
cd /tmp
echo "Test PDF content" > test.txt

# Create a simple PDF (using Python)
python3 << 'EOF'
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("test.pdf", pagesize=letter)
c.drawString(100, 750, "Test Timesheet")
c.drawString(100, 730, "Employee: John Doe")
c.save()
print("✅ test.pdf created")
EOF
```

Now test the conversion:
```bash
# Replace with your actual Railway URL and API key
RAILWAY_URL="https://your-service.railway.app"
API_KEY="your-api-key-here"

curl -X POST "$RAILWAY_URL/api/v1/pdf/convert" \
  -H "Authorization: Bearer $API_KEY" \
  -F "file=@test.pdf" \
  -F "dpi=200"
```

**Expected:** JSON response with `"status": "completed"` and base64 images

## ✅ Step 7: Integrate with Main Application (5 minutes)

### 7.1 Update Main App Environment Variables

Add to your main application's `.env` file:
```bash
PDF_SERVICE_URL=https://your-railway-url.railway.app
PDF_SERVICE_API_KEY=your-api-key-here
```

### 7.2 Install httpx in Main App (if not already installed)

```bash
cd /app/backend
pip install httpx
pip freeze > requirements.txt
```

### 7.3 Update Main App Code

I'll create a new integration file for you in the next step.

---

## 🎯 Success Criteria

You're done when:
- ✅ `/health` endpoint returns "healthy"
- ✅ Test PDF converts successfully
- ✅ You have Railway URL and API key saved
- ✅ Service is running (check Railway dashboard)

---

## 🆘 Troubleshooting

### Issue: "poppler-utils not found"
**Solution:** Check Dockerfile includes `apt-get install -y poppler-utils`

### Issue: "Authorization failed"
**Solution:** Make sure API_KEY environment variable is set in Railway

### Issue: "Cannot connect to service"
**Solution:** 
1. Check Railway dashboard - is service running?
2. Check deployment logs for errors
3. Make sure you generated a domain in Railway settings

### Issue: "File too large"
**Solution:** Service has 50MB limit. For larger files, increase in `main.py`

---

## 📊 Monitoring

Railway provides:
- **Logs**: Click "Deployments" → View logs
- **Metrics**: CPU, Memory usage in dashboard
- **Alerts**: Set up in Railway settings

---

## 💰 Cost Tracking

Railway shows:
- **Current usage** in dashboard
- **Estimated monthly cost**
- **$5 free credit** per month

For development, you'll likely stay within free tier!

---

## 🔄 Making Updates

To update the service:
```bash
cd /app/pdf-service

# Make your changes to main.py or other files

git add .
git commit -m "Update: your changes"
git push

# Railway automatically redeploys! 🎉
```

---

## ⏭️ Next Steps After Deployment

1. ✅ Save Railway URL and API key securely
2. ⏳ Integrate with main application (see Step 7)
3. ⏳ Test with real timesheet PDFs
4. ⏳ Monitor logs for first 24 hours
5. ⏳ Set up alerts in Railway

---

## 📞 Need Help?

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **This Service Docs**: See README.md in this repo

---

**Total Time: ~15 minutes**
**Cost: FREE (within $5 credit)**
**Difficulty: Easy ⭐⭐☆☆☆**

Let's go! 🚀
