#!/bin/bash
# Run complete test suite for the Timesheet SaaS application
# Usage: ./scripts/run_all_tests.sh

set -e  # Exit on error

echo "=========================================="
echo "🧪 TIMESHEET SAAS - FULL TEST SUITE"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Function to run tests and track failures
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo ""
    echo "-------------------------------------------"
    echo "📝 Running: $test_name"
    echo "-------------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# 1. Backend Unit Tests
run_test "Time Utils Tests" "cd /app/backend && python3 test_time_utils.py"
run_test "Date Utils Tests" "cd /app/backend && python3 test_date_utils.py"

# 2. Backend Critical Regression Tests
run_test "Critical Regression Tests" "cd /app/backend && pytest tests/test_critical_regression.py -v -m critical"

# 3. Backend API Tests (if pytest is set up)
if [ -f "/app/backend/tests/test_api.py" ]; then
    run_test "API Integration Tests" "cd /app/backend && pytest tests/test_api.py -v"
fi

# 4. Backend Multi-tenancy Tests (if exists)
if [ -f "/app/backend/tests/test_multi_tenancy.py" ]; then
    run_test "Multi-tenancy Tests" "cd /app/backend && pytest tests/test_multi_tenancy.py -v"
fi

# 5. Frontend Tests (if Jest is configured)
if [ -f "/app/frontend/package.json" ] && grep -q "\"test\"" /app/frontend/package.json; then
    run_test "Frontend Unit Tests" "cd /app/frontend && yarn test --passWithNoTests"
fi

# Summary
echo ""
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Safe to deploy ✈️"
    exit 0
else
    echo -e "${RED}❌ $FAILED TEST SUITE(S) FAILED${NC}"
    echo ""
    echo "⚠️  DO NOT DEPLOY - Fix failing tests first"
    exit 1
fi
