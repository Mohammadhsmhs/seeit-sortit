# DGX Spark — First 30 Minutes

> Ownership: **Ongun**, with anyone on the team paired up. Done by **10:00 Saturday** (30 min after hacking begins). If we don't have inference running by 10:00 we have a problem — escalate to NVIDIA staff (yellow / purple stickers per the briefing).
>
> What we know (from kickoff briefing Friday): DGX Spark is on our desk. NVIDIA provides DGX Spark Training at 8:45 AM Saturday — **attend that, this doc is for after**.

---

## What the Spark gives us

- NVIDIA GB10 Grace Blackwell Superchip
- **128 GB unified LPDDR5X memory** (CPU + GPU share this — no separate VRAM)
- 6,144 CUDA cores, 192 Tensor cores
- 4 TB NVMe SSD
- **Pre-installed** (per NVIDIA documentation): Ollama, NVIDIA NIM containers, NeMo framework, TensorRT-LLM, vLLM, CUDA, Python

This is **not** "set up a fresh Ubuntu box." Most of what we need is already there. Our job is to verify and use it, not install it.

---

## Step 1 — Get access (5 min)

Two access modes depending on what NVIDIA tells us at the 8:45 AM training:

**Mode A: Local console** (most likely) — keyboard/monitor connected to the Spark on the desk. Just sit down and use it.

**Mode B: SSH from your laptop** — NVIDIA gives an IP and credentials. From your laptop:
```bash
ssh user@<spark-ip-address>
# Password or SSH key — whichever NVIDIA hands out
```

**Confirm which mode at the 8:45 training.** Don't assume.

---

## Step 2 — Verify the basics are running (5 min)

```bash
# 1. Is Ollama running?
ollama list
# Expected: a list of any models already pre-pulled (might be empty)

# 2. GPU healthy?
nvidia-smi
# Expected: GB10 Grace Blackwell visible, memory usage near 0

# 3. Disk free?
df -h /workspace 2>/dev/null || df -h ~
# Expected: 100+ GB free on the main partition

# 4. Python ready?
python3 --version
pip3 list | grep -E "torch|transformers|ollama"
```

If any of these fail → grab a NVIDIA staff member immediately. **Do not try to fix infra yourself** — they expect support requests and we don't have time to debug their stack.

---

## Step 3 — Pull our models (10 min)

This downloads the model weights to local disk. Sizes are approximate at Q4 quantization:

```bash
# Reasoning workhorse — ~40 GB
ollama pull llama3.3:70b

# Vision model — ~5 GB
ollama pull qwen2.5vl:7b

# Nemotron Super for the bounty — ~60 GB (try this last, may not be in Ollama registry yet)
ollama pull nemotron-super:120b
# If that 404s, try:
#   ollama pull nemotron:120b
# If that fails too, we'll use NVIDIA NIM cloud endpoint as fallback (see Step 5)
```

While they download, move on to Step 4. **Don't watch the download bar — that's a time sink.**

---

## Step 4 — Write the smoke test (5 min)

This is the 5-line script every team member should know how to run. Save as `smoke.py` in the repo:

```python
import ollama

resp = ollama.chat(
    model="llama3.3:70b",
    messages=[{"role": "user", "content": "Reply with the single word OK."}]
)
print(resp["message"]["content"])
```

Run it:
```bash
python3 smoke.py
# Expected output: OK   (or "OK." or "Sure: OK" — anything containing OK is a pass)
```

If it returns anything: **the Spark works, Ollama works, we are unblocked**.

Repeat with `model="qwen2.5vl:7b"` to verify vision model loads. For the vision smoke test, pass an image:

```python
import ollama
resp = ollama.chat(
    model="qwen2.5vl:7b",
    messages=[{
        "role": "user",
        "content": "What is in this image? Reply in 5 words or fewer.",
        "images": ["/path/to/any/test-photo.jpg"]
    }]
)
print(resp["message"]["content"])
```

---

## Step 5 — Fallback: NVIDIA NIM cloud endpoints (5 min — only if a model fails locally)

If a model won't pull or won't fit, we have a fallback: **NVIDIA-hosted NIM endpoints at `build.nvidia.com`** that we can call via OpenAI-compatible API.

1. Go to https://build.nvidia.com — sign in with the NVIDIA Developer account (Ongun has the team account)
2. Click "Get API Key" → copy
3. Set in our `.env`:
   ```bash
   NVIDIA_NIM_API_KEY=nvapi-...
   ```
4. In Python:
   ```python
   from openai import OpenAI
   client = OpenAI(
       base_url="https://integrate.api.nvidia.com/v1",
       api_key="<NVIDIA_NIM_API_KEY>"
   )
   resp = client.chat.completions.create(
       model="meta/llama-3.3-70b-instruct",  # or "nvidia/nemotron-super-120b-a12b"
       messages=[{"role": "user", "content": "Reply with OK"}],
   )
   print(resp.choices[0].message.content)
   ```

**Use cloud only as fallback for a specific model.** Anything that runs locally must stay local — that's the privacy story.

---

## Common failure modes (and fixes)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ollama list` not found | Service not running | `sudo systemctl start ollama` |
| `ollama pull` super slow | Network shared with 40 teams | Pull during the 12:30 lunch break instead |
| First `ollama.chat` call hangs 30+ sec | Model loading into memory for the first time | Normal. Subsequent calls < 2 sec. |
| OOM error | Two big models loaded simultaneously | Unload with `ollama stop <model>`. Time-slice. |
| Vision model returns gibberish | Image path wrong / image too large | Check the path. Resize image to <2 MB before passing. |
| Nemotron not in Ollama registry | Different name or NIM-only | Try NIM endpoint (Step 5). Don't burn 30 min searching. |

---

## What you should NOT touch

- **Do not run `sudo apt upgrade`.** The Spark image is pinned for a reason.
- **Do not move the Spark.** Official rule.
- **Do not unplug.** Official rule.
- **Do not install other models speculatively** ("let me try Mistral too") — disk fills, time burns.
- **Do not change CUDA versions.** Anything ML-shaped is built against the installed version.

---

## Once Step 4 passes — what's next

You hand off to the rest of the pipeline.

The model providers in our code will look like:
```python
# src/models/local.py — uses Ollama on localhost
# src/models/nim.py    — uses NVIDIA NIM cloud (fallback only)
```

Each agent imports its provider and calls `provider.complete(...)`. The agent code is the same regardless of provider — that's the swap-friendly design we agreed on in `decisions-locked.md`.

---

## Time check

You should be done with all five steps by **10:00 Saturday**. If you're still pulling models at 11:00, switch to NIM endpoints for whatever isn't loaded — the local-vs-cloud distinction is a "we used Nebius cloud overflow" line in the README, not a problem.

**The Spark is set up. Build the pipeline.**
