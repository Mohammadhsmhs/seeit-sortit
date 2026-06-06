# Build Prompt — Orchestrator

> Paste into Cursor at **15:30 Saturday** (after the 4 sequential agents exist). Estimated build time: **45 min**.
>
> Companion spec: `agents/intake-agent-spec.md`, `agents/severity-agent-spec.md`, `agents/routing-agent-spec.md`, `agents/submission-agent-spec.md`. The orchestrator just wires them.

---

## What you're about to build

A single Python module that takes a photo + voice + optional GPS and returns a fully-processed `CivicIssue` written to SQLite. Sequential pipeline. No concurrency. Each stage failure is logged but never crashes the call.

The watcher (escalation agent) runs SEPARATELY and watches the SQLite table — not invoked by the orchestrator.

---

## Paste this prompt into Cursor

```
GOAL: Build src/agents/orchestrator.py — a single Python module that wires the
intake → severity → routing → submission agents together. One synchronous call
processes one CivicIssue end-to-end and persists the result.

CONSTRAINTS:
- File: src/agents/orchestrator.py
- Synchronous. Plain Python. No asyncio.
- Imports: from src.agents.intake import IntakeAgent (and the other three)
- Each agent has a .process(issue_or_inputs) -> CivicIssue method per the
  agent specs in docs/hackathon-prep/agents/.
- Public API: Orchestrator(llm_provider, ...).process(photo_path, voice_path,
  device_lat=None, device_lon=None) -> CivicIssue
- The orchestrator owns:
  1. Building an empty CivicIssue from raw inputs (just photo_path passed
     through; intake fills the rest)
  2. Calling intake, severity, routing, submission IN ORDER
  3. Catching exceptions per stage. On exception, log to a stage_errors
     table and continue with whatever fields the previous stage populated.
  4. After submission completes, INSERT or UPDATE in the processed_issues
     table (this is what the watcher polls)
  5. Returns the final CivicIssue
- DEMO_MODE handling: if os.getenv("DEMO_MODE") == "1" and issue.borough ==
  "Tower Hamlets", retarget submission to Camden Open311 sandbox BEFORE
  calling the submission agent. Set issue.demo_actual_target = "Camden".
- Logging: print a single line per stage with timing — "intake 1.2s OK",
  "severity 4.7s OK", "routing 0.0s OK", "submission 1.8s OK".

ACCEPTANCE:
- python -c "
   from src.agents.orchestrator import Orchestrator
   from src.models.llm import get_default_provider
   orch = Orchestrator(get_default_provider())
   issue = orch.process(photo_path='demo_data/rebecca_photo.jpg',
                        voice_path='demo_data/rebecca_voice.m4a')
   assert issue.category is not None
   assert issue.severity_score is not None
   assert issue.borough is not None
   assert issue.submission_status in ('submitted','failed','queued')
   print(f'{issue.category} | sev {issue.severity_score} | {issue.borough} -> {issue.submission_status}')
   "

CONTEXT:
- The four agent specs are in docs/hackathon-prep/agents/*-agent-spec.md.
  Each spec defines the agent's input, output, and a build prompt for itself.
  Assume those agents already exist before the orchestrator is built.
- decisions-locked.md mandates synchronous, no React, SQLite, plain Python.
- The watcher in src/agents/watcher.py is a SEPARATE process that polls
  processed_issues every 30 seconds — the orchestrator just writes to that
  table. Do not call the watcher.
- On failure of any single stage, downstream stages still get called with
  whatever the previous stage managed to produce. e.g. if severity throws,
  severity_score stays None and routing still runs on the raw lat/lon.
  This is how we never lose a citizen report mid-pipeline.
- Logging table: stage_errors with columns id, run_id, stage, error_msg,
  ts. Generate run_id as a uuid4 at the start of each .process() call.

HAND-OFF:
- Output flows to processed_issues table.
- The watcher (separate process) picks up rows from there.
- The dashboard reads from there too.
```

---

## After the AI produces the orchestrator

1. **Run the acceptance test verbatim.** If it fails, paste the error back into Cursor and ask for a fix.
2. **Run it 3 more times back-to-back** to verify no shared state corruption.
3. **Verify the `processed_issues` row** in SQLite:
   ```bash
   sqlite3 scraper/fixmystreet.db "SELECT id, category, severity_score, borough, submission_status FROM processed_issues ORDER BY id DESC LIMIT 1;"
   ```
4. **Stage failure rehearsal** — set `OPEN311_FORCE_FAIL=1` env var (orchestrator should respect it) and verify it still writes a row with `submission_status='failed'` and logs to `stage_errors`.
5. Commit: `chore: orchestrator end-to-end working on Rebecca`.

---

## Common AI-output corrections

| If the AI generates | Correct it with |
|---------------------|-----------------|
| async functions | "Make this fully synchronous, remove async/await keywords" |
| `pip install` for fancy ORMs (SQLAlchemy, etc.) | "Use only the standard library sqlite3 module" |
| Concurrent agent calls | "Run agents strictly sequentially" |
| Error handling that re-raises | "Catch and log; never re-raise from the orchestrator" |
| Stage errors hidden | "Print one line per stage with timing and OK/FAIL" |

---

## Time budget

- AI generation: 5 min
- Acceptance run + fix iterations: 15-20 min
- Multi-run stability check: 5 min
- Stage failure rehearsal: 10 min
- Commit + brief note in `docs/DECISIONS.md`: 5 min

Total: ~45 min. If you're past 60 min, **stop adding features**. A working orchestrator that handles the happy path + one failure mode is enough.
