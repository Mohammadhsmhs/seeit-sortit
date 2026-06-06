# Decisions LOCKED — Sorted

> Decisions made BEFORE 9:30 AM Saturday. Re-opening any of these requires Ongun's explicit "yes, we are re-opening this." Default answer is **no, move on**.
>
> Each decision: what · why · what would force a re-open.

---

## 1. Models

| Use | Model | Why this | What forces a re-open |
|-----|-------|----------|----------------------|
| Reasoning (severity, routing, drafting, escalation) | **Llama 3.3 70B (Q4)** on DGX Spark via Ollama | Fits in 128 GB unified memory, runs at ~35-45 tok/s, well-supported | Model fails to load → switch to Llama 3.1 70B or Llama 3 8B as fallback |
| Reasoning (Nemotron bounty layer) | **Nemotron Super 120B-A12B** (MoE, only 12B active) | Wins the Nemotron bounty, 12B active params = fast, NVIDIA-branded | Doesn't fit alongside vision model → use Nemotron only for severity ranking, keep Llama 3.3 for the rest |
| Vision (intake classification) | **Qwen2.5-VL-7B** via Ollama | Small enough to coexist with reasoning model, strong on images | Quality bad → fall back to Llama 4 Scout (if we can pull it) or hardcoded category |
| STT (voice intake) | **ElevenLabs Scribe** | 99 languages, cloud API (so doesn't compete for GPU) | API down → browser SpeechRecognition API as fallback |
| Voice agent (phone) | **ElevenLabs Conversational AI** | Bounty requirement, low-latency, programmable agent | None — required for ElevenLabs prize |
| Telephony | **Twilio** | Cleanest ElevenLabs integration, UK numbers available | Same-day account approval issue → skip live call, recorded fallback |

**One model swap rule:** swap is OK if the new one returns the same shape. Don't re-architect agents for a different model.

---

## 2. Software stack

| Layer | Decision | Why | What forces a re-open |
|-------|----------|-----|----------------------|
| Backend language | **Python 3.11+** | Matches NeMo Agent Toolkit, our friend knows Python | Never |
| Web framework | **Flask** | Zero ceremony, single-file servers, easy to demo | Never |
| Frontend | **Vanilla HTML + JS + CSS** | No build step, no node_modules, ships fast | Never. *No React.* |
| Map | **Leaflet 1.9** + OpenStreetMap tiles | Free, fast, no API key | Never |
| Charts | **Chart.js 4** | Drop-in, no build | Never |
| Data store | **SQLite (single file)** | Portable, fast, queryable, fits in repo | Never. *No Postgres.* |
| Inference runtime | **Ollama** on the Spark (with NIM for Nemotron if it's there) | Pre-installed on DGX Spark, simple `ollama pull` and you're running | DGX setup issue → fall back to NVIDIA NIM cloud endpoints (build.nvidia.com) |
| Orchestration | **Plain Python, async + asyncio** | No LangGraph, no CrewAI — those add learning curve we don't have | Never |
| Phone webhook tunneling | **ngrok** (free tier) | Fastest path from Twilio to our local Flask | Never |

---

## 3. Architecture (the 5-agent pipeline)

**Locked shape:**

```
INTAKE → SEVERITY → ROUTING → SUBMISSION → ESCALATION
```

- One orchestrator (`src/agents/orchestrator.py`) wires them together
- Each agent is a pure Python class with one `process()` method
- State flows through a shared `CivicIssue` Pydantic model
- All persistence in SQLite, no in-memory state between requests

**Locked: 5 agents.** Not 7. Not 3.

| Agent | Owner | Hard scope |
|-------|-------|-----------|
| Intake | Ongun | Photo → category + GPS + structured issue. No multi-photo. |
| Severity | Ongun | Compute 0-10 score + cited rationale. Only 4 data sources for RAG (collisions, schools, hospitals, density). |
| Routing | Ongun | Return one council + one channel. No fancy department fan-out. |
| Submission | Ongun | One Open311 POST to Camden. Hackney as second-borough demo only. |
| Escalation | Teammate 2 or Ongun | One outbound call via ElevenLabs+Twilio. No SMS, no email-letters, no MP letter. Just the call. |

---

## 4. Demo decisions

| What | Decision | Why |
|------|----------|-----|
| Protagonist name | **Rebecca** | Locked across deck + demo + video |
| Protagonist context | **Single mum, Tower Hamlets, daughter at Osmani Primary School** | Already in onboarding deck |
| Issue | **Fly-tipping — dumped mattresses, broken furniture, bin bags** | Visceral, photo-friendly, real-pattern category |
| Demo address | **Vallance Road, Tower Hamlets** | Real road, near real schools, plausible scenario |
| Submission target (Open311 live) | **Camden** | We verified `fixmystreet.camden.gov.uk/open311/v2/requests.xml` works. Tower Hamlets has no Open311. |
| Story handling of Camden vs Tower Hamlets | **Demo says "Tower Hamlets" but the actual API call goes to Camden as a sandbox.** The demo script openly acknowledges this in the README, not in the demo itself. | Don't fake. The audience won't notice; the README explains. |
| Demo borough leaderboard top spot | **Greenwich (100.0 composite)** | Already in our scorecard, looks real |
| Demo borough leaderboard bottom | **Camden #13 of 33** | Honest, controversial, drives the accountability point |
| Phone call target number | **Pre-recorded** by default. **Live attempt** only if Twilio + ElevenLabs sandbox works by 19:00 Sat. | Recorded fallback is the plan, live is the bonus |

---

## 5. Bounties we are chasing

In order of priority:

1. **Public Services track winner** — the whole project. Composite story: protagonist + accountability + privacy-first + closed-loop.
2. **ElevenLabs Prize** — escalation agent runs continuously through Saturday afternoon → Sunday demo (≥1h 11min), persistent context, Nemotron + ElevenLabs voice.
3. **Nemotron Bounty (RTX 5080)** — severity ranking agent uses Nemotron Super. Make it visible in the README + on-screen labels.

**Not chasing:** the HP bounty (n/a in materials we saw), Nebius-specific prize (we use Nebius only as inference overflow).

---

## 6. Scope CUTS (we will not build any of these)

This is what we have decided NOT to do. Saying "we should add X" on Saturday earns a redirect to this list.

| Cut | Why |
|-----|-----|
| Native iOS app | PWA equivalent, 30-min upgrade, looks the same in demo |
| Council-side dashboard | Slide in the pitch, not a built feature |
| Love Clean Streets scraping | Behind login, not worth the time |
| Multilingual UI | Scribe handles input language; UI stays English |
| Real LGO / MP letter sending | We draft the letters and show them — don't actually send during demo |
| FixMyStreet photo uploads to the public site | Privacy story breaks. We submit text-only to Camden's Open311. |
| Photo download from FixMyStreet for the demo | We supply our own photo (Rebecca's mattress shot) |
| User accounts / login on the app | Anonymous flow. Twilio number identifies users. |
| In-app push notifications | Out of scope. Status check via dashboard. |
| Council leaderboard with all 33 boroughs | 16 with data is fine. We disclose the limit. |
| Map clustering at zoom-out | Performance fix only if dashboard is slow |
| User-side prioritisation customisation ("I care more about potholes") | Out of scope |
| Anything that needs >2 hours of integration work nobody scoped | Default cut |

---

## 7. Privacy positioning (this is the killer pitch line)

**Locked claim:** *"All inference runs locally on the NVIDIA DGX Spark. Photos and case data never leave the device. Only the structured report leaves — and only to the one council that needs it."*

**What "the device" means here:** the DGX Spark. We're in a venue with a Spark on the desk. That's "the device."

**What this means for code:**
- Vision model runs on Spark (not on a cloud API)
- Reasoning models run on Spark
- Only the OUTBOUND artifacts leave: the Open311 POST + the Twilio call
- ElevenLabs API counts as "leaving" — disclose in README: *"voice synthesis only; raw audio of the resident never leaves the device"*

**Don't oversell.** The agent uses ElevenLabs (cloud) for STT and TTS during the demo. That's fine. Be honest about it. The competitor (FixMyStreet) puts PHOTOS on the public web. We don't. That's the real win.

---

## 8. README and pitch positioning

| Element | Locked text |
|---------|-------------|
| Project name | `Sorted` |
| Tagline (README + repo) | "We finish what Babbage started." |
| One-liner | "Every Londoner just got a £200/hour ombudsman that takes one photo and one voice note and chases the council until it's fixed." |
| Hero metric | "6,000+ historical FixMyStreet reports analysed across 24 London boroughs" |
| Sponsor mentions | NVIDIA · HP · Nebius · ElevenLabs — in that order, every time |
| Differentiator (always say this) | "We close the loop. FixMyStreet and CivicDesk file the report. We don't stop until it's fixed." |

---

## 9. What is genuinely still open

These three are open — Ongun decides at the appropriate checkpoint, not at the briefing.

- **Open** — Live phone call vs recorded fallback for the demo. Decided at 19:00 Sat checkpoint.
- **Open** — Whether to fan to Hackney as a second Open311 demo. Decided at 17:00 Sat checkpoint based on time left.
- **Open** — Pitch deck cover image (Sorted portrait vs Analytical Engine schematic). Decided 08:30 Sun.

Everything else in this file is **locked**. Don't reopen.
