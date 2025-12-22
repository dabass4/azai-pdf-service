# AZAI Dependency Management - Quick Reference

---

## 🚀 QUICK COMMANDS

### Daily Security Scan
```bash
/app/scripts/dependency_management/check_security.sh
```

### Weekly Outdated Check
```bash
/app/scripts/dependency_management/check_outdated.sh
```

### Monthly Full Report
```bash
/app/scripts/dependency_management/generate_report.sh
cat /app/scripts/dependency_management/reports/dependency_status_latest.md
```

### Apply Security Updates (With Caution)
```bash
/app/scripts/dependency_management/update_security.sh
```

---

## 🔥 EMERGENCY SECURITY FIX

**Current Critical Vulnerabilities: 7**

### One-Line Fix (All Critical Patches):
```bash
cd /app/backend && \
pip install --upgrade pymongo==4.6.3 python-socketio==5.14.0 urllib3==2.6.0 fastapi==0.124.0 && \
pip freeze > requirements.txt && \
sudo supervisorctl restart backend
```

### Verify Fix:
```bash
/app/scripts/dependency_management/check_security.sh
```

### Test Upload Feature:
```bash
curl -X POST https://medicaid-claims.preview.emergentagent.com/api/timesheets/upload \
  -F "file=@/tmp/test_timesheet.pdf" \
  -F "organization_id=test-org"
```

---

## 📋 MAINTENANCE SCHEDULE

| Day | Task | Time |
|-----|------|------|
| **Monday** | Security scan | 5 min |
| **Friday** | Check outdated packages | 5 min |
| **1st of Month** | Full report + plan updates | 30 min |

---

## 🛠 COMMON TASKS

### Update Single Package
```bash
cd /app/backend
pip install --upgrade PACKAGE_NAME==VERSION
pip freeze > requirements.txt
sudo supervisorctl restart backend
```

### Update JavaScript Package
```bash
cd /app/frontend
yarn upgrade PACKAGE_NAME@^VERSION
sudo supervisorctl restart frontend
```

### Check Package Version
```bash
# Python
pip show PACKAGE_NAME

# JavaScript
yarn list PACKAGE_NAME
```

### View Logs After Update
```bash
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

---

## ✅ POST-UPDATE CHECKLIST

After updating dependencies:

```bash
# 1. Restart services
sudo supervisorctl restart backend frontend

# 2. Check services are running
sudo supervisorctl status

# 3. Test critical endpoints
curl https://medicaid-claims.preview.emergentagent.com/api/health

# 4. Check for errors
tail -n 50 /var/log/supervisor/backend.err.log

# 5. Test PDF upload
# (Use test file or frontend)

# 6. Re-run security audit
/app/scripts/dependency_management/check_security.sh
```

---

## 🔍 TROUBLESHOOTING

### Package Won't Update
```bash
pip install --upgrade --force-reinstall PACKAGE_NAME
```

### Service Won't Start After Update
```bash
# Check logs
tail -n 100 /var/log/supervisor/backend.err.log

# Restart all
sudo supervisorctl restart all

# Check pip install errors
pip check
```

### Dependency Conflict
```bash
# Show dependency tree
pip show PACKAGE_NAME

# Check conflicts
pip check
```

### Need to Rollback
```bash
# Use Emergent platform rollback feature
# OR manually:
cd /app/backend
pip install PACKAGE_NAME==OLD_VERSION
pip freeze > requirements.txt
sudo supervisorctl restart backend
```

---

## 📊 CURRENT STATUS (Dec 10, 2025)

### 🔴 Security Issues: 7 vulnerabilities
- pymongo, python-socketio, starlette (2), urllib3 (2), ecdsa

### 📦 Outdated: 46 Python packages, 14+ JS packages

### ✅ Stable: poppler-utils, MongoDB

---

## 📚 DOCUMENTATION LINKS

- **Full Action Plan:** `/app/DEPENDENCY_MANAGEMENT_ACTION_PLAN.md`
- **Vulnerability Details:** `/app/scripts/dependency_management/SECURITY_VULNERABILITIES_DETAIL.md`
- **Tool Documentation:** `/app/scripts/dependency_management/README.md`
- **Latest Report:** `/app/scripts/dependency_management/reports/dependency_status_latest.md`

---

## 🎯 PRIORITY MATRIX

| Priority | Action | Timeframe |
|----------|--------|-----------|
| 🔴 P0 | Fix pymongo, starlette, urllib3 | This week |
| 🟡 P1 | Update python-socketio | Next week |
| 🟢 P2 | Update minor versions | Monthly |
| 🔵 P3 | Evaluate major updates | Quarterly |

---

## 🆘 NEED HELP?

1. **Read the docs** in `/app/scripts/dependency_management/`
2. **Check package changelog** on PyPI or npm
3. **Review detailed vulnerability report**
4. **Test in isolated environment first**
5. **Have rollback plan ready**

---

**Quick Access:**
```bash
# View this file anytime
cat /app/scripts/dependency_management/QUICK_REFERENCE.md

# View full action plan
cat /app/DEPENDENCY_MANAGEMENT_ACTION_PLAN.md

# Get latest security report
/app/scripts/dependency_management/check_security.sh
```

---

*Last Updated: December 10, 2025*
