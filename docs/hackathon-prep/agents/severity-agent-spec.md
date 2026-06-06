# Agent 02 — Severity

> Owner: **Ongun**. Time budget: **2 hours** (11:00–13:00 Saturday).
> Hands off to: routing agent.
> **THIS IS THE NEMOTRON BOUNTY AGENT.** Quality of citation matters; see `bounties/nemotron-bounty-strategy.md`.

---

## What it does

Take an intake-classified issue. Score how severe / how high-priority it is (0-10). **Cite specific facts from London open data** to justify the score.

```
INPUT
  CivicIssue (from intake)
    - category, latitude, longitude, photo_description, voice_transcript

OUTPUT
  CivicIssue (mutated, with these populated)
    - severity_score: int (0-10)
    - severity_rationale: str   # 2-3 sentences citing specific data
    - severity_citations: list[Citation]
                              # { source: str, fact: str, distance_m: int | None }
```

---

## Scoring rubric (the agent's job)

| Score | Description |
|-------|-------------|
| 0–2 | Cosmetic, side road, no vulnerable users nearby |
| 3–4 | Standard nuisance, residential street |
| 5–6 | Notable impact, school or hospital within 500m |
| 7–8 | Active hazard, school within 200m, traffic |
| 9–10 | Immediate safety risk to children or vulnerable adults |

The model produces both a number and a rationale. Both go on screen and into the dashboard.

---

## RAG data sources (the 4 we ground against)

| Source | What we extract | What we cite |
|--------|-----------------|--------------|
| **STATS19 collisions** (TfL via London Datastore) | Collisions within 500m of report location, last 5 years | "7 STATS19 serious injuries within 500m, including 1 cyclist" |
| **GIAS schools** (DfE) | Schools within 500m | "Osmani Primary School is 44m from the location" |
| **NHS organisation data** | Hospitals + GP surgeries within 1km | "BARNSLEY STREET NEIGHBOURHOOD MENTAL HEALTH CENTRE is 160m away" |
| **2021 Census LSOA density** (ONS) | Population density of the LSOA containing the point | "Population density of 17,095 people / sq km" |

Pre-loaded into SQLite at Saturday-morning RAG-corpus phase (`docs/hackathon-prep/reference/rag-data-shopping-list.md`).

**Query shape (one call per data source):**
```sql
SELECT name, ROUND((distance_m), 0) AS dist
FROM <source>
WHERE distance_m(latitude, longitude, ?, ?) < 500
ORDER BY dist
LIMIT 5;
```

We don't use embeddings. **Geometric proximity is the RAG.** Don't overthink it.

---

## Model — Nemotron Super 120B-A12B (locked)

Severity ranking is the bounty use case. See `bounties/nemotron-bounty-strategy.md` for the full rationale and comparative-evidence plan.

**Fallback chain:**
1. Nemotron Super local on Spark (preferred)
2. Nemotron via NVIDIA NIM endpoint (`build.nvidia.com`)
3. Llama 3.3 70B local (if Nemotron fails entirely — README still credits Nemotron, comparison runs separately)

Wired through `src/models/llm.py` so swap is a one-line change.

---

## Step-by-step build outline (2 hours)

