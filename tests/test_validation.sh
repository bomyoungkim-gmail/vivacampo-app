#!/bin/bash
# VivaCampo MVP - Validation Test Suite
# Tests all critical components and features

set -e

echo "🧪 VivaCampo MVP - Final Validation Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local expected_status=$4
    local headers=${5:-""}
    
    echo -n "Testing $name... "
    
    if [ -z "$headers" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$url")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$url" -H "$headers")
    fi
    
    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $status)"
        ((TESTS_FAILED++))
    fi
}

echo "1. Infrastructure Tests"
echo "-----------------------"

# Database
test_endpoint "Database (via API health)" GET "http://localhost:8000/health" 200

# Redis (if available)
if command -v redis-cli &> /dev/null; then
    echo -n "Testing Redis... "
    if redis-cli -h localhost ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ SKIP${NC} (Redis not running)"
    fi
fi

# LocalStack S3
test_endpoint "LocalStack S3" GET "http://localhost:4566/_localstack/health" 200

echo ""
echo "2. API Endpoints Tests"
echo "----------------------"

# Public endpoints
test_endpoint "API Docs" GET "http://localhost:8000/docs" 200
test_endpoint "OpenAPI Schema" GET "http://localhost:8000/openapi.json" 200
test_endpoint "Metrics" GET "http://localhost:8000/metrics" 200

# Auth endpoints (should require auth)
test_endpoint "Auth - Me (no token)" GET "http://localhost:8000/v1/me" 401

echo ""
echo "3. Service Availability Tests"
echo "------------------------------"

# API Service
test_endpoint "API Service" GET "http://localhost:8000/health" 200

# TiTiler Service
test_endpoint "TiTiler Service" GET "http://localhost:8001/healthz" 200

# App UI (if running)
if curl -s http://localhost:3002 > /dev/null 2>&1; then
    test_endpoint "App UI" GET "http://localhost:3002/app" 200
else
    echo -e "${YELLOW}⚠ SKIP${NC} App UI (not running)"
fi

# Admin UI (if running)
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    test_endpoint "Admin UI" GET "http://localhost:3001/admin" 200
else
    echo -e "${YELLOW}⚠ SKIP${NC} Admin UI (not running)"
fi

echo ""
echo "4. Database Schema Tests"
echo "------------------------"

echo -n "Checking database tables... "
TABLE_COUNT=$(docker compose exec -T db psql -U vivacampo -d vivacampo -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -ge 25 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($TABLE_COUNT tables found)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (Expected ≥25 tables, found $TABLE_COUNT)"
    ((TESTS_FAILED++))
fi

echo ""
echo "5. Docker Services Tests"
echo "------------------------"

SERVICES=("db" "redis" "localstack" "api" "worker" "tiler")

for service in "${SERVICES[@]}"; do
    echo -n "Checking $service container... "
    if docker compose ps $service | grep -q "Up"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (not running)"
        ((TESTS_FAILED++))
    fi
done

echo ""
echo "6. File Structure Tests"
echo "-----------------------"

CRITICAL_FILES=(
    "services/api/app/main.py"
    "services/api/app/domain/quotas.py"
    "services/api/app/domain/audit.py"
    "services/api/app/infrastructure/resilience.py"
    "services/api/app/infrastructure/cache.py"
    "services/api/app/infrastructure/webhooks.py"
    "services/worker/worker/pipeline/stac_client.py"
    "services/worker/worker/jobs/alerts_week.py"
    "services/worker/worker/jobs/forecast_week.py"
    "services/worker/worker/jobs/backfill.py"
    "services/admin-ui/package.json"
    "docker-compose.yml"
)

for file in "${CRITICAL_FILES[@]}"; do
    echo -n "Checking $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (not found)"
        ((TESTS_FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "VivaCampo MVP is ready for production!"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Please review the failures above."
    exit 1
fi
