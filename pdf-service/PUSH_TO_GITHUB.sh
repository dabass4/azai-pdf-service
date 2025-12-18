#!/bin/bash
# Quick script to push PDF service to GitHub

echo "🚀 Pushing PDF Service to GitHub (dabass4/pdf-service)"
echo ""

cd /app/pdf-service

# Check if remote exists
if git remote | grep -q "origin"; then
    echo "✅ Remote 'origin' already exists"
else
    echo "📝 Adding remote: https://github.com/dabass4/pdf-service.git"
    git remote add origin https://github.com/dabass4/pdf-service.git
fi

# Ensure we're on main branch
git branch -M main

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Code pushed to GitHub"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to: https://railway.app"
    echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
    echo "3. Select: dabass4/pdf-service"
    echo "4. Railway will automatically build and deploy"
    echo ""
    echo "📊 Watch deployment logs in Railway dashboard"
else
    echo ""
    echo "❌ Push failed. Check error above."
    echo ""
    echo "Common fixes:"
    echo "- Make sure GitHub repo exists: https://github.com/dabass4/pdf-service"
    echo "- Check your GitHub authentication"
    echo "- Try: git remote set-url origin https://github.com/dabass4/pdf-service.git"
fi
