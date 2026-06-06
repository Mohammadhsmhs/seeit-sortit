#!/usr/bin/env bash
# setup_nim.sh — Alternative setup using NVIDIA NIM containers on DGX Spark
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

NIM_IMAGE="nvcr.io/nim/meta/llama-3.3-70b-instruct:latest"
NIM_CONTAINER_NAME="london-civic-nim"
NIM_PORT=8000

echo "============================================================"
echo "  London Civic Agent — NVIDIA NIM Setup"
echo "============================================================"
echo ""

# ------------------------------------------------------------------
# 1. Prerequisites
# ------------------------------------------------------------------
echo "--- Step 1: Checking prerequisites ---"

command -v nvidia-smi &>/dev/null || fail "nvidia-smi not found"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
ok "GPU detected"

command -v docker &>/dev/null || fail "Docker not found"
ok "Docker available"

# Check NGC authentication
if ! docker pull --quiet "$NIM_IMAGE" 2>/dev/null; then
    echo ""
    echo "NGC login required. Run:"
    echo "  docker login nvcr.io"
    echo "  Username: \$oauthtoken"
    echo "  Password: <your NGC API key from https://ngc.nvidia.com/setup>"
    echo ""
    fail "Cannot pull NIM image — authenticate with NGC first"
fi
echo ""

# ------------------------------------------------------------------
# 2. Pull NIM container
# ------------------------------------------------------------------
echo "--- Step 2: Pulling NIM container ---"

docker pull "$NIM_IMAGE"
ok "NIM image pulled: $NIM_IMAGE"
echo ""

# ------------------------------------------------------------------
# 3. Start NIM inference server
# ------------------------------------------------------------------
echo "--- Step 3: Starting NIM inference server ---"

# Stop existing container if running
if docker ps -q -f name="$NIM_CONTAINER_NAME" | grep -q .; then
    echo "Stopping existing NIM container..."
    docker stop "$NIM_CONTAINER_NAME" &>/dev/null || true
    docker rm "$NIM_CONTAINER_NAME" &>/dev/null || true
fi

docker run -d \
    --name "$NIM_CONTAINER_NAME" \
    --gpus all \
    --shm-size=16g \
    -p "$NIM_PORT:8000" \
    -e NIM_MAX_MODEL_LEN=4096 \
    "$NIM_IMAGE"

ok "NIM container started on port $NIM_PORT"

# Wait for NIM to be ready (it can take a few minutes to load the model)
echo "Waiting for NIM server to be ready (this may take 2-5 minutes)..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "http://localhost:$NIM_PORT/v1/models" &>/dev/null; then
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "  ... waiting ($ELAPSED/${MAX_WAIT}s)"
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "Container logs:"
    docker logs --tail 20 "$NIM_CONTAINER_NAME"
    fail "NIM server did not become ready within ${MAX_WAIT}s"
fi
ok "NIM server ready"
echo ""

# ------------------------------------------------------------------
# 4. Set environment variables
# ------------------------------------------------------------------
echo "--- Step 4: Setting environment variables ---"

export MODEL_PROVIDER=nim
export NIM_BASE_URL="http://localhost:$NIM_PORT/v1"
export NIM_API_KEY=""
export NIM_MODEL="meta/llama-3.3-70b-instruct"

ok "MODEL_PROVIDER=$MODEL_PROVIDER"
ok "NIM_BASE_URL=$NIM_BASE_URL"
ok "NIM_MODEL=$NIM_MODEL"

cat > "$PROJECT_ROOT/.env" <<EOF
MODEL_PROVIDER=nim
NIM_BASE_URL=http://localhost:$NIM_PORT/v1
NIM_API_KEY=
NIM_MODEL=meta/llama-3.3-70b-instruct
EOF
ok "Wrote .env file"
echo ""

# ------------------------------------------------------------------
# 5. Verify inference
# ------------------------------------------------------------------
echo "--- Step 5: Verifying inference ---"

RESPONSE=$(curl -sf "http://localhost:$NIM_PORT/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": "Reply with exactly: NIM_OK"}],
        "max_tokens": 20
    }' 2>&1) || fail "NIM inference request failed"

if echo "$RESPONSE" | grep -qi "NIM_OK\|choices"; then
    ok "NIM inference working"
else
    warn "NIM responded but output unexpected — check manually"
    echo "$RESPONSE" | head -5
fi
echo ""

# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------
echo "============================================================"
echo "  NIM SETUP COMPLETE"
echo "============================================================"
echo ""
echo "  Container:    $NIM_CONTAINER_NAME"
echo "  Image:        $NIM_IMAGE"
echo "  Endpoint:     http://localhost:$NIM_PORT/v1"
echo "  Model:        $NIM_MODEL"
echo ""
echo "  Manage:"
echo "    docker logs -f $NIM_CONTAINER_NAME   # view logs"
echo "    docker stop $NIM_CONTAINER_NAME      # stop server"
echo "    docker start $NIM_CONTAINER_NAME     # restart"
echo ""
echo "  Next steps:"
echo "    source .env"
echo "    python -m src.main --demo"
echo ""
echo "============================================================"
