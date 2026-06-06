# London Civic Agent

AI-powered multi-agent system that classifies, scores, routes, and escalates civic complaints across London's 33 boroughs — built for the NVIDIA Hack for Impact London 2026.

## Quick Start

```bash
pip install -r requirements.txt
python -m src.main --demo              # run 3 demo scenarios (mock mode, no GPU needed)
python -m src.demo.run_demo --fast     # polished presentation-ready demo
```

## Architecture

The pipeline processes a citizen's complaint through five sequential agents:

1. **Intake Agent** -- Parses free-text descriptions, classifies into 19 issue categories (Roads, Waste, Lighting, etc.), extracts subcategory, location hints, and generates a title.

2. **Severity Agent** -- Scores each issue 1-10 using a rule-based matrix combining:
   - Category base scores (from analysed FixMyStreet data)
   - Hazard keyword detection (gas leak, asbestos, etc.)
   - Proximity to schools, hospitals, care homes (real geospatial data)
   - Collision hotspot analysis (Stats19 road accident data)
   - Population density from Census 2021 LSOAs
   - Repeat-report clustering (SQLite DB of 1000+ scraped reports)
   - **Live TfL road disruption data** (real-time API, no auth required)

3. **Routing Agent** -- Maps the issue to the correct London borough council or Transport for London (TfL) using coordinate-to-borough lookup, postcode extraction, landmark matching, and TfL road network detection.

4. **Submission Agent** -- Generates a formal, structured report ready for council submission systems.

5. **Escalation Agent** -- When issues exceed SLA thresholds, generates staged escalation: follow-up letters, formal complaints, and Local Government Ombudsman / MP referrals.

**Cross-cutting concerns:**
- **NeMo Guardrails** -- Input/output safety rails (PII redaction, topic filtering, hallucination checks)
- **RAG Corpus** -- Pre-built geospatial index over schools, hospitals, care homes, and road collisions for context-rich justifications
- **TfL Live API** -- Real-time road status and disruption data from Transport for London

All agents run locally on a single machine. In mock mode (default), no GPU or network is required.

## Features

- **19 civic issue categories** with 56 subcategories derived from real FixMyStreet report analysis
- **Geospatial severity scoring** using real London datasets (schools, hospitals, care homes, road collisions, population density)
- **Live TfL integration** -- real-time road disruption data enriches severity assessments
- **33-borough routing** with postcode, landmark, and coordinate-based resolution
- **Multi-stage escalation** with auto-generated formal complaints and MP referral letters
- **NeMo Guardrails** for PII redaction and topic safety
- **RAG-enriched justifications** with nearby real-world context
- **Flask dashboard** with borough performance analytics
- **Runs on NVIDIA DGX Spark** with Llama 3.3 70B via Ollama, or in mock mode on any laptop

## Demo Instructions

**Mock mode (no GPU, no network):**
```bash
python -m src.demo.run_demo --fast     # all 3 scenarios, no delays
python -m src.demo.run_demo            # with presentation animations
python -m src.demo.run_demo --scenario 2  # single scenario (pothole on A205)
```

**With a real LLM (Ollama / NIM):**
```bash
export MODEL_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export OPENAI_MODEL=llama3.3:70b-instruct-q4_K_M
python -m src.demo.run_demo
```

**Dashboard:**
```bash
python -m src.dashboard.app            # opens on http://localhost:5050
```

**Single issue:**
```bash
python -m src.main "Deep pothole on the A205 near Herne Hill" --lat 51.455 --lon -0.096
```

## Development Setup

```bash
# Clone and set up
git clone <repo-url> && cd london-civic-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest src/tests/ -v

# Run demo
python -m src.main --demo
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_PROVIDER` | `mock` | `mock`, `openai`, or `nim` |
| `OPENAI_BASE_URL` | `http://localhost:8000/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `meta/llama-3.1-8b-instruct` | Model name |
| `NIM_API_KEY` | (empty) | NVIDIA NIM API key |
| `TFL_APP_KEY` | (empty) | Optional -- raises TfL rate limit |

## DGX Spark Deployment

The system is designed to run entirely on a single NVIDIA DGX Spark (128 GB unified memory) with Llama 3.3 70B quantised to Q4:

```bash
# One-command setup (GPU check, Ollama install, model pull, pipeline verification)
bash scripts/setup_spark.sh

# Or use Docker Compose
docker compose up -d
docker compose exec ollama ollama pull llama3.3:70b-instruct-q4_K_M
```

Key specs:
- **Model:** Llama 3.3 70B Q4_K_M (~40 GB VRAM)
- **Inference:** Ollama with OpenAI-compatible API on port 11434
- **Dashboard:** Flask on port 5050
- **Latency:** ~3-5s per issue end-to-end on DGX Spark

## Project Structure

```
london-civic-agent/
├── src/
│   ├── agents/              # Pipeline agents
│   │   ├── intake.py        #   Text parsing and classification
│   │   ├── severity.py      #   Rule-based severity scoring (1-10)
│   │   ├── routing.py       #   Borough/council routing
│   │   ├── submission.py    #   Formal report generation
│   │   ├── escalation.py    #   SLA-based escalation
│   │   └── orchestrator.py  #   Pipeline coordinator
│   ├── models/              # LLM provider abstraction
│   │   ├── base.py          #   CivicIssue model + LLMProvider ABC
│   │   ├── mock.py          #   Offline mock (keyword-based)
│   │   ├── nim.py           #   NVIDIA NIM provider
│   │   └── openai_compat.py #   OpenAI-compatible (Ollama/vLLM)
│   ├── integrations/        # External services
│   │   ├── tfl.py           #   TfL Unified API (live, no auth)
│   │   ├── fixmystreet.py   #   FixMyStreet submission
│   │   ├── elevenlabs.py    #   Voice synthesis
│   │   └── twilio.py        #   Phone/SMS
│   ├── nemo/                # NeMo Guardrails
│   ├── rag/                 # RAG corpus and retriever
│   ├── data/                # JSON configs, geospatial index
│   ├── dashboard/           # Flask web dashboard
│   ├── demo/                # Presentation demo runner
│   ├── tests/               # Unit and integration tests
│   ├── config.py            # Central configuration
│   └── main.py              # CLI entry point
├── data/
│   ├── raw/                 # Source datasets (schools, hospitals, Stats19)
│   └── rag_index.json       # Pre-built RAG index
├── scraper/                 # FixMyStreet data scraper
├── scripts/                 # Setup and deployment scripts
├── docs/                    # Documentation and research
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Team

*London Civic Agent Team -- NVIDIA Hack for Impact London 2026*

## License

MIT
