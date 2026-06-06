# Nebius Cloud Setup — Overflow, Batch, Backup

> Owner: Ongun. Done by **end of Friday evening** if possible, otherwise as needed.
>
> **What Nebius is for us:** the overflow valve. The Spark is the hero. Nebius takes work that can't run on the Spark, or that's better off the critical path.
>
> Sponsor talk: **Saturday 09:00 — Nebius**. Listen for hackathon credit offers and any specific endpoint they want us to use.

---

## Where Nebius IS used in our stack

1. **Overflow inference** — if Nemotron Super doesn't fit on the Spark alongside the vision model, run Nemotron on Nebius's hosted Studio API. Keep the privacy story honest by disclosing this in the README.
2. **Batch work** — RAG index building, mass embeddings, FixMyStreet enrichment. None of this needs the Spark, none of it is on the demo's hot path.
3. **Backup inference** — if the Spark dies, Nebius is our second-best path to a working demo.
4. **Sponsor compliance** — they sponsored us. Touching their API at least once is the polite minimum. Mention them in the README and pitch.

---

## Where Nebius is NOT used

- ❌ The **escalation agent** (the Watcher) — must live on or near the Spark for the persistence + privacy story.
- ❌ The **vision intake** — local on the Spark, low latency, privacy.
- ❌ Anything user-facing during the live demo where latency is visible (severity scoring on a fresh Rebecca report, for instance).
- ❌ Storage of citizen photos. ElevenLabs and Nebius both touch our network during the run — neither sees raw photo data. That's the line.

---

## Step 1 — Account + credits (10 min)

1. Go to https://nebius.com → sign up with a team email
2. **Attend the Nebius partner talk at 9:00 AM Saturday.** Ask: *"What hackathon credit pool do Sorted participants have access to?"* — apply whatever they hand out before any usage.
3. Console → API Keys → create one named `sorted-hackathon`
4. Save to `.env`:

   ```bash
   NEBIUS_API_KEY=ne-xxxxxxxxxxxxxxxxxxxx
   NEBIUS_FOLDER_ID=b1g...xxxxxxxxx   # if their dashboard gives you one
   ```

---

## Step 2 — Pick the right product (5 min)

Nebius has multiple offerings. For 14.5 hours, use only:

| Product | Use it for | Don't use it for |
|---------|-----------|-------------------|
| **Nebius Studio (Inference API)** | Llama / Nemotron / Qwen inference via OpenAI-compatible API | Vision (if it's on Studio, fine; otherwise local Qwen2.5-VL) |
| **GPU compute instances** | Skip. Spinning up an A100 takes 20-40 minutes and we don't have time. | Anything |
| **Object storage** | Skip. SQLite + git is enough for us. | Anything |
| **Kubernetes / clusters** | Skip. Saturday is not the day. | Anything |

**Default: Nebius = Studio Inference API. Everything else: ignore.**

---

## Step 3 — Sanity test the Inference API (5 min)

Same pattern as the NVIDIA NIM fallback — OpenAI-compatible client:

```python
# nebius_smoke.py
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1",
    api_key=os.environ["NEBIUS_API_KEY"],
)

resp = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",  # check Nebius model catalog
    messages=[{"role": "user", "content": "Reply with only the word OK"}],
)
print(resp.choices[0].message.content)
```

```bash
pip install openai
python3 nebius_smoke.py
# Expected: OK
```

If this returns OK, Nebius is unblocked. Find the Nemotron model name in their catalog (or NVIDIA NIM equivalent) and re-test.

---

## Step 4 — Wire Nebius as a provider class (10 min — Saturday only if needed)

In our code (Saturday — owned by Ongun):

```python
# src/models/nebius.py
import os
from openai import OpenAI
from .base import LLMProvider, ChatResponse

class NebiusProvider(LLMProvider):
    def __init__(self, model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"):
        self.client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1",
            api_key=os.environ["NEBIUS_API_KEY"],
        )
        self.model = model

    def complete(self, messages, **kwargs) -> ChatResponse:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return ChatResponse(text=resp.choices[0].message.content)
```

Our agents already use `LLMProvider` abstraction (per `decisions-locked.md` swap rule). Switching to Nebius is one line in `src/config.py`:

```python
MODEL_PROVIDER = "nebius"  # or "local" or "nim"
```

---

## Step 5 — Batch RAG corpus building (Saturday morning — if useful)

If the Spark is taxed and the RAG corpus needs embeddings:

- Push the corpus to Nebius
- Use their batch embeddings endpoint
- Pull the resulting vectors into our local FAISS / Chroma index

But honestly — **for 4 datasets (STATS19, schools, hospitals, density) totalling <100K rows, local embeddings on the Spark are faster than the round-trip.** Don't pre-optimise. Only use Nebius batch if local embedding takes >10 min Saturday morning.

---

## What goes in the README about Nebius

```markdown
## Cloud Overflow — Nebius

Heavy lifting that doesn't need to be on-device runs on Nebius Studio:
- [What you actually used Nebius for. Be honest. Don't lie if you only used it for one test.]

Nebius keeps the Spark free for the hot path (vision, agent reasoning, persistent
session memory). No citizen photos or addresses leave the device — only the
structured submission to the council and the synthesised voice for the phone call.
```

If we end up not using Nebius materially in the working demo, still credit them in the sponsor list — but don't oversell.

---

## What can go wrong

| Symptom | Fix |
|---------|-----|
| 401 from Nebius | API key not exported / wrong key from another env |
| "Model not found" | Their catalog uses slightly different names — paste into their playground to find the exact ID |
| Slow first call | Cold start, model needs to load. ~10-30s the first time. Subsequent fast. |
| Credit exhausted | Sponsor talk question wasn't asked properly. Find a Nebius person. |

---

## What you should NOT do

- ❌ Build the demo on Nebius. Privacy story breaks.
- ❌ Spin up VM instances "just in case." Eats time, eats credits, eats focus.
- ❌ Mention Nebius prominently in the pitch if we only used it for one batch job. Honest acknowledgement only.
- ❌ Put the FixMyStreet scraper on Nebius. Just run it on a laptop overnight Friday.

---

## Exit criterion

By **end of Friday evening:**

1. Account created, API key in `.env`
2. `nebius_smoke.py` returns OK
3. Decision logged in `docs/DECISIONS.md`: *"Nebius use planned: [overflow Nemotron / batch embeddings / nothing — sponsor mention only]"*

If smoke test doesn't pass by Saturday 9:30 — **drop Nebius from the active stack.** Mention them in the sponsor list only.
