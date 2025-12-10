#!/bin/bash
# AZAI Outdated Dependencies Check
# Identifies packages that have newer versions available

set -e

BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

REPORT_DIR="/app/scripts/dependency_management/reports"
mkdir -p "$REPORT_DIR"

echo "======================================"
echo "AZAI Outdated Dependencies Check"
echo "Generated: $(date)"
echo "======================================"
echo ""

# Python Backend
echo "${BLUE}[1/2] Checking Python packages...${NC}"
echo "--------------------------------------"
cd /app/backend

echo "Analyzing 154 Python packages..."
pip list --outdated --format=json > "$REPORT_DIR/outdated_python.json" 2>&1 || true

OUTDATED_COUNT=$(cat "$REPORT_DIR/outdated_python.json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$OUTDATED_COUNT" -eq "0" ]; then
    echo "${GREEN}✅ All Python packages are up to date!${NC}"
else
    echo "${YELLOW}📦 $OUTDATED_COUNT Python packages have updates available${NC}"
    echo ""
    echo "Top 10 outdated packages:"
    pip list --outdated --format=columns 2>&1 | head -15
fi
echo ""

# JavaScript Frontend
echo "${BLUE}[2/2] Checking JavaScript packages...${NC}"
echo "--------------------------------------"
cd /app/frontend

echo "Analyzing JavaScript packages..."
yarn outdated --json > "$REPORT_DIR/outdated_javascript.json" 2>&1 || true

# Get summary
OUTDATED_JS=$(yarn outdated 2>&1 | grep -c "^" || echo "0")

if [ "$OUTDATED_JS" -le "2" ]; then
    echo "${GREEN}✅ All JavaScript packages are up to date!${NC}"
else
    echo "${YELLOW}📦 JavaScript packages have updates available${NC}"
    echo ""
    yarn outdated 2>&1 | head -20
fi

echo ""
echo "======================================"
echo "Reports saved to: $REPORT_DIR"
echo "  - outdated_python.json"
echo "  - outdated_javascript.json"
echo "======================================"
