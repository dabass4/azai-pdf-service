# Quick Command Reference - PDF Service Deployment

## Your GitHub Repository
**URL:** https://github.com/dabass4/pdf-service

---

## 🚀 Deploy to Railway (3 Commands)

### Option 1: Use the Script (Easiest)
```bash
cd /app/pdf-service
./PUSH_TO_GITHUB.sh
```

### Option 2: Manual Commands
```bash
cd /app/pdf-service

# Add remote (if not already added)
git remote add origin https://github.com/dabass4/pdf-service.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 📝 Before First Push

### 1. Create GitHub Repository
Go to: https://github.com/new
- Repository name: `pdf-service`
- Visibility: Public (for Railway free tier)
- Don't initialize with README

### 2. Verify Your Files
```bash
cd /app/pdf-service
ls -la

# You should see:
# - main.py
# - Dockerfile
# - requirements.txt
# - railway.json
# - README.md
```

---

## 🔄 Update After Changes

If you make changes to the code:

```bash
cd /app/pdf-service

# Check what changed
git status

# Add changes
git add .

# Commit with message
git commit -m "Your change description"

# Push to GitHub
git push origin main
```

Railway will automatically redeploy after each push!

---

## 🔍 Check Git Status

```bash
cd /app/pdf-service

# Check current branch
git branch

# Check remote URL
git remote -v

# Check commit history
git log --oneline -5
```

---

## 🆘 Fix Common Issues

### Issue: "remote origin already exists"
```bash
cd /app/pdf-service
git remote remove origin
git remote add origin https://github.com/dabass4/pdf-service.git
```

### Issue: "failed to push"
```bash
# Force push (use carefully!)
git push -f origin main
```

### Issue: "repository not found"
Make sure you've created the repo at:
https://github.com/dabass4/pdf-service

---

## 🎯 After Successful Push

### 1. Connect to Railway
1. Go to: https://railway.app
2. Login with GitHub
3. New Project → Deploy from GitHub repo
4. Select: `dabass4/pdf-service`
5. Click "Deploy"

### 2. Watch Build Logs
- Railway dashboard → Click your project
- View real-time logs
- Wait 3-5 minutes for build

### 3. Get Your Service URL
- Railway dashboard → Settings → Domains
- Click "Generate Domain"
- Copy URL: `https://pdf-service-production-xxxx.up.railway.app`

### 4. Set Environment Variable
- Railway dashboard → Variables tab
- Add variable:
  - Name: `PDF_SERVICE_API_KEY`
  - Value: `your-secure-api-key`

### 5. Test Your Service
```bash
curl https://your-railway-url/health
```

---

## 📊 Railway Deployment Status

After pushing, check:

**Dashboard:** https://railway.app/dashboard

**Look for:**
- ✅ Green "Active" badge
- ✅ "Application startup complete" in logs
- ✅ Public domain assigned

---

## 🔗 Quick Links

- **GitHub Repo:** https://github.com/dabass4/pdf-service
- **Railway Dashboard:** https://railway.app
- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway

---

## 📞 Get Help

If deployment fails:
1. Check `/app/pdf-service/RAILWAY_BUILD_FIX.md`
2. View Railway logs for error message
3. Ask in Railway Discord (very helpful!)

---

**Current Status:**
- ✅ Code ready
- ✅ Git configured
- ✅ Build issues fixed
- ✅ GitHub username set: dabass4
- 🎯 Ready to push!
