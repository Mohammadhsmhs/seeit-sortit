# Project Plan — London Civic Agent

## Queued (next session)
- **Council connectors** — build email + web-form delivery for all 33 boroughs. Research real department email addresses per borough. Add SMTP-based submission integration. Browser-automation stubs for councils with web-form-only intake. Delivery selector that picks API > email > web form > FixMyStreet fallback per (borough, category).

## Overview
Multi-agent civic complaint system for NVIDIA Hack for Impact London (5–7 June 2026).
Photo + voice in → classified, ranked, routed, filed, tracked, escalated.

## Architecture (revised post-feasibility)

### Models
| Role | Model | Notes |
|------|-------|-------|
| Vision (intake) | Qwen2.5-VL-7B or Llama 4 Scout | Small enough to coexist with main LLM |
| Reasoning / routing / drafting | Llama 3.3 70B (Q4) | ~35–45 tok/s on DGX Spark. Swap to Nemotron Super 120B if NVIDIA brownie points matter. |
| STT | ElevenLabs Scribe | 99 languages |
| Phone escalation | ElevenLabs Conversational AI | Requires Twilio integration |
| RAG | TensorRT-LLM + local vector store | Pre-load corpus before hackathon |

### Agents (priority order)
| # | Agent | Priority | Est. Hours | Status |
|---|-------|----------|------------|--------|
| 1 | Intake (photo + voice → structured issue) | P0 | 4–6 | **DONE** (mock mode) |
| 2 | Severity Ranking (RAG over London open data) | P0 | 6–8 | **DONE** (mock mode with proximity scoring) |
| 3 | Routing (which council/authority?) | P0 | 2–3 | **DONE** (mock mode) |
| 4 | Submission (council API / email) | P0 | 2–3 | **DONE** (mock mode) |
| 5 | Phone Escalation (ElevenLabs + Twilio) | P1 | 6–8 | Not started |
| 6 | CRM Tracking + SLA Monitor | P2 | 4–6 | Not started |
| 7 | Public Dashboard + Council Leaderboard | P1 | 4–6 | **DONE** (Leaflet map, Chart.js, live DB data, port 5050) |
| 8 | Further Escalation (LGO/MP drafts) | P3 — cut if behind | 4–6 | Not started |
| 9 | Multilingual | P3 — cut if behind | 2–3 | Not started |
| 10 | NeMo Guardrails | P3 — cut if behind | 3–4 | Not started |

### Pre-Hackathon Build (completed)
| Component | Status | Details |
|-----------|--------|---------|
| App scaffolding (`src/`) | **DONE** | 24 files, `python -m src.main --demo` works, 5/5 tests pass |
| FixMyStreet scraper | **DONE** | 2,374 reports across 9 London boroughs (Barnet, Bromley, Camden, Greenwich, Hackney, Islington, Lewisham, Southwark, Westminster) |
| FixMyStreet deep analysis | **DONE** | 433-line report in `docs/fixmystreet-analysis.md` — 189 categories, resolution stats, urgency signals, demo scenarios |
| Issue taxonomy conversion | **DONE** | `src/data/categories.json` (56 categories), `src/data/boroughs.json` (33 authorities), `src/data/severity_factors.json` |
| Category mapping | **DONE** | `src/data/category_mapping.json` — 79 raw FMS categories mapped to parent taxonomy |
| Severity factors integration | **DONE** | SeverityAgent reads `severity_factors.json` (56 categories, proximity modifiers, repeat report modifiers) |
| Demo script + scenarios | **DONE** | `src/demo/run_demo.py` with ANSI colors, 3 scenario JSONs (flytipping, pothole, streetlight) |
| Hackathon pitch doc | **DONE** | `docs/hackathon-pitch.md` and `docs/demo-script.md` |
| Makefile | **DONE** | `make test`, `make demo`, `make dashboard`, `make scrape` |

