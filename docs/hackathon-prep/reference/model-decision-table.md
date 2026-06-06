# Model Decision Table — Per Agent, Per Surface

> Single-page consolidated reference. Per use case: which model, why, where it runs, fallback chain, how to swap. Stay consistent with `decisions-locked.md` — if the two disagree, decisions-locked wins.

---

## The headline decision

| Reasoning task | **Llama 3.3 70B (Q4)** | Workhorse for routing, drafting, escalation logic |
| Severity ranking | **Nemotron Super 120B-A12B (MoE)** | Bounty entry. Better citations than Llama. |
| Vision (intake) | **Qwen 2.5-VL 7B** | Small enough to coexist |
| STT | **ElevenLabs Scribe** | Cloud, doesn't compete for GPU |
| Voice agent | **ElevenLabs Conv AI** | Bounty requirement |

---

## Full table

| Agent / use | Primary model | Where runs | Speed (Q4) | Memory | Why this model | First fallback | Second fallback |
|-------------|---------------|-----------|-----------|--------|----------------|---------------|-----------------|
| **Intake — vision classification** | Qwen 2.5-VL 7B | DGX Spark (Ollama) | ~50 tok/s | ~6 GB | Strong image+text in one shot, coexists with reasoning model | Llama 4 Scout (if pulled) | Hardcoded category from filename hint |
| **Intake — STT** | ElevenLabs Scribe (cloud) | ElevenLabs API | ~real-time | 0 | 99 languages, bundled with our API key, doesn't tax GPU | Browser SpeechRecognition API | Hardcoded transcript |
| **Intake — taxonomy snap** | Llama 3.3 70B (Q4) | DGX Spark (Ollama) | ~35-45 tok/s | ~40 GB | Already loaded for downstream agents; tiny JSON-fix call | Nemotron Super | Fuzzy string match in Python |
| **Severity ranking** | **Nemotron Super 120B-A12B** | DGX Spark (Ollama) | ~18 tok/s | ~60 GB | Bounty entry. Quotes specific dataset facts vs paraphrasing | Llama 3.3 70B + README note | Nemotron via NIM cloud |
| **Routing** | none (pure lookup) | n/a | n/a | n/a | Lookup over `routing_table.json`. No LLM needed. | n/a | n/a |
| **Submission — description generation** | Llama 3.3 70B (Q4) | DGX Spark | ~35 tok/s | shared with above | Same model already hot; short generation | Llama 3.1 8B | Template string with no LLM |
| **Watcher — context Q&A** | Nemotron Super (via ElevenLabs Conv AI) | ElevenLabs hosts the LLM | cloud latency | 0 (locally) | Bounty mandates ElevenLabs voice + Nemotron stack | Llama 3.3 via ElevenLabs LLM swap | gpt-4o-mini in Conv AI config |
| **Watcher — outbound voice** | ElevenLabs Conv AI agent | ElevenLabs API | cloud | 0 | Bounty | none — recorded fallback covers demo | n/a |

---

## The memory budget on the Spark (128 GB unified)

| Loaded | Free | Notes |
|--------|------|-------|
| Llama 3.3 70B Q4 (~40 GB) + Qwen 2.5-VL 7B (~6 GB) | ~80 GB | Comfortable. Default during the demo. |
| Llama 3.3 70B + Qwen 2.5-VL + **Nemotron Super** (~60 GB) | ~22 GB | **Tight.** OS + tooling needs headroom. Risky. |
| Nemotron Super + Qwen 2.5-VL (no Llama) | ~62 GB | Safer. Severity uses Nemotron. Drafting/routing use Llama via time-slice (load on demand). |
| Nemotron Super alone | ~68 GB | Test scenario only. |

**Default plan**: Llama 3.3 + Qwen always hot. **Time-slice Nemotron**: load when severity is called, unload after if memory tight. We accept ~5 sec cold-start on severity calls.

