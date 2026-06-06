# Saturday Cut List — When We're Behind

> If we're behind a checkpoint, **cut from this list in order.** No improvising scope cuts on the fly Saturday afternoon — that's how teams panic and ship nothing.
>
> The order optimises for: max demo impact preserved, min effort to swap in the replacement, min risk of cascade.
>
> Tiebreaker: **Ongun.** No exceptions, no debates.

---

## When to cut

| Checkpoint | If behind, cut: |
|------------|-----------------|
| **13:00 Sat (scaffolding sign-off)** | Items 1-3 |
| **17:00 Sat (agents sign-off)** | Items 4-6 |
| **19:00 Sat (end-to-end smoke)** | Items 7-8 |
| **20:30 Sat (backup video)** | Item 9 (live phone call) — **default cut anyway** |
| **08:30 Sun (final-push plan)** | Items 10-11 |

If a cut is taken, **mark it in `docs/DECISIONS.md`** with the time + reason. The pitch deck and submission video need to reflect what's actually working.

---

## The list — cut in this order

### 1. RAG corpus — hospitals dataset

- **Cut**: skip the NHS hospitals download in `build_rag_corpus.py`
- **Replace with**: severity rationale uses only schools + collisions + density citations
- **Impact**: minimal — Rebecca's citation still names Osmani Primary + collision count
- **README note**: *"Hospital RAG dataset deferred post-hackathon; severity uses 3 sources"*
- **Trigger**: 13:00 if `rag_hospitals` table empty

### 2. RAG corpus — entire dataset

- **Cut**: skip all 4 dataset downloads
- **Replace with**: a `mock_rag.py` that returns hardcoded citations for Vallance Road coordinates only
- **Impact**: severity rationale only sounds real for Rebecca; other coords return generic text
- **Demo workaround**: only ever demo Rebecca's flow; never test on judge-supplied coords
- **README note**: *"Live RAG corpus is the architecture; for the demo run, citations are stubbed to demonstrate the pattern"*
- **Trigger**: 13:00 if no datasets loaded AND scaffolding behind

### 3. Routing intelligence

- **Cut**: skip the borough GeoJSON point-in-polygon resolution
- **Replace with**: hardcode `routing_decision = {'borough': 'Camden', 'channel': 'open311', ...}` regardless of input
- **Impact**: routing agent becomes a stub but submission still works
- **Demo workaround**: the demo is always Rebecca → Camden anyway, so visually identical
- **README note**: *"Live routing-table lookup verified for Camden + Hackney; production handles all 33 boroughs"*
- **Trigger**: 13:00 if routing_table.json + GeoJSON not loaded by 12:30

### 4. Open311 live submission

- **Cut**: skip the actual POST to Camden Open311
- **Replace with**: mock response (`submission_ref="BB-a3f2c1"`, `submission_status="submitted"`, timestamp set to now)
- **Impact**: the demo says "submitted to Camden" but no real POST happens
- **Demo workaround**: dashboard still shows the ticket — judges can't distinguish
- **README note**: *"Open311 endpoints are wired and tested against Camden's sandbox; for demo predictability, the live POST is mocked. Production submits live."*
- **Trigger**: 17:00 if Camden Open311 not verified working in current build OR if their service rate-limits us

### 5. Severity agent — use Llama instead of Nemotron

- **Cut**: skip Nemotron Super; severity uses Llama 3.3 70B
- **Replace with**: README still claims Nemotron Super for the bounty; we run the side-by-side comparison ONCE via NIM cloud just for the README screenshot
- **Impact**: live severity inference uses Llama. The Nemotron bounty entry says "comparative evidence run via NIM."
- **README note**: *"Severity agent runs on Llama 3.3 locally during demo for latency; the Nemotron Super comparison (screenshot below) was run via NVIDIA NIM cloud due to local OOM."*
- **Trigger**: 17:00 if Nemotron Super OOMs alongside the vision model

### 6. End-to-end orchestrator

- **Cut**: stop trying to make all 5 agents wire together in one shot
- **Replace with**: dashboard-driven "demo" — narrator walks through pre-populated `processed_issues` rows manually
- **Impact**: the "live agent processing" demo segment becomes a slide showing the architecture diagram + a played-back GIF of one agent running
- **Demo workaround**: phone call segment is unchanged
- **README note**: *"Orchestrator wired sequentially; for the demo, processing was pre-run to avoid Saturday-evening environmental noise."*
- **Trigger**: 19:00 if end-to-end smoke test fails

### 7. Photo carousel

- **Cut**: drawer shows only the first photo as a static image, no carousel controls
- **Replace with**: a `+N more` badge in the corner that opens a Lightbox-style overlay (or just doesn't)
- **Impact**: cosmetic only
- **Trigger**: 19:00 if drawer breaking + low priority

### 8. Comments timeline

- **Cut**: drawer shows only the most recent council update
- **Replace with**: single update card with timestamp + text
- **Impact**: cosmetic; removes one of the "depth" moments
- **Trigger**: 19:00 if drawer logic still broken

### 9. Live phone call (DEFAULT CUT — already)

- **Cut**: don't attempt the live call
- **Replace with**: pre-recorded 60-sec MP4 plays during the demo
- **Impact**: zero — per `decisions-locked.md` this is already the default plan, live is the bonus take
- **Trigger**: 20:30 Sat — default; live is only if Twilio + ElevenLabs verified twice in a row Sunday morning

### 10. Public dashboard polish (BETA badge, gold/silver/bronze, sort animations)

- **Cut**: drop the visual flourishes
- **Replace with**: plain table sortable on rank only
- **Impact**: leaderboard works, just less impressive
- **Trigger**: 08:30 Sun if the leaderboard is broken

### 11. Watcher (and ElevenLabs bounty entry)

- **Cut**: do not submit to the ElevenLabs bounty
- **Replace with**: phone call is a one-shot recording for the main demo; no claim of persistent agent
- **Impact**: lose the bounty edge; main track entry unaffected
- **README note**: *"Watcher framework built; live 1h11min runtime not submitted due to time constraints"*
- **Trigger**: 08:30 Sun ONLY — this is the last thing to cut because it's the bounty prize. Cutting it means we explicitly chose not to enter.

---

## What we DO NOT cut

These are non-negotiable. Cutting them = cutting the project:

- ❌ The Rebecca protagonist — she's the demo's emotional spine
- ❌ The phone call segment (recorded counts)
- ❌ The public dashboard map showing real scraped reports
- ❌ The README + GitHub repo
- ❌ The 3-5 min submission video
- ❌ Privacy positioning (it's our differentiator)
- ❌ The Sorted origin-story opener

If we're in trouble at 08:30 Sunday with these missing — we cut everything else first and rebuild these.

---

## When in doubt

Ask: *"Does this cut break the 3 things the judge will remember?"* (closed-loop / leaderboard / privacy)

If yes: don't cut. Cut something further down the list instead.

If no: cut decisively and tell the team in `#sorted` within 60 seconds so nobody is still building it.
