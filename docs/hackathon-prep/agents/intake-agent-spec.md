# Agent 01 — Intake

> Owner: **Ongun**. Time budget: **90 min** (start 09:30 Sat — done by 11:00).
> Hands off to: severity agent.

---

## What it does

Take a photo + a voice note. Return a structured `CivicIssue` the rest of the pipeline can reason over.

```
INPUT
  - photo: bytes (jpeg) — Rebecca snapped this on her phone
  - voice_note: bytes (m4a / mp3 / wav) — "There's dumped rubbish outside the school"
  - device_location: (lat, lon) — optional fallback if EXIF stripped

OUTPUT
  CivicIssue(
    photo_description: str,       # "Pile of mattresses and bin bags on a pavement"
    voice_transcript: str,        # "There's dumped rubbish outside the school"
    category: str,                # one of our 18 taxonomy categories (see issue-taxonomy/)
    subcategory: str | None,      # e.g. "Dumped or flytipped waste"
    latitude: float,              # from EXIF or device_location
    longitude: float,
    address: str | None,          # reverse-geocoded
    severity_hint: int | None,    # 0-10 — leave None, severity agent owns this
    photos: list[str],            # local paths
    raw_voice_text: str,          # full transcript for the watcher
  )
```

---

## Model choices (already locked in `decisions-locked.md`)

| Step | Model | Where it runs |
|------|-------|---------------|
| Photo → description + category | **Qwen2.5-VL-7B** via Ollama | DGX Spark |
| Voice → transcript | **ElevenLabs Scribe** | Cloud |
| Category mapping (raw → taxonomy) | **Llama 3.3 70B** via Ollama (small JSON-fixing call) | DGX Spark |
| Reverse geocoding | Nominatim (OpenStreetMap) | Public API, no key needed |

**Why these:** Qwen handles photos + text in one shot, Scribe is bundled with our ElevenLabs key, Llama is already loaded for downstream agents, Nominatim is free and doesn't need an API key.

---

## EXIF GPS extraction

Modern iPhone photos contain GPS in EXIF. *Unless* they were shared via certain apps that strip it. Our flow:

1. Try EXIF first using `exifread` or Pillow's `_getexif()`
2. If no GPS, fall back to `device_location` (passed in from the browser's `navigator.geolocation`)
3. If both missing, **prompt the user to confirm a pin on a map** — the consumer intake page must support this. Owner: intake-UI builder.

For the demo: Rebecca's photo will have EXIF intact (we control it). The fallback is for the live judge test if they try a real photo.

---

## Step-by-step build outline (90 min)

1. **0:00–0:10** — File scaffolding. Create `src/agents/intake.py`, `src/models/intake.py` (Pydantic), wire to orchestrator stub.
2. **0:10–0:30** — Vision call. Send the photo to Qwen2.5-VL with a system prompt that asks for one of our 18 categories + a short description. Smoke-test with a real fly-tipping photo from `scraper/photos/`.
3. **0:30–0:45** — Voice call. Send the audio to ElevenLabs Scribe. Smoke-test with a recorded voice note.
4. **0:45–0:55** — EXIF GPS. Extract or fall back. Smoke-test with a photo that has EXIF, and one that doesn't.
5. **0:55–1:10** — Reverse geocode via Nominatim. Add 200ms-friendly caching so we don't hammer the API.
6. **1:10–1:25** — Category fix-up. Sometimes Qwen returns "fly tipping" instead of our canonical "Fly-Tipping" — pass through Llama with the taxonomy as JSON, asking for the closest match.
7. **1:25–1:30** — Persist to SQLite (`issues` table). The dashboard reads from here.

---

## Cursor build prompt (copy-paste into Cursor at 09:30)

```
GOAL: Build the intake agent for our civic complaint pipeline. Input is a photo
file and a voice-note audio file. Output is a Pydantic CivicIssue object with
fields described below, persisted to SQLite.

CONSTRAINTS:
- File: src/agents/intake.py
- Pydantic models: src/models/intake.py (CivicIssue defined as shown below)
- Vision: ollama.chat with model "qwen2.5vl:7b". Use the LLMProvider
  abstraction in src/models/base.py if it exists, otherwise call ollama directly.
- STT: elevenlabs.client.ElevenLabs.speech_to_text.convert with model "scribe_v1"
- EXIF: pip install Pillow, use _getexif() to extract GPS; convert from rational
  to decimal degrees
- Geocoding: GET https://nominatim.openstreetmap.org/reverse?lat=X&lon=Y&format=json
  with a User-Agent header "Sorted/1.0 (hackathon)"
- Category taxonomy (load from this list, snap to closest):
  Roads and Highways, Waste and Fly-Tipping, Street Cleaning, Street Lighting and
  Traffic, Pavements and Footways, Vehicles, Trees and Vegetation, Parks and Public
  Spaces, Noise and Nuisance, Pollution, Antisocial Behaviour, Housing, Planning and
  Building, Pest Control, Food and Business, Dead Animals, Utilities, Fraud and Misuse
- DB: scraper/fixmystreet.db, new table 'processed_issues' with id, photo_description,
  voice_transcript, category, subcategory, latitude, longitude, address, photo_paths,
  raw_voice_text, created_at
- No async. Synchronous Python only.

ACCEPTANCE:
- python -c "from src.agents.intake import IntakeAgent; \
   r = IntakeAgent().process(photo_path='test_photo.jpg', voice_path='test_voice.m4a'); \
   print(r.model_dump_json(indent=2))"
   prints a CivicIssue with non-null category, latitude, longitude, photo_description,
   voice_transcript.

CONTEXT:
- Look at any existing src/models/*.py and src/agents/*.py for patterns.
- decisions-locked.md says no async, no React, vanilla Python.
- The 18 categories must snap-fit — if Qwen returns "flytipping", we should
  return "Waste and Fly-Tipping" (use Llama 3.3 to snap to the closest match
  with a 1-shot JSON prompt).
- Failure mode: if Scribe API errors, fall back to the empty string and log a
  warning. Do not crash.

CivicIssue pydantic model:
  class CivicIssue(BaseModel):
      photo_description: str
      voice_transcript: str
      category: str
      subcategory: Optional[str] = None
      latitude: float
      longitude: float
      address: Optional[str] = None
      severity_hint: Optional[int] = None
      photos: list[str]
      raw_voice_text: str
```

That prompt is ~25 lines. Paste it into Cursor as one block. Expect 2-3 follow-up refinements.

---

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Qwen returns text but no category match | System prompt unclear | Add few-shot examples in the prompt |
| Scribe returns empty | File format unsupported | `ffmpeg -i in.m4a out.wav` first |
| EXIF GPS missing | Photo shared via WhatsApp | Use `device_location` fallback |
| Nominatim rate-limit | Free tier is 1 req/sec | Cache results in SQLite |
| Pipeline crashes on bad photo | Qwen failure | Catch + return category="Unknown" + photo_description="(unrecognised)" |

---

## Smoke test (run this every time you change intake)

```python
# tests/smoke_intake.py
from src.agents.intake import IntakeAgent

issue = IntakeAgent().process(
    photo_path="scraper/photos/flytipping/4078347_0.jpeg",  # known fly-tipping photo
    voice_path="demo_data/rebecca_voice.m4a",
)
assert issue.category == "Waste and Fly-Tipping", f"Wrong category: {issue.category}"
assert -0.5 < issue.longitude < 0.5, "London bounds check"
assert 51 < issue.latitude < 52
print("PASS")
```

---

## Hand-off

When this works, your output goes to the **severity agent**. It needs the category and lat/lon. Make sure those two fields are never None when you hand off.