**Fallback plan if OOM during demo**: severity moves to NVIDIA NIM cloud endpoint. README still claims Nemotron Super (truthful — same model). Latency goes from ~5s to ~3s on cloud. Privacy story acknowledges: *"During the demo, severity scoring used NVIDIA's NIM cloud endpoint due to the Spark's memory pressure when running three models simultaneously."*

---

## How to swap (the LLMProvider abstraction)

Every agent talks to LLMs through a `LLMProvider` interface. Swap by setting one env var:

```python
# src/models/llm.py
from .local_ollama import LocalProvider
from .nim_cloud import NIMProvider
from .nebius_cloud import NebiusProvider

PROVIDERS = {
    "local":  LocalProvider,      # Ollama on Spark
    "nim":    NIMProvider,        # build.nvidia.com
    "nebius": NebiusProvider,     # studio.nebius.ai
}

def get_default_provider():
    name = os.getenv("MODEL_PROVIDER", "local")
    return PROVIDERS[name]()
```

**Swap mid-demo:** `export MODEL_PROVIDER=nim && python -m src.agents.orchestrator ...` Restart takes 5 sec.

**Swap per-agent:** each agent's constructor accepts an explicit provider. Severity gets a Nemotron-pinned provider; everyone else gets the default.

```python
# Severity always uses Nemotron, regardless of env
from src.models.llm import NIMProvider
severity = SeverityAgent(provider=NIMProvider(model="nvidia/nemotron-super-120b-a12b"))
```

---

## NIM cloud equivalents (for the fallbacks)

| Local model | NIM model name | Endpoint |
|-------------|----------------|----------|
| `llama3.3:70b` | `meta/llama-3.3-70b-instruct` | `https://integrate.api.nvidia.com/v1` |
| `nemotron-super:120b` | `nvidia/nemotron-super-120b-a12b` | same |
| `qwen2.5vl:7b` | `qwen/qwen2.5-vl-7b-instruct` | same |

API key: `NVIDIA_NIM_API_KEY` in `.env` (set Friday evening from build.nvidia.com).

---

## Cloud overflow via Nebius

Per `setup/nebius-setup.md`: Nebius is the overflow valve, not the demo path. Same OpenAI-compatible client shape as NIM. Different model catalogue — find the closest equivalent in their playground (e.g. their Llama 3.1 70B if Llama 3.3 isn't there).

---

## The Llama 3.3 vs Nemotron Super decision (consolidated)

| | Llama 3.3 70B | Nemotron Super 120B-A12B |
|---|---|---|
| Size | ~40 GB Q4 | ~60 GB Q4 (12 GB active params) |
| Speed | ~35-45 tok/s | ~18 tok/s |
| Reasoning depth | Strong | Stronger on grounded reasoning |
| Citation faithfulness | Paraphrases | Quotes specifics |
| NVIDIA-branded | No | **Yes** |
| Bounty-relevant | No | **Nemotron bounty** |

**Decision**: severity uses Nemotron Super for the bounty + citation quality. Everything else uses Llama 3.3 70B for speed. The two coexist via time-slicing.

If we can't keep Nemotron loaded → severity moves to NIM cloud, Llama 3.3 stays local for everything else.

---

## What to say to a judge about model choices

> *"Llama 3.3 70B is the workhorse — routing, drafting, the watcher's internal reasoning. Nemotron Super is loaded specifically for severity ranking, where citation quality is the win condition. Qwen for vision. ElevenLabs for voice. Every choice is in service of one job per model."*

Memorise that 30-sec answer. It pairs with the Nemotron Q&A in `judge-qa-prep.md`.

---

## Anti-patterns

- ❌ Loading 3 large models at once "to be safe" — OOM mid-demo
- ❌ Hardcoding model names in agent code — use the provider abstraction
- ❌ Using Nemotron for routing or drafting — wasted compute, no quality gain
- ❌ Promising "all NVIDIA models" in the README — we use Qwen too (Alibaba) for vision. Disclose honestly.
- ❌ Pulling new models Saturday afternoon "in case we need them" — disk + time sink
