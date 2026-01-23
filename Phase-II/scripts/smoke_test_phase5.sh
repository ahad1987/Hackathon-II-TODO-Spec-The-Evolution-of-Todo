#!/bin/bash
# Phase V Smoke Test Script (T070)
# Tests all Phase V services to ensure they're operational

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Service endpoints
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
RECURRING_URL="${RECURRING_URL:-http://localhost:8001}"
REMINDER_URL="${REMINDER_URL:-http://localhost:8002}"
NOTIFICATION_URL="${NOTIFICATION_URL:-http://localhost:8003}"
AUDIT_URL="${AUDIT_URL:-http://localhost:8004}"

echo -e "${YELLOW}Phase V Smoke Test Suite${NC}"
echo "========================================"

TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    echo -n "Testing ${name}... "
    code=$(curl -s -o /dev/null -w "%{http_code}" "${url}")
    if [ "$code" -eq 200 ]; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAIL (HTTP ${code})${NC}"
        ((TESTS_FAILED++))
    fi
}

echo ""
echo "1. Health Checks"
echo "-----------------------------------"
test_endpoint "Main Backend" "${BACKEND_URL}/health"
test_endpoint "Recurring Processor" "${RECURRING_URL}/health/live"
test_endpoint "Reminder Service" "${REMINDER_URL}/health/live"
test_endpoint "Notification Service" "${NOTIFICATION_URL}/health/live"
test_endpoint "Audit Logger" "${AUDIT_URL}/health/live"

echo ""
echo "2. Readiness Probes"
echo "-----------------------------------"
test_endpoint "Recurring Processor Ready" "${RECURRING_URL}/health/ready"
test_endpoint "Reminder Service Ready" "${REMINDER_URL}/health/ready"
test_endpoint "Notification Service Ready" "${NOTIFICATION_URL}/health/ready"
test_endpoint "Audit Logger Ready" "${AUDIT_URL}/health/ready"

echo ""
echo "3. Service Info"
echo "-----------------------------------"
test_endpoint "Recurring Processor Info" "${RECURRING_URL}/"
test_endpoint "Reminder Service Info" "${REMINDER_URL}/"
test_endpoint "Notification Service Info" "${NOTIFICATION_URL}/"
test_endpoint "Audit Logger Info" "${AUDIT_URL}/"

echo ""
echo "4. Dapr Subscriptions"
echo "-----------------------------------"
test_endpoint "Recurring Processor Subs" "${RECURRING_URL}/dapr/subscribe"
test_endpoint "Reminder Service Subs" "${REMINDER_URL}/dapr/subscribe"
test_endpoint "Notification Service Subs" "${NOTIFICATION_URL}/dapr/subscribe"
test_endpoint "Audit Logger Subs" "${AUDIT_URL}/dapr/subscribe"

echo ""
echo "========================================"
echo -e "Results: ${GREEN}${TESTS_PASSED} passed${NC}, ${RED}${TESTS_FAILED} failed${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
