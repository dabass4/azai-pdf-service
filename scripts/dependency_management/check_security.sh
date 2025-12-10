#!/bin/bash
# AZAI Dependency Security Audit Script
# Checks for known security vulnerabilities in dependencies

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "AZAI Security Audit - $(date)"
echo "======================================"
echo ""

# Backend Python Security Audit
echo "${YELLOW}[1/2] Checking Python dependencies for vulnerabilities...${NC}"
echo "--------------------------------------"
cd /app/backend

if pip-audit --desc --format json > /tmp/pip-audit.json 2>&1; then
    echo "${GREEN}✅ No Python security vulnerabilities found!${NC}"
    echo ""
else
    echo "${RED}⚠️  Security vulnerabilities detected in Python packages!${NC}"
    pip-audit --desc
    echo ""
    echo "Full report saved to: /app/scripts/dependency_management/reports/security_python.json"
    mkdir -p /app/scripts/dependency_management/reports
    cp /tmp/pip-audit.json /app/scripts/dependency_management/reports/security_python.json
fi

# Frontend JavaScript Security Audit
echo "${YELLOW}[2/2] Checking JavaScript dependencies for vulnerabilities...${NC}"
echo "--------------------------------------"
cd /app/frontend

if yarn audit --json > /tmp/yarn-audit.json 2>&1; then
    echo "${GREEN}✅ No JavaScript security vulnerabilities found!${NC}"
    echo ""
else
    AUDIT_SUMMARY=$(yarn audit --summary 2>&1 | grep -E "Severity|vulnerabilities found" || echo "Check detailed report")
    echo "${RED}⚠️  Security vulnerabilities detected in JavaScript packages!${NC}"
    echo "$AUDIT_SUMMARY"
    echo ""
    echo "Run 'cd /app/frontend && yarn audit' for detailed information"
    mkdir -p /app/scripts/dependency_management/reports
    cp /tmp/yarn-audit.json /app/scripts/dependency_management/reports/security_javascript.json
fi

echo "======================================"
echo "Security audit complete!"
echo "======================================"
