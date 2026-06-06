#!/usr/bin/env bash
# quick_test.sh — Smoke tests: demo pipeline, test suite, dashboard health check
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

PASS=0
FAIL=0
TESTS=()

record() {
    local name="$1" result="$2"
    if [ "$result" = "PASS" ]; then
        TESTS+=("${GREEN}PASS${NC}  $name")
        PASS=$((PASS + 1))
    else
        TESTS+=("${RED}FAIL${NC}  $name")
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================================"
echo "  London Civic Agent — Quick Smoke Tests"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Load env if present
if [ -f ".env" ]; then
    set -a; source .env; set +a
fi

# ------------------------------------------------------------------
# 1. Demo pipeline (mock mode as fallback)
# ------------------------------------------------------------------
echo "--- Test 1: Demo pipeline ---"
if python -m src.main --demo 2>&1; then
    record "Demo pipeline" "PASS"
else
    record "Demo pipeline" "FAIL"
fi
echo ""

# ------------------------------------------------------------------
# 2. Test suite
# ------------------------------------------------------------------
echo "--- Test 2: Test suite ---"
if python -m pytest src/tests/ -v 2>&1; then
    record "Test suite (pytest)" "PASS"
else
    record "Test suite (pytest)" "FAIL"
fi
echo ""

# ------------------------------------------------------------------
# 3. Dashboard health check
# ------------------------------------------------------------------
echo "--- Test 3: Dashboard /api/stats ---"

DASHBOARD_PORT=5050
DASHBOARD_PID=""

# Start dashboard in background
python -m src.dashboard.app &>/dev/null &
DASHBOARD_PID=$!

# Wait for it to come up
READY=false
for i in $(seq 1 10); do
    if curl -sf "http://localhost:$DASHBOARD_PORT/api/stats" &>/dev/null; then
        READY=true
        break
    fi
    sleep 1
done

if $READY; then
    STATS=$(curl -sf "http://localhost:$DASHBOARD_PORT/api/stats")
    if echo "$STATS" | python -m json.tool &>/dev/null; then
        record "Dashboard /api/stats" "PASS"
        echo "  Response: $(echo "$STATS" | python -c 'import sys,json; d=json.load(sys.stdin); print(f"total_reports={d.get(\"total_reports\",\"?\")}")' 2>/dev/null || echo "$STATS" | head -1)"
    else
        record "Dashboard /api/stats" "FAIL"
        echo "  Response was not valid JSON"
    fi
else
    record "Dashboard /api/stats" "FAIL"
    echo "  Dashboard did not start within 10s"
fi

# Clean up dashboard process
if [ -n "$DASHBOARD_PID" ]; then
    kill "$DASHBOARD_PID" 2>/dev/null || true
    wait "$DASHBOARD_PID" 2>/dev/null || true
fi
echo ""

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
TOTAL=$((PASS + FAIL))

echo "============================================================"
echo "  RESULTS: $PASS/$TOTAL passed"
echo "============================================================"
echo ""
for t in "${TESTS[@]}"; do
    echo -e "  $t"
done
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "  ${RED}$FAIL test(s) failed${NC}"
    exit 1
else
    echo -e "  ${GREEN}All tests passed${NC}"
fi
echo "============================================================"
