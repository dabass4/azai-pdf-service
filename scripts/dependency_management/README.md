# AZAI Dependency Management System

## Overview

This directory contains automated scripts for managing and monitoring dependencies in the AZAI healthcare timesheet application.

## Scripts

### 🔒 Security Monitoring

#### `check_security.sh`
Scans for known security vulnerabilities in both Python and JavaScript dependencies.

**Usage:**
```bash
/app/scripts/dependency_management/check_security.sh
```

**Frequency:** Run daily or before each deployment

**Output:** Console report + JSON files in `reports/` directory

---

### 📦 Update Checking

#### `check_outdated.sh`
Identifies packages with newer versions available.

**Usage:**
```bash
/app/scripts/dependency_management/check_outdated.sh
```

**Frequency:** Run weekly

**Output:** 
- Lists outdated packages
- Saves JSON reports for analysis

---

### 📊 Comprehensive Reporting

#### `generate_report.sh`
Creates a detailed markdown report combining security status, outdated packages, and recommendations.

**Usage:**
```bash
/app/scripts/dependency_management/generate_report.sh
```

**Frequency:** Run monthly or before planning updates

**Output:** Timestamped markdown report in `reports/` directory

**View latest report:**
```bash
cat /app/scripts/dependency_management/reports/dependency_status_latest.md
```

---

### 🔄 Security Updates

#### `update_security.sh`
Automatically applies security patches to vulnerable packages.

**Usage:**
```bash
/app/scripts/dependency_management/update_security.sh
```

**⚠️ CAUTION:** This modifies your dependencies. Always:
1. Review changes before applying
2. Run in development/staging first
3. Test thoroughly after updates
4. Have a rollback plan

**Frequency:** Run immediately when vulnerabilities are detected

---

## Recommended Schedule

| Frequency | Action | Script |
|-----------|--------|--------|
| **Daily** | Security scan | `check_security.sh` |
| **Weekly** | Check outdated | `check_outdated.sh` |
| **Monthly** | Full report | `generate_report.sh` |
| **As Needed** | Security updates | `update_security.sh` |
| **Quarterly** | Review major updates | Manual review of report |

---

## For Healthcare/Medicaid Compliance

### Priority Levels

1. **🔴 Critical Security** (Immediate)
   - CVSS Score 7.0+
   - Known exploits
   - Data exposure risks

2. **🟡 Important Updates** (Within 30 days)
   - Security patches (CVSS < 7.0)
   - Critical bug fixes
   - Dependency conflicts

3. **🟢 Enhancement Updates** (Quarterly)
   - New features
   - Performance improvements
   - Major version upgrades

### Update Process

```
1. Scan → 2. Review → 3. Test (Dev) → 4. Test (Staging) → 5. Deploy (Prod)
```

### Testing Checklist

After any dependency update:

- [ ] Backend services start successfully
- [ ] Frontend builds without errors
- [ ] PDF timesheet upload works
- [ ] Authentication flows work
- [ ] Admin panel accessible
- [ ] Claims submission functions
- [ ] Database connections stable
- [ ] API endpoints respond correctly

---

## Reports Directory

All generated reports are saved in:
```
/app/scripts/dependency_management/reports/
```

**Files:**
- `security_python.json` - Latest Python security audit
- `security_javascript.json` - Latest JavaScript security audit
- `outdated_python.json` - Outdated Python packages
- `outdated_javascript.json` - Outdated JavaScript packages
- `dependency_status_YYYYMMDD_HHMMSS.md` - Timestamped full reports
- `dependency_status_latest.md` - Symlink to most recent report

---

## Integration with CI/CD

To automate these checks in your deployment pipeline:

```yaml
# Example: Run before each deployment
pre-deploy:
  - /app/scripts/dependency_management/check_security.sh
  - if [ $? -ne 0 ]; then exit 1; fi
```

---

## Troubleshooting

### Script won't run
```bash
chmod +x /app/scripts/dependency_management/*.sh
```

### pip-audit not found
```bash
cd /app/backend && pip install pip-audit
```

### Permission errors
```bash
sudo chown -R $USER:$USER /app/scripts/dependency_management
```

---

## Support

For questions or issues with dependency management:
1. Review the generated reports
2. Check package changelogs
3. Test in isolated environment first
4. Consult package documentation

---

*Last Updated: $(date '+%Y-%m-%d')*
