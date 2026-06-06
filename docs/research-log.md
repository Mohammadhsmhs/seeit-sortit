# Research Log

## 2026-06-01 — Feasibility Assessment

### DGX Spark / GB10 Hardware
- 128 GB unified LPDDR5x memory (shared CPU + GPU, no separate VRAM)
- 6,144 CUDA cores, 192 Tensor Cores (gen5), 4 TB NVMe SSD, 140W TDP
- Max model size on single unit: ~200B params (quantized)
- Llama 3.3 70B (Q4): ~35–45 tok/s — confirmed fits
- Llama 4 Scout (17B active / 109B MoE): fits comfortably
- Nemotron Ultra (~253B): does NOT fit on single Spark — needs 2 linked units
- Nemotron Super 120B-A12B (MoE): fits but tight, ~18 tok/s
- Pre-installed: Ollama, TensorRT-LLM, NIM containers, NeMo framework, vLLM
- Two 70B-class models cannot coexist in 128 GB simultaneously — must time-slice or use one large + one small

### ElevenLabs
- Outbound calls: supported via `POST /v1/convai/twilio/outbound-call` — requires Twilio as telephony provider
- IVR navigation: supported via DTMF tones (in-band and out-of-band)
- Free tier: ~10,000 credits/month (~15 min of agent conversation)
- Latency: p50 first-chunk 75–150ms with `eleven_flash_v2_5`
- Scribe STT: 99 languages, available

### FixMyStreet
- Run by **mySociety** (UK charity, not government, not private company) since 2007
- Revenue model: FixMyStreet Pro (paid SaaS for councils)
- `/import` API exists — POST with subject, name, email, detail, lat/lon, photo. No auth needed.
- **Critical:** submitted reports require user email confirmation click — not fully automatable
- **Reports are PUBLIC** — text, photos, location all visible on their website/map
- Email, phone never published. Name display is opt-in.
- This conflicts with "no photos leave the hardware" pitch if we upload photos

**Competitive positioning:** FixMyStreet is a reporting form. We're building an agent that acts on behalf of the user. Different product category entirely. FixMyStreet doesn't track SLAs, doesn't escalate, doesn't rank severity, doesn't do follow-through.

**Scraping opportunity:** Reports are public, geolocated, categorised. Useful for:
- Training/validation data for our classifier
- Severity signal (cluster of reports = systemic issue)
- Evidence in escalation letters ("reported 6 times over 3 months")

### London Open Data
- **London Datastore** (data.london.gov.uk): active, 700+ datasets, CSV/XLS/GeoJSON. No API key needed.
- **TfL Unified API**: free with registration (app_id + app_key). Endpoints: `/AccidentStats/{year}`, `/Road/{ids}/Disruption`, `/Road`. AccidentStats lags ~1 year.
- **DfT traffic volume**: open, AADF counts per count-point, CSV + REST API, filterable to London
- **STATS19 collision history**: available via London Datastore, CSV, 1979–2024
- **Footfall data: RESTRICTED** — High Streets Data Partnership data gated behind membership. Use TfL station entry/exit as proxy.
- **Schools (GIAS)**: free CSV, daily updates, filterable to London
- **Hospitals (NHS ODS)**: CSV download
- **Care homes (CQC)**: monthly CSV from cqc.org.uk
- **Census 2021**: ward + LSOA level, free from London Datastore/ONS/NOMIS
- **City of London portal (data.cityoflondon.gov.uk): DOES NOT EXIST** — use London Datastore or data.gov.uk

### NeMo Agent Toolkit
- v1.7, formerly "AgentIQ", actively developed
- Framework-agnostic: wraps LangChain, LlamaIndex, CrewAI, etc.
- Includes RAG evaluation, profiling, observability (OpenTelemetry)
- NeMo Guardrails: separate project, NOT yet integrated into Agent Toolkit (on roadmap)
- Learning curve: moderate. Thin wrapper if you already use LangChain/LlamaIndex.
- No GPU required for the toolkit itself — only for local LLM inference

### Reportable Issue Categories (researched 2026-06-01)
18 categories, ~60+ specific issue types identified from FixMyStreet, London borough websites, GOV.UK.

**By volume (FixMyStreet data, ~12k reports/month UK-wide):**
- Road defects (potholes, paving, markings): ~50% of all reports
- Environmental (litter, fly-tipping, dog fouling): ~25%
- Everything else: ~25% (abandoned vehicles, trees, noise, pest control, planning, etc.)

**Photo-classifiable categories (13 of 18):** potholes, fly-tipping, graffiti, abandoned vehicles, trees/vegetation, pavement damage, parks, street furniture, antisocial behaviour evidence, housing exterior, planning violations, dead animals, some utilities. These cover ~75% of reports by volume.

**Non-photo categories (5 of 18):** noise/nuisance, pollution (some), pest control (some), food/business, fraud/misuse. These need voice/text description intake path.

**Weekly FixMyStreet volumes:** fly-tipping ~1,550/week, graffiti ~1,020/week, potholes ~870/week.

**Demographic pattern:** More deprived areas report litter/fouling; more affluent areas report potholes. Reporting highest at deprivation decile 7 (moderately affluent).

**Demo recommendation:** Fly-tipping (visual, emotional, geolocated) + potholes (volume king). Two scenarios showing different issue types.

**Data sources for scraping:** mySociety publishes per-authority dashboards and ward-level data. Academic datasets at research.mysociety.org and data.mysociety.org.

### Past NVIDIA Hackathon Winners
- **Loomin** (GTC 2026, 1st): physics learning tool, Nemotron Ultra + RAG, ~300 participants
- **cuOptIQ** (Agent Toolkit Hackathon, 1st): multi-agent logistics with cuOpt + Omniverse
- **OpenCodeReview** (2nd): automated code security, config-swappable model pattern
- Judges value: real-world applicability, NVIDIA stack usage, multi-agent orchestration working e2e