1. **0:00–0:15** — RAG store: bulk-load the 4 datasets into SQLite tables with proper indexes on lat/lon (use a simple `(lat * 1000) >> 0` bucket index if SpatiaLite isn't available).
2. **0:15–0:30** — Distance function: a Python `haversine_m(lat1, lon1, lat2, lon2) -> float`. Used everywhere.
3. **0:30–0:50** — Retrieval: write 4 functions that each return the top-N items within 500m / 1km. Test on Rebecca's coordinates (51.521, -0.0656).
4. **0:50–1:20** — Severity prompt: write a Nemotron prompt that takes the issue + the 4 RAG results + the rubric and returns a JSON `{score, rationale, citations}`.
5. **1:20–1:40** — Smoke test on 3 known reports from the scraper. Verify citations reference real numbers and named entities.
6. **1:40–1:55** — Wire to orchestrator: severity reads the intake output, writes mutated CivicIssue.
7. **1:55–2:00** — Persist to `processed_issues` table (severity_score, severity_rationale columns).

---

## Cursor build prompt (paste at 11:00)

```
GOAL: Build the severity agent. Given a CivicIssue (with latitude, longitude,
category, photo_description, voice_transcript), score it 0-10 and produce a
2-3 sentence rationale citing SPECIFIC facts from four London open datasets.

CONSTRAINTS:
- File: src/agents/severity.py
- LLM: use NemotronProvider (src/models/nemotron.py) — model "nemotron-super:120b"
  via Ollama, base_url localhost. Fallback chain in src/models/llm.py if it errors.
- RAG: SQLite tables already populated by build-prompt-rag-corpus run (Saturday
  morning). Tables: rag_collisions, rag_schools, rag_hospitals, rag_lsoa.
  Each row has columns: name, latitude, longitude, extra_json.
- Distance: write haversine_m() in src/utils/geo.py. Don't depend on SpatiaLite.
- For each source: SELECT items where haversine_m(lat, lon, issue.lat, issue.lon)
  is below threshold (500m collisions/schools, 1km hospitals, point-in-polygon
  for the LSOA — or approximate by nearest centroid).
- Pass the RAG results to Nemotron in a JSON-shaped prompt. Require JSON output:
  { "score": int 0-10, "rationale": str, "citations": [{source, fact, distance_m}] }
- Use json.loads to parse. If parsing fails, retry once with "PLEASE RETURN VALID JSON".
- Persist mutated CivicIssue to processed_issues table — columns severity_score,
  severity_rationale, severity_citations (JSON).

ACCEPTANCE:
- python -c "
   from src.agents.severity import SeverityAgent
   issue = build_test_issue(lat=51.521, lon=-0.0656, category='Waste and Fly-Tipping')
   r = SeverityAgent().process(issue)
   assert 0 <= r.severity_score <= 10
   assert len(r.severity_rationale) > 50
   assert any('Osmani' in c.fact for c in r.severity_citations) or \
          any('STATS19' in c.source for c in r.severity_citations)
   print(r.severity_score, r.severity_rationale)
   "

CONTEXT:
- Look at src/models/llm.py and src/agents/intake.py for the existing pattern.
- decisions-locked.md says no async, vanilla Python.
- nemotron-bounty-strategy.md says citation faithfulness is THE win condition —
  the model must reference the dataset name AND a specific value (distance,
  count, name). Generic "near a school" answers don't count.
- Scoring rubric is in this file — embed it in the system prompt.
```

---

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Nemotron returns prose, not JSON | Prompt drift | Re-ask with "Return only the JSON object" |
| Citations all say "n/a" | RAG returned nothing | Verify RAG tables loaded (`SELECT COUNT(*) FROM rag_schools`) |
| Score is always 9 or always 5 | Model gaming the rubric | Inject 3 few-shot examples showing distinct scores |
| Latency >10 sec | Nemotron cold | Pre-warm at orchestrator startup |
| Wrong citations (hallucination) | Model fabricated | Validate citation `fact` against returned RAG rows; drop if no match |

---

## Smoke test (`tests/smoke_severity.py`)

Run on 3 real reports. Print score + rationale for visual inspection.

```python
from src.agents.severity import SeverityAgent
from src.models.intake import CivicIssue

cases = [
    # Tower Hamlets fly-tipping near schools (should score high)
    CivicIssue(latitude=51.521, longitude=-0.0656, category="Waste and Fly-Tipping",
               photo_description="Pile of mattresses", voice_transcript="near the school",
               photos=[], raw_voice_text=""),
    # Suburban residential pothole (should score moderate)
    CivicIssue(latitude=51.55, longitude=0.10, category="Roads and Highways",
               photo_description="Small pothole", voice_transcript="on my side street",
               photos=[], raw_voice_text=""),
]
for c in cases:
    r = SeverityAgent().process(c)
    print(f"{r.severity_score}/10 — {r.severity_rationale[:100]}")
```

---

## Hand-off

Output → **routing agent**. Routing reads `category` + `latitude` + `longitude` to determine the council. Severity score travels through but is not used for routing — it appears in the demo dashboard and on the agent's spoken summary during the phone call.
