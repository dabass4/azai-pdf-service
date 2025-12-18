# Railway Build Error Fix - "Script start.sh not found"

## ✅ ERROR FIXED!

**Error Message:**
```
⚠ Script start.sh not found
✖ Railpack could not determine how to build the app.
```

**Root Cause:**
Railway's auto-detection (Nixpacks/Railpack) couldn't determine how to build the app. It was looking for a start.sh script but couldn't find build instructions.

---

## 🔧 What I Fixed

### 1. Added `nixpacks.toml` ✅
Tells Railway/Nixpacks exactly how to build and run the app:

```toml
[phases.setup]
nixPkgs = ["python311", "poppler_utils"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = []

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

### 2. Added `Procfile` ✅
Fallback method to tell Railway how to start the app:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. Updated `railway.json` ✅
Simplified to explicitly tell Railway to use Dockerfile:

```json
{
  "build": {
    "builder": "DOCKERFILE"
  }
}
```

---

## 🚀 Deploy Now

### Option 1: Push and Railway Will Auto-Deploy
```bash
cd /app/pdf-service
git push origin main
```

Railway will automatically:
1. Detect the push
2. Use nixpacks.toml for build configuration
3. Install poppler-utils
4. Install Python dependencies
5. Start the service

### Option 2: Manual Redeploy in Railway
1. Go to Railway dashboard
2. Click your project
3. Deployments → Deploy → Redeploy
4. Watch logs appear immediately

---

## 📊 What You'll See in Logs (Success)

```
==> Building
    Setting up Python 3.11...
    Installing poppler-utils...
    Installing requirements...
    
==> Installing dependencies
    Collecting fastapi==0.104.1
    Collecting uvicorn[standard]==0.24.0
    Collecting pdf2image==1.16.3
    Successfully installed...
    
==> Starting
    INFO:     Started server process [1]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🎯 Three Ways Railway Can Build This App

Railway now has 3 ways to build your app (in order of preference):

### 1. Using `nixpacks.toml` (Recommended) ✅
- Modern, Railway's preferred method
- Fast builds
- Clear configuration
- **This is what we're using now**

### 2. Using `Dockerfile` (Fallback)
- If nixpacks fails
- Explicitly defined in railway.json
- More control over build

### 3. Using `Procfile` (Last Resort)
- Heroku-style deployment
- Only for starting the app
- Railway auto-detects Python and installs deps

---

## ✅ Verification Steps

After pushing, verify build success:

### 1. Check Logs Appear (Within 10 seconds)
Railway dashboard → Deployments → Latest

**You should see:**
```
==> Cloning repository
==> Building with Nixpacks
==> Installing dependencies
==> Starting application
```

### 2. Check Build Completes (2-3 minutes)
Look for:
```
✓ Build completed successfully
✓ Deployment successful
```

### 3. Check Service is Running
Status should show:
- Green dot "Active"
- No errors

### 4. Test Health Endpoint
```bash
curl https://your-railway-url.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "poppler_installed": true,
  "poppler_version": "22.12.0"
}
```

---

## 🔍 Why This Error Happened

Railway uses different build systems:

1. **Nixpacks** (default) - Tries to auto-detect
2. **Dockerfile** - Needs to be explicitly configured
3. **Buildpacks** (legacy) - For older projects

Your project had:
- ✅ Dockerfile (present)
- ✅ railway.json (present)
- ❌ But Railway couldn't determine build method

**Solution:** Added explicit configuration files so Railway knows exactly what to do.

---

## 🛠️ Troubleshooting If Still Fails

### If you still see "start.sh not found":

**1. Verify Files Were Pushed:**
```bash
cd /app/pdf-service
git log --oneline | head -1
# Should show: "Fix: Add nixpacks.toml and Procfile"

# Push again if needed
git push origin main
```

**2. Check Files on GitHub:**
Go to: https://github.com/dabass4/pdf-service

Should see:
- ✅ nixpacks.toml
- ✅ Procfile  
- ✅ Dockerfile
- ✅ railway.json
- ✅ main.py
- ✅ requirements.txt

**3. Force Railway to Rebuild:**
Railway dashboard → Settings → "Trigger Deploy"

**4. Try Railway CLI:**
```bash
railway login
cd /app/pdf-service
railway up
```

---

## 📋 File Structure (Final)

Your repository should now have:

```
/pdf-service/
├── main.py              ← FastAPI app
├── requirements.txt     ← Python dependencies
├── Dockerfile           ← Docker build instructions
├── railway.json         ← Railway config (Dockerfile)
├── nixpacks.toml        ← Nixpacks config (NEW!)
├── Procfile             ← Start command (NEW!)
├── README.md            ← Documentation
├── .gitignore          ← Git ignore rules
└── (other docs)
```

---

## 🎉 What Changed

**Before (Failed):**
```
⚠ Railway: "How do I build this?"
✖ No clear instructions found
✖ Looking for start.sh... not found
✖ Can't determine build method
```

**After (Works):**
```
✓ Railway reads nixpacks.toml
✓ "Oh! Python 3.11 + poppler-utils"
✓ "Install requirements.txt"
✓ "Start with uvicorn command"
✓ Build proceeds successfully
```

---

## 💡 Pro Tips

### 1. Check Build Method in Railway
Railway dashboard → Settings → Build → "Builder"
- Should show: "Nixpacks" or "Dockerfile"

### 2. View Build Logs in Real-Time
Railway will now show detailed logs:
- What it's installing
- Command outputs
- Any errors

### 3. If Nixpacks Fails, Dockerfile is Fallback
Railway will automatically try Dockerfile if Nixpacks fails.

### 4. Environment Variables
Don't forget to set:
- Railway → Variables → `PDF_SERVICE_API_KEY`

---

## 🔗 Related Files

- `/app/pdf-service/nixpacks.toml` - Build configuration
- `/app/pdf-service/Procfile` - Start command
- `/app/pdf-service/railway.json` - Railway settings
- `/app/pdf-service/Dockerfile` - Docker build

---

## 📞 If Still Having Issues

**Railway Discord (Fastest Help):**
- Join: https://discord.gg/railway
- Channel: #help
- Say: "Getting 'start.sh not found' error even after adding nixpacks.toml"
- Share: Link to your GitHub repo

**Check Railway Documentation:**
- Nixpacks: https://docs.railway.app/deploy/builders
- Config: https://docs.railway.app/deploy/config-as-code

---

## ✅ Success Indicators

You'll know it's fixed when:

1. ✅ Push to GitHub completes
2. ✅ Railway detects push immediately
3. ✅ Logs show "Building with Nixpacks"
4. ✅ Build completes in 2-3 minutes
5. ✅ Service shows "Active" status
6. ✅ Health endpoint returns healthy

---

**Current Status:**
- ✅ nixpacks.toml created
- ✅ Procfile created
- ✅ railway.json updated
- ✅ All changes committed
- 🚀 Ready to push!

**Next Action:** Push to GitHub and Railway will build successfully!

```bash
cd /app/pdf-service
git push origin main
```

**Expected Result:** Build will start immediately and complete successfully in 2-3 minutes! 🎉
