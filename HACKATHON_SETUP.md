# London Civic Agent -- Hackathon Setup Guide

Step-by-step setup for the NVIDIA DGX Spark (128 GB unified memory).

---

## Prerequisites

- NVIDIA DGX Spark with GPU drivers installed
- Python 3.11+
- Ollama pre-installed (or Docker for NIM route)

Verify GPU access:

```bash
nvidia-smi
```

---

## Option A: One-Command Setup (Recommended)

The setup script handles everything: dependencies, model download, verification.

```bash
chmod +x scripts/*.sh
./scripts/setup_spark.sh
```

This will:
1. Check GPU availability
2. Create a Python virtual environment and install dependencies
3. Start Ollama and pull Llama 3.3 70B (Q4_K_M)
4. Verify the model responds to inference requests
5. Write a `.env` file with the correct configuration
6. Run the demo pipeline end-to-end
7. Print a status report

After setup, start the dashboard:

```bash
source .venv/bin/activate
export $(cat .env | xargs)
python -m src.dashboard.app
```

Dashboard: http://localhost:5050

---

## Option B: NVIDIA NIM Setup

If you prefer NIM containers over Ollama:

```bash
# Log in to NGC first
docker login nvcr.io
# Username: $oauthtoken
# Password: <your NGC API key>

./scripts/setup_nim.sh
```

---

## Option C: Docker Compose

Run both the app and Ollama as containers:

```bash
docker compose up -d

# Pull the model into the Ollama container (first run only)
docker compose exec ollama ollama pull llama3.3:70b-instruct-q4_K_M

# Verify
curl http://localhost:5050/api/stats
```

---

## Model Downloads (Pre-Download)

Download both models ahead of time to avoid delays during the demo:

```bash
./scripts/download_models.sh
```

Models:
- **Llama 3.3 70B (Q4_K_M)** -- reasoning, ~40 GB download, ~42 GB VRAM
- **Qwen2.5-VL-7B** -- vision/photo analysis, ~5 GB download, ~8 GB VRAM
- **Total estimated VRAM**: ~60 GB of 128 GB available

---

## Quick Smoke Test

Run after setup to verify everything works:

```bash
./scripts/quick_test.sh
```

Tests:
1. Demo pipeline (3 scenarios through the full agent pipeline)
2. Pytest suite (unit + integration tests)
3. Dashboard health check (starts dashboard, hits `/api/stats`)

---

## Manual Setup (Step by Step)

If the scripts don't work on your environment, here is the manual process:

```bash
# 1. Virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start Ollama
ollama serve &

# 3. Pull the model
ollama pull llama3.3:70b-instruct-q4_K_M

# 4. Configure environment
export MODEL_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export OPENAI_MODEL=llama3.3:70b-instruct-q4_K_M

# 5. Test inference
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.3:70b-instruct-q4_K_M","messages":[{"role":"user","content":"Hello"}],"max_tokens":20}'

# 6. Run demo
python -m src.main --demo

# 7. Start dashboard
python -m src.dashboard.app
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `MODEL_PROVIDER` | `mock` | `mock`, `openai`, or `nim` |
| `OPENAI_BASE_URL` | `http://localhost:8000/v1` | Ollama/vLLM endpoint |
| `OPENAI_API_KEY` | (empty) | Set to `ollama` for Ollama |
| `OPENAI_MODEL` | `meta/llama-3.1-8b-instruct` | Model name |
| `NIM_BASE_URL` | `https://integrate.api.nvidia.com/v1` | NIM endpoint |
| `NIM_API_KEY` | (empty) | NGC API key for NIM |
| `NIM_MODEL` | `meta/llama-3.1-8b-instruct` | NIM model name |

---

## Troubleshooting

**Ollama won't start**: Check if port 11434 is already in use (`lsof -i :11434`).

**Model pull fails**: Ensure you have at least 50 GB free disk space. Check network.

**NIM auth fails**: Re-run `docker login nvcr.io` with a fresh NGC API key.

**Dashboard 500 errors**: Check that `scraper/fixmystreet.db` exists. Run `python scraper/scrape_london.py` if missing.

**Out of memory**: If running both models simultaneously causes OOM, load only the reasoning model and skip vision for the demo.
