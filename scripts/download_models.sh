#!/usr/bin/env bash
# download_models.sh — Pre-download all models needed for the London Civic Agent
# Llama 3.3 70B Q4 (reasoning) + Qwen2.5-VL-7B (vision)
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "============================================================"
echo "  London Civic Agent — Model Download"
echo "============================================================"
echo ""

command -v ollama &>/dev/null || fail "Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh"

# Ensure Ollama server is running
if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "Starting Ollama server..."
    ollama serve &>/dev/null &
    sleep 3
    curl -sf http://localhost:11434/api/tags &>/dev/null || fail "Could not start Ollama server"
    ok "Ollama server started"
else
    ok "Ollama server already running"
fi
echo ""

# ------------------------------------------------------------------
# 1. Llama 3.3 70B Q4 — primary reasoning model
# ------------------------------------------------------------------
LLAMA_MODEL="llama3.3:70b-instruct-q4_K_M"

echo "--- Model 1: $LLAMA_MODEL (reasoning) ---"
echo "  Estimated size: ~40 GB"
echo "  Estimated VRAM: ~42 GB"
echo ""

if ollama list | grep -q "llama3.3:70b-instruct-q4_K_M"; then
    ok "$LLAMA_MODEL already downloaded"
else
    echo "Downloading $LLAMA_MODEL ..."
    ollama pull "$LLAMA_MODEL"
    ok "$LLAMA_MODEL downloaded"
fi
echo ""

# ------------------------------------------------------------------
# 2. Qwen2.5-VL-7B — vision model for photo analysis
# ------------------------------------------------------------------
QWEN_MODEL="qwen2.5vl:7b"

echo "--- Model 2: $QWEN_MODEL (vision) ---"
echo "  Estimated size: ~5 GB"
echo "  Estimated VRAM: ~8 GB"
echo ""

if ollama list | grep -q "qwen2.5vl"; then
    ok "$QWEN_MODEL already downloaded"
else
    echo "Downloading $QWEN_MODEL ..."
    ollama pull "$QWEN_MODEL"
    ok "$QWEN_MODEL downloaded"
fi
echo ""

# ------------------------------------------------------------------
# 3. Verify both models are available
# ------------------------------------------------------------------
echo "--- Verifying models ---"

AVAILABLE=$(ollama list 2>/dev/null)
PASS=0
TOTAL=2

if echo "$AVAILABLE" | grep -q "llama3.3"; then
    ok "Llama 3.3 70B: available"
    PASS=$((PASS + 1))
else
    warn "Llama 3.3 70B: NOT FOUND"
fi

if echo "$AVAILABLE" | grep -q "qwen2.5vl"; then
    ok "Qwen2.5-VL-7B: available"
    PASS=$((PASS + 1))
else
    warn "Qwen2.5-VL-7B: NOT FOUND"
fi
echo ""

# ------------------------------------------------------------------
# 4. Memory usage estimates
# ------------------------------------------------------------------
echo "============================================================"
echo "  MEMORY USAGE ESTIMATES"
echo "============================================================"
echo ""
echo "  DGX Spark unified memory:  128 GB"
echo ""
echo "  Llama 3.3 70B (Q4_K_M):   ~42 GB VRAM"
echo "  Qwen2.5-VL-7B:            ~8 GB VRAM"
echo "  Ollama overhead:           ~2 GB"
echo "  System / OS:               ~8 GB"
echo "  ────────────────────────────────────"
echo "  Total estimated:           ~60 GB"
echo "  Available headroom:        ~68 GB"
echo ""
echo "  NOTE: Both models can be loaded simultaneously on the"
echo "  DGX Spark. The 128 GB unified memory is sufficient."
echo ""
echo "  Models downloaded: $PASS/$TOTAL"
echo "============================================================"

if [ $PASS -lt $TOTAL ]; then
    exit 1
fi
