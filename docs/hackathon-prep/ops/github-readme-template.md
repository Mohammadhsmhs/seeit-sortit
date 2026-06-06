# README Template

> Copy this into the repo's `README.md` at **10:00 Sunday**. Replace every `{{ placeholder }}` before pushing. Total polish time: ~30 min.
>
> The README is the FIRST thing judges read. The first 200 words must sell the project before the user scrolls. The middle is the bounty entries. The bottom is setup.

---

## The template (paste this verbatim into README.md, then fill in)

````markdown
# Sorted

> *"We finish what Babbage started."*

**Sorted** is a multi-agent AI civic complaint system built at the **NVIDIA Hack for Impact London** (5–7 June 2026). One photo and one voice note triggers a 5-agent pipeline that classifies the issue, scores severity against cited London open data, submits to the correct council via Open311, and **chases the council by phone** until the issue is fixed. All inference runs locally on the NVIDIA DGX Spark — citizen photos and addresses never leave the device.

### 🎥 Watch the 4-minute demo: [{{ video_title }}]({{ youtube_url }})

### 🌍 Live dashboard: [{{ dashboard_url }}]({{ dashboard_url }})

---

## What's different about Sorted

Most civic apps file a report and stop. We close the loop.

- **The agent acts on behalf of the resident** — one photo, one voice note, zero clicks
- **Severity is grounded** — Nemotron Super cites specific London open datasets (collisions, schools, hospitals, density)
- **Submission goes direct** — Open311 POST straight to council CRMs (Camden verified live)
- **The Sorted Watcher** — a persistent voice agent that places phone calls when councils breach SLA
- **Public accountability** — a fair multi-dimensional leaderboard ranks all 33 London boroughs

---

## Powered by NVIDIA Nemotron Super 120B-A12B

The **severity ranking agent** runs on NVIDIA Nemotron Super (120B params, 12B active MoE) deployed locally on the DGX Spark.

We use Nemotron specifically because severity ranking requires grounded reasoning over four heterogeneous London open datasets (STATS19 collisions, GIAS schools, NHS hospitals, Census 2021 density) and must produce a faithfully-cited 2–3 sentence rationale. Comparative testing on a 3-report sample showed Nemotron quoting specific dataset facts (e.g. *"Osmani Primary 44m from incident"*) where Llama 3.3 70B paraphrased.

![Llama vs Nemotron comparison](./demo_data/llama_vs_nemotron.png)

Nemotron also powers the escalation agent's persistent context — see below.

**Inference cost: 0 USD. Privacy: full. Runtime: local.**

---

## Sorted Watcher — ElevenLabs Bounty Submission

The Sorted Watcher is an **autonomous voice agent that runs persistently** for the duration of the hackathon. It monitors the CRM, places phone calls when SLAs are breached, and maintains a session log of every event it observes.

- **Stack**: NVIDIA Nemotron Super + ElevenLabs Conversational AI (voice in/out)
- **Continuous runtime**: from `{{ watcher_start_ts }}` to `{{ watcher_demo_ts }}` = **{{ watcher_duration }} hours**
- **Session log**: [`watcher_session.json`](./watcher_session.json) — every event, timestamped
- **Live test**: ask the agent any question from `{{ judge_questions.md }}` via the ElevenLabs Conv AI sandbox

[See full strategy](./docs/hackathon-prep/bounties/elevenlabs-prize-strategy.md)

---

## Architecture

```
INTAKE → SEVERITY → ROUTING → SUBMISSION  ┐
   ↓        ↓         ↓          ↓        ↓
  Qwen   Nemotron   lookup    Open311  ┌─────────────┐
  +VL     Super     table      POST    │ SQLite CRM  │
  +Scribe                              └─────────────┘
                                              ↓
                                       ┌─────────────┐
                                       │ Watcher     │ ← polls every 30s
                                       │ (Nemotron + │
                                       │ ElevenLabs) │
                                       └─────────────┘
                                              ↓
                                     OUTBOUND PHONE CALL
                                       (Twilio + EL Conv AI)
```

5 agents + 1 persistent Watcher + public dashboard. All local on the DGX Spark. Open311 + Twilio + ElevenLabs are the only external integrations.

---

## Tech stack

