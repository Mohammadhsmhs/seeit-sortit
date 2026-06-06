#!/usr/bin/env bash
# setup_spark.sh — Day 1 setup for NVIDIA DGX Spark (128GB unified memory)
# Installs deps, pulls Llama 3.3 70B Q4 via Ollama, verifies the full pipeline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "============================================================"
echo "  London Civic Agent — DGX Spark Setup"
echo "============================================================"
echo ""

# ------------------------------------------------------------------
# 1. Check NVIDIA GPU
# ------------------------------------------------------------------
echo "--- Step 1: Checking GPU ---"
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    ok "NVIDIA GPU detected"
else
    fail "nvidia-smi not found — is the NVIDIA driver installed?"
fi
echo ""

# ------------------------------------------------------------------
# 2. Python dependencies
# ------------------------------------------------------------------
echo "--- Step 2: Installing Python dependencies ---"
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "Created virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Python dependencies installed"
echo ""

# ------------------------------------------------------------------
# 3. Start Ollama and pull Llama 3.3 70B Q4
# ------------------------------------------------------------------
echo "--- Step 3: Ollama + Llama 3.3 70B ---"

if ! command -v ollama &>/dev/null; then
    fail "Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Start Ollama server if not already running
if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "Starting Ollama server..."
    ollama serve &>/dev/null &
    OLLAMA_PID=$!
    sleep 3
    if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
        fail "Ollama server failed to start"
    fi
    ok "Ollama server started (PID $OLLAMA_PID)"
else
    ok "Ollama server already running"
fi

MODEL="llama3.3:70b-instruct-q4_K_M"

# Pull model if not already present
if ollama list | grep -q "llama3.3:70b-instruct-q4_K_M"; then
    ok "Model $MODEL already available"
else
    echo "Pulling $MODEL (this may take 20-40 minutes on first run)..."
    ollama pull "$MODEL"
    ok "Model pulled"
fi
echo ""

# ------------------------------------------------------------------
# 4. Verify model responds
# ------------------------------------------------------------------
echo "--- Step 4: Verifying model inference ---"

RESPONSE=$(curl -sf http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'"$MODEL"'",
        "messages": [{"role": "user", "content": "Reply with exactly: INFERENCE_OK"}],
        "max_tokens": 20
    }' 2>&1) || fail "Model inference request failed"

if echo "$RESPONSE" | grep -qi "INFERENCE_OK\|choices"; then
    ok "Model inference working"
else
    warn "Model responded but output unexpected — check manually"
    echo "$RESPONSE" | head -5
fi
echo ""

# ------------------------------------------------------------------
# 5. Set environment variables
# ------------------------------------------------------------------
echo "--- Step 5: Setting environment variables ---"

export MODEL_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export OPENAI_MODEL="$MODEL"

ok "MODEL_PROVIDER=$MODEL_PROVIDER"
ok "OPENAI_BASE_URL=$OPENAI_BASE_URL"
ok "OPENAI_MODEL=$OPENAI_MODEL"

# Write an env file for convenience
cat > "$PROJECT_ROOT/.env" <<EOF
MODEL_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=$MODEL
EOF
ok "Wrote .env file"
echo ""

# ------------------------------------------------------------------
# 6. Run demo to verify full pipeline
# ------------------------------------------------------------------
echo "--- Step 6: Running demo pipeline ---"

cd "$PROJECT_ROOT"
if python -m src.main --demo; then
    ok "Demo pipeline completed successfully"
else
    fail "Demo pipeline failed — check output above"
fi
echo ""

# ------------------------------------------------------------------
# Status report
# ------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  SETUP COMPLETE"
echo "============================================================"
echo ""
echo "  GPU:          $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "  Ollama:       $(ollama --version 2>/dev/null || echo 'N/A')"
echo "  Model:        $MODEL"
echo "  Provider:     $MODEL_PROVIDER"
echo "  Endpoint:     $OPENAI_BASE_URL"
echo "  Python:       $(python --version 2>/dev/null)"
echo "  Project:      $PROJECT_ROOT"
echo ""
echo "  Next steps:"
echo "    source .venv/bin/activate"
echo "    source .env  # or: export \$(cat .env | xargs)"
echo "    python -m src.dashboard.app   # start dashboard on :5050"
echo ""
echo "============================================================"