### Data Pipeline
Pre-load before hackathon weekend:
- [x] TfL collision history (STATS19 CSV) — 20,834 London collisions downloaded
- [ ] DfT traffic volume (AADF CSV, London filter)
- [ ] TfL road network data (API)
- [x] Schools (GIAS CSV, London filter) — 5,881 schools downloaded
- [x] Hospitals (NHS ODS CSV) — 6,432 NHS sites downloaded
- [x] Care homes (CQC CSV) — 9,390 CQC providers downloaded
- [x] Census 2021 population density (LSOA level) — 4,994 LSOAs downloaded
- [ ] TfL station entry/exit counts (footfall proxy)
- [x] FixMyStreet scraped reports — 2,374 reports, 9 boroughs, 189 categories

### Key Integrations
- [ ] ElevenLabs Scribe (STT)
- [ ] ElevenLabs Conversational AI + Twilio (outbound calls)
- [x] FixMyStreet scraper (public report data) — working, 2,374 reports collected
- [ ] TfL Unified API (live disruptions, collision stats)
- [ ] NeMo Agent Toolkit (orchestration)

## What Still Needs to Happen (at hackathon)
1. **Real LLM integration** — swap mock mode for actual Llama 3.3 70B / Nemotron Super inference on DGX Spark
2. **Phone escalation** — ElevenLabs Conversational AI + Twilio outbound call integration
3. **NeMo Agent Toolkit** — orchestration layer connecting all agents
4. **End-to-end testing with real models** — full pipeline from photo/voice input through to council submission
5. **Vector index** — build RAG vector store over downloaded corpus (STATS19, schools, hospitals, care homes, census)
6. **Wire RAG proximity scoring** — connect real school/hospital/care home data to severity agent (currently uses mock proximity)
7. **DfT traffic volume + TfL data** — remaining dataset downloads
8. **CRM skeleton** — if time permits (P2)
9. **Demo polish** — recorded phone call fallback, presentation rehearsal

## Pre-Hackathon Checklist (before 5 June)
- [ ] Lock team (3–5 confirmed)
- [ ] Decide Llama 3.3 70B vs Nemotron Super for reasoning layer
- [x] Download and chunk all RAG corpus data (5 of 8 datasets downloaded)
- [ ] Build vector index over corpus
- [ ] Get ElevenLabs + Twilio sandbox working with outbound calls
- [ ] Map 3 London boroughs' reporting endpoints (Camden, Hackney, City of London)
- [x] Build FixMyStreet scraper (2,374 reports, 9 boroughs)
- [x] Sketch demo arc and rehearse (demo script + 3 scenarios + pitch doc written)
- [ ] Test photo EXIF GPS handling (iOS HEIC)

## Hackathon Timeline (5–7 June)
### Friday evening (18:00–23:00)
- DGX Spark setup, model deployment, environment config
- Verify pre-loaded RAG corpus works on-device
- Swap agent mock mode for real LLM calls

### Saturday (09:00–23:00)
- AM: Wire real LLM into intake + severity agents, build vector index
- PM: End-to-end pipeline testing, RAG proximity scoring with real data
- Evening: Phone escalation integration (P1)

### Sunday (09:00–15:00)
- AM: End-to-end integration, bug fixes, demo rehearsal
- PM: Demo polish, recorded fallback for phone call
- 15:00–17:00: Presentations

## Risks
| Risk | Mitigation |
|------|------------|
| Nemotron Ultra doesn't fit on Spark | Already dropped — using Llama 3.3 70B or Nemotron Super |
| FixMyStreet email confirmation blocks full automation | Submit text-only, describe photo instead of uploading; or use council-direct APIs |
| Photos on FixMyStreet break privacy pitch | Don't upload photos; agent describes what it sees |
| Live phone demo fails | Pre-recorded fallback, rehearsed |
| Footfall data restricted | Use TfL station entry/exit as proxy |
| Team too small | Recruiting — need minimum 3 for P0 + P1 scope |
| Over-scoped | Cut P3 items on Saturday morning if P0 isn't working e2e |
| Mock-to-real transition | All agents have clean LLM abstraction layer — swap should be straightforward |
