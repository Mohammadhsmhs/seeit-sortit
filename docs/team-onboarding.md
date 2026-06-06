# Team Onboarding — London Civic Agent

The London Civic Agent is an AI-powered pipeline that takes citizen reports of civic issues (potholes, fly-tipping, broken streetlights) and automatically classifies, scores severity, routes to the correct London borough council, and generates formal submissions. It runs on NVIDIA NIM with Llama 3.3 70B (mock mode available for offline dev).

## Quick Start

```bash
git clone <repo-url> && cd Nvidia\ Hackathon
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest src/tests/ -v                # run tests (mock mode, no API keys needed)
python -m src.eval.evaluate                   # run evaluation against 50 real reports
```

## Project Structure

```
src/
  agents/          # Core pipeline agents (intake, severity, routing, submission, escalation)
  models/          # LLM providers (mock, NIM, OpenAI-compatible)
  data/            # JSON config: boroughs, categories, severity factors, category mapping
  prompts/         # Prompt templates (.txt files)
  rag/             # RAG corpus and retriever for context enrichment
  nemo/            # NeMo Guardrails (PII redaction, topic filtering)
  integrations/    # External APIs (FixMyStreet, TfL, Twilio, ElevenLabs)
  dashboard/       # Flask web UI
  demo/            # Demo scenarios (JSON + runner)
  eval/            # Evaluation framework
  utils/           # Utilities (photo EXIF extraction)
  tests/           # Unit and integration tests
scraper/           # FixMyStreet scraper + SQLite DB (2374 real London reports)
data/raw/          # Census, schools, hospitals, collision data for RAG
docs/              # Architecture, evaluation reports, taxonomy docs
```

## Key Files to Know

| File | What it does |
|---|---|
| `src/agents/orchestrator.py` | Chains all agents: intake -> severity -> routing -> submission |
| `src/agents/intake.py` | Classifies reports into 19 categories |
| `src/agents/severity.py` | Scores 1-10 using rules, proximity data, repeat reports |
| `src/models/mock.py` | Offline keyword-based LLM substitute |
| `src/models/nim.py` | NVIDIA NIM API client |
| `src/config.py` | All env vars and paths |
| `src/data/category_mapping.json` | Maps 80+ FixMyStreet categories to our 19 parent categories |

## How to Add a New Agent

1. Create `src/agents/your_agent.py` with a class that has a `process(issue: CivicIssue) -> CivicIssue` method
2. Accept `LLMProvider` in `__init__` (works with mock or real LLM)
3. Wire it into `src/agents/orchestrator.py` at the appropriate pipeline step
4. Add tests in `src/tests/`

## How to Swap Mock for Real LLM

```bash
export MODEL_PROVIDER=nim
export NIM_API_KEY=nvapi-xxxxx
export NIM_MODEL=meta/llama-3.3-70b-instruct
python -m src.demo.run_demo
```

Or use a local vLLM endpoint:

```bash
export MODEL_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_MODEL=meta/llama-3.3-70b-instruct
```

## How to Run Tests

```bash
python -m pytest src/tests/ -v           # all tests
python -m pytest src/tests/test_pipeline.py -v -k "TestIntake"  # specific class
python -m src.eval.evaluate              # eval against real data (writes docs/evaluation-report.md)
```

## Current Status

- [x] Full pipeline working in mock mode (intake, severity, routing, submission, escalation)
- [x] 2374 real London reports scraped from FixMyStreet
- [x] Severity scoring with proximity to schools/hospitals, repeat-area detection, RAG context
- [x] Evaluation framework with classification, routing, and severity metrics
- [x] NeMo Guardrails (PII redaction, topic filtering)
- [ ] NIM integration tested end-to-end with Llama 3.3 70B
- [ ] Phone interface (Twilio + ElevenLabs voice)
- [ ] Photo analysis via Qwen2.5-VL-7B
- [ ] Dashboard polished for demo

## Team Roles (Assign)

| Role | Person | Focus |
|---|---|---|
| LLM / Infra Lead | TBD | NIM setup, prompt tuning, model serving |
| Frontend Lead | TBD | Dashboard UI, demo flow, presentation |
| Phone Integration Lead | TBD | Twilio, ElevenLabs, voice pipeline |
