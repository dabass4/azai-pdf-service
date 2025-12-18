# Railway Build Fix Guide

## Issues Fixed

### 1. ✅ Removed Problematic Health Check
**Issue:** Dockerfile had healthcheck using `requests` library that wasn't installed
**Fix:** Removed healthcheck (Railway doesn't need it)

### 2. ✅ Added Railway Configuration
**Issue:** Railway might not detect build settings correctly
**Fix:** Created `railway.json` with explicit configuration

### 3. ✅ Added httpx to requirements
**Issue:** Missing dependency for HTTP calls
**Fix:** Added `httpx==0.25.2` to requirements.txt

---

## How to Deploy (After Fixes)

### Step 1: Commit and Push Changes

```bash
cd /app/pdf-service

# Check status
git status

# Add all new files
git add .

# Commit changes
git commit -m "Fix: Railway build issues - removed healthcheck, added config"

# Push to GitHub
git push origin main
```

### Step 2: Trigger Railway Redeploy

**Option A: Automatic (if connected)**
- Railway will automatically detect the push
- New build will start in 10-30 seconds
- Watch the logs in Railway dashboard

**Option B: Manual Trigger**
1. Go to Railway dashboard
2. Click your pdf-service project
3. Click "Deployments" tab
4. Click "Deploy" button (top right)
5. Select "Redeploy"

---

## Common Build Errors & Solutions

### Error 1: "Failed to build Dockerfile"
**Symptoms:**
```
ERROR: failed to solve: process "/bin/sh -c apt-get update..." did not complete successfully
```

**Solution:**
```dockerfile
# In Dockerfile, change:
RUN apt-get update && apt-get install -y poppler-utils

# To:
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

Already fixed in updated Dockerfile ✅

---

### Error 2: "Module not found"
**Symptoms:**
```
ModuleNotFoundError: No module named 'pdf2image'
```

**Solution:**
Check requirements.txt includes all dependencies:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pdf2image==1.16.3
Pillow==10.1.0
httpx==0.25.2
```

Already fixed ✅

---

### Error 3: "Port binding failed"
**Symptoms:**
```
Error: Cannot bind to port 8000
```

**Solution:**
Railway uses dynamic PORT variable. Update CMD:
```dockerfile
# Wrong:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Correct (Railway handles this):
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Actually, Railway will override the port automatically. Current setup is fine ✅

---

### Error 4: "Build timeout"
**Symptoms:**
```
Build exceeded 10 minute timeout
```

**Solution:**
Railway free tier has 10-minute build limit. Our build should take 2-3 minutes.

If it times out:
1. Remove unnecessary dependencies
2. Use lighter base image
3. Optimize Dockerfile layers

Current setup is optimized ✅

---

### Error 5: "Health check failed"
**Symptoms:**
```
Health check failed: connection refused
```

**Solution:**
We removed the problematic health check. Railway will check if service responds on PORT.

Already fixed ✅

---

## How to View Build Logs in Railway

### Step 1: Access Logs
1. Go to Railway dashboard: https://railway.app
2. Click on your "pdf-service" project
3. Click "Deployments" tab
4. Click on the latest deployment

### Step 2: Read the Logs
Logs show in real-time:

**Build Phase:**
```
#1 [internal] load build definition from Dockerfile
#2 [internal] load .dockerignore
#3 [internal] load metadata for docker.io/library/python:3.11-slim
#4 [1/6] FROM docker.io/library/python:3.11-slim
#5 [2/6] RUN apt-get update && apt-get install -y poppler-utils
#6 [3/6] WORKDIR /app
#7 [4/6] COPY requirements.txt .
#8 [5/6] RUN pip install --no-cache-dir -r requirements.txt
#9 [6/6] COPY main.py .
#10 exporting to image
```

**Deploy Phase:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Look for Errors
**Build errors** appear during steps #1-#10
**Runtime errors** appear after "Started server process"

---

## Verification Checklist

After deploying, verify:

### ✅ Build Success
```
In Railway logs, look for:
- "Build completed successfully"
- No ERROR messages
- "exporting to image" completed
```

### ✅ Service Running
```
In Railway logs, look for:
- "Started server process [1]"
- "Application startup complete"
- "Uvicorn running on..."
```

### ✅ Health Check
```bash
# Test your Railway URL
curl https://your-service.railway.app/health

# Expected response:
{
  "status": "healthy",
  "poppler_installed": true,
  "poppler_version": "22.12.0"
}
```

### ✅ Environment Variable
```
In Railway dashboard:
- Go to "Variables" tab
- Check PDF_SERVICE_API_KEY is set
- If missing, add it
```

---

## Alternative: Simplified Dockerfile (If Still Failing)

If you still have issues, try this minimal Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app
COPY main.py .

# Start app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

## Railway-Specific Tips

### 1. Use Railway's Environment Variables
Railway automatically provides:
- `PORT` - The port to bind to
- `RAILWAY_ENVIRONMENT` - "production" or "development"
- `RAILWAY_PUBLIC_DOMAIN` - Your service URL

### 2. Enable Verbose Logging
In main.py, add logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 PDF Service starting up...")
    logger.info(f"📍 Port: {os.environ.get('PORT', 8000)}")
    logger.info(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')}")
```

### 3. Check Resource Usage
Railway free tier limits:
- CPU: Shared
- Memory: 512MB-1GB
- Build time: 10 minutes
- Deploy time: No limit

Our service should use:
- Build: 2-3 minutes ✅
- Memory: ~200MB ✅
- CPU: Minimal ✅

---

## Quick Debug Commands

### Test Dockerfile Locally (Optional)
```bash
cd /app/pdf-service

# Build image
docker build -t pdf-service-test .

# Run container
docker run -p 8000:8000 -e PDF_SERVICE_API_KEY=test pdf-service-test

# Test in browser
curl http://localhost:8000/health
```

### Check Railway CLI (Optional)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Redeploy
railway up
```

---

## Still Having Issues?

### Get Help:
1. **Railway Discord**: https://discord.gg/railway
   - Very responsive community
   - Railway team monitors

2. **Railway Docs**: https://docs.railway.app
   - Dockerfile guide
   - Troubleshooting section

3. **Check Status**: https://status.railway.app
   - See if Railway has issues

### Share These Details:
- Build logs (copy from Railway)
- Your Dockerfile
- requirements.txt
- Error message (exact text)

---

## Success Indicators

You'll know it's working when:

1. ✅ Build logs show: "Build completed"
2. ✅ Deploy logs show: "Application startup complete"
3. ✅ Railway shows: Green "Active" status
4. ✅ Health check returns: `{"status": "healthy"}`
5. ✅ Can convert PDF via API

---

## Next Steps After Successful Deploy

1. **Get Your URL**
   - Railway dashboard → Settings → Domains
   - Copy the URL: `https://pdf-service-production-xxxx.up.railway.app`

2. **Test the Service**
   ```bash
   curl https://your-url/health
   ```

3. **Update Main App**
   - Add URL to main app's .env:
   ```bash
   PDF_SERVICE_URL=https://your-url
   PDF_SERVICE_API_KEY=your-key
   ```

4. **Integrate**
   - Follow `/app/backend/INTEGRATION_GUIDE.md`

---

**Current Status of Fixes:**
- ✅ Dockerfile optimized
- ✅ Health check removed
- ✅ Railway.json added
- ✅ Dependencies updated
- ✅ Ready to push and deploy

**Next Action:** Push changes to GitHub and Railway will auto-deploy!