| Component | Tech |
|-----------|------|
| Vision (intake) | Qwen 2.5-VL 7B via Ollama |
| STT | ElevenLabs Scribe |
| Reasoning | NVIDIA Nemotron Super 120B-A12B + Llama 3.3 70B (Q4) via Ollama |
| Voice agent | ElevenLabs Conversational AI |
| Telephony | Twilio (UK number) |
| Cloud overflow | Nebius Studio Inference API |
| Backend | Python 3.11 + Flask + SQLite |
| Frontend | Vanilla HTML + JS + Leaflet + Chart.js |

---

## Honest disclosures

- The demo submits to **Camden's Open311 sandbox** even though Rebecca's story (the protagonist) is in Tower Hamlets. Tower Hamlets does not expose Open311 publicly; Camden does. The routing agent honestly returns Tower Hamlets; the orchestrator retargets to Camden via `DEMO_MODE=1`.
- The Sorted Watcher's session log includes both real events (from the actual pipeline) and **synthetic seed events** for the live judge test — synthetic events are tagged `"synthetic": true` in the log.
- `DEMO_TIME_FACTOR=86400` compresses 14 days into 14 seconds during the live demo. Production uses real time.
- Rebecca is a composite of the 6,000+ real residents whose data is in our scraped dataset.

---

## Run it locally

```bash
git clone https://github.com/{{ org }}/sorted
cd sorted
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the dashboard (port 5050)
python dashboard/app.py

# Start the Sorted Watcher (separate terminal)
python -m src.agents.watcher

# Submit a test report (uses the Rebecca demo inputs)
python -c "
from src.agents.orchestrator import Orchestrator
from src.models.llm import get_default_provider
orch = Orchestrator(get_default_provider())
issue = orch.process(photo_path='demo_data/rebecca_photo.jpg',
                     voice_path='demo_data/rebecca_voice.m4a')
print(issue.model_dump_json(indent=2))
"
```

Requires: NVIDIA DGX Spark (or a swap to NVIDIA NIM cloud via `MODEL_PROVIDER=nim`), ElevenLabs API key, Twilio account + UK number.

See `docs/hackathon-prep/setup/` for end-to-end setup guides.

---

## Sponsors

This project was built at **NVIDIA Hack for Impact London** with hardware and software from **NVIDIA**, **HP**, **Nebius**, and **ElevenLabs**.

---

## Team Sorted

- **Ongun Ozdemir** — project lead, agent pipeline
- **{{ teammate_1_name }}** — data + UI
- **{{ teammate_2_name }}** — {{ teammate_2_role }}

---

## License

MIT — see [LICENSE](./LICENSE).

---

*"London's first computer was built to fix the city. So is its latest."*
````

---

## Placeholders to fill in at 10:00 Sunday

| Placeholder | Where it comes from |
|-------------|---------------------|
| `{{ video_title }}` | "Sorted — NVIDIA Hack for Impact London Submission" |
| `{{ youtube_url }}` | The unlisted YouTube link |
| `{{ dashboard_url }}` | The ngrok or hosted URL (or omit if local-only) |
| `{{ watcher_start_ts }}` | SQL: `SELECT MIN(ts) FROM watcher_session_log` |
| `{{ watcher_demo_ts }}` | SQL: `SELECT MAX(ts) FROM watcher_session_log` |
| `{{ watcher_duration }}` | Computed from the above |
| `{{ org }}` | GitHub org / username |
| `{{ teammate_1_name }}` | The Goldman teammate's name |
| `{{ teammate_2_name }}` | TBD member's name |
| `{{ teammate_2_role }}` | Locked at the briefing |

---

## Anti-patterns for the README

- ❌ Emoji explosions — at most three: 🎥 🌍 and one in the title
- ❌ Long architecture diagrams in ASCII — we have one, that's enough
- ❌ Glossy marketing language — we have one tagline, repeat it
- ❌ "TODO" sections — if it's a TODO, remove or fill before push
- ❌ Citing models we didn't use ("integrates with all major LLMs")
- ❌ Sales bullets — say what it does, not why it's amazing
- ❌ A "Why this matters" section after "What we built" — front-load the why

---

## Final review before push

Read the first 200 words out loud. Does it sell the project to someone who's never heard of us? If yes — push. If no — rewrite the opener.
