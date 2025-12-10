#!/bin/bash
# AZAI Security Update Script
# Applies critical security patches automatically

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "AZAI Security Patch Update"
echo "$(date)"
echo "======================================"
echo ""
echo "${YELLOW}⚠️  This script will update packages with security vulnerabilities${NC}"
echo "${YELLOW}⚠️  Backup recommended before proceeding${NC}"
echo ""

read -p "Continue with security updates? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Update cancelled."
    exit 0
fi

echo ""
echo "${GREEN}Starting security updates...${NC}"
echo ""

# Python Security Updates
echo "[1/2] Updating Python packages with vulnerabilities..."
cd /app/backend

# Get list of vulnerable packages
if pip-audit --fix --dry-run 2>&1 | grep -q "would fix"; then
    echo "${YELLOW}Applying Python security fixes...${NC}"
    pip-audit --fix
    
    # Update requirements.txt
    pip freeze > requirements.txt
    echo "${GREEN}✅ Python packages updated and requirements.txt regenerated${NC}"
else
    echo "${GREEN}✅ No Python security updates needed${NC}"
fi

echo ""

# JavaScript Security Updates
echo "[2/2] Updating JavaScript packages with vulnerabilities..."
cd /app/frontend

if yarn audit --json 2>&1 | grep -q '"type":"auditSummary"'; then
    echo "${YELLOW}Applying JavaScript security fixes...${NC}"
    yarn audit --fix
    echo "${GREEN}✅ JavaScript packages updated${NC}"
else
    echo "${GREEN}✅ No JavaScript security updates needed${NC}"
fi

echo ""
echo "======================================"
echo "${GREEN}Security updates complete!${NC}"
echo "======================================"
echo ""
echo "${YELLOW}Next steps:${NC}"
echo "1. Restart services: sudo supervisorctl restart backend frontend"
echo "2. Run tests: /app/scripts/run_all_tests.sh"
echo "3. Verify functionality"
echo ""
