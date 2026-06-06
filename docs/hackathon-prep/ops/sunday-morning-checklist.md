# Sunday Morning Checklist — 07:00 → 08:30

> Wake up. Get to the venue. Make sure nothing died overnight. This document covers **07:00 → 08:30**. After 08:30, follow `ops/submission-checklist.md`.
>
> Goal: by 08:30 we know whether the demo from last night still works. If yes, we move to recording + submission. If no, we triage in the first 30 minutes.

---

## 07:00 — At home

- [ ] Alarm goes off. Don't snooze. The whole day depends on whether the watcher survived overnight.
- [ ] Phone fully charged + cable in bag
- [ ] USB drive with `demo_data/` in your bag
- [ ] One bottle of water, one piece of fruit, breakfast on the way
- [ ] **Check `#sorted` Discord on your phone**. If the watcher died overnight, someone may have flagged it. Read before you arrive.

---

## 07:45 — At the venue door

- [ ] Building opens 08:00 — wait if you arrive early. Don't lobby for early entry.
- [ ] Skim the Notion: any code-freeze rule updates or schedule changes overnight?
- [ ] Last sip of coffee before the door opens. You're going to need both hands soon.

---

## 08:00 — Inside, at the desk

The order matters.

### 08:00 — Watcher health check (2 min)

```bash
# Is the watcher still running on the Spark?
ps aux | grep watcher

# How long has it been running?
sqlite3 scraper/fixmystreet.db \
  "SELECT MIN(ts), MAX(ts), COUNT(*) FROM watcher_session_log;"
```

**Expected:** `(start_ts, recent_ts, 1000+)`. The session has been alive >12 hours and accumulating events. **This is the ElevenLabs bounty proof.**

- ✅ If still running → leave it alone. Don't touch.
- ❌ If dead → restart immediately with `--resume`. Note in `docs/DECISIONS.md` the gap window. The session_id stays the same. The ElevenLabs bounty entry's duration is `now - first_ts`, NOT `now - restart`.

### 08:02 — DGX Spark health (3 min)

```bash
nvidia-smi
ollama list
```

- ✅ If models are loaded and Spark is responsive — continue.
- ❌ If models unloaded (Spark restarted overnight) — `ollama pull` the three again. Costs 5-10 min. Adjust the morning timeline accordingly.

### 08:05 — Smoke test: end-to-end run on Rebecca (5 min)

```bash
python -c "
from src.agents.orchestrator import Orchestrator
from src.models.llm import get_default_provider
orch = Orchestrator(get_default_provider())
issue = orch.process(
    photo_path='demo_data/rebecca_photo.jpg',
    voice_path='demo_data/rebecca_voice.m4a',
)
print(issue.category, issue.severity_score, issue.borough, issue.submission_status)
"
```

- ✅ Returns the right values → all four agents still wired correctly.
- ❌ Any agent broken → triage now. Use the cut-list (`risks/saturday-cut-list.md`) if not fixable in 15 minutes.

### 08:10 — Live phone test (5 min — the decision moment)

Per `decisions-locked.md`: live call only if it works twice in a row Sunday morning.

```bash
python trigger_call.py  # to your own number
# Hang up after agent's first sentence; that's enough
python trigger_call.py  # again
```

- ✅ Both succeed → live call is plan A for the demo
- ❌ Either fails → recorded fallback is the plan. **Lock it.** Log in `docs/DECISIONS.md`. Don't second-guess after this point.

### 08:15 — Dashboard sanity (5 min)

Visit `http://localhost:5050` in fresh incognito.

- [ ] Map renders with markers
- [ ] Leaderboard shows real boroughs
- [ ] Click a marker → drawer opens cleanly
- [ ] Borough page works

Note any visual regressions but **don't fix anything that judges won't see** in the 3-min demo.

---

## 08:20 — 5-minute team standup

Each person one sentence:

- *"My component is [state]. What I'm doing next is [Y]. I will be done by [time]."*

Lock who is doing what for the next 2.5 hours:

| Person | 08:30 – 10:00 | 10:00 – 10:45 |
|--------|---------------|---------------|
| Ongun | Record submission video w/ Teammate 2 | Submission portal + final smoke test |
| Teammate 1 | Polish dashboard + screenshots refresh + README setup steps | Be the "second pair of eyes" on the submission |
| Teammate 2 | Edit submission video, upload to YouTube, README pitch section | Q&A prep, judging-criteria run-through |

---

## 08:25 — Final pre-recording warm-up

Before recording the 3-5 min submission video at 09:00, get these things ready:

- [ ] Demo laptop charged + plugged in
- [ ] Cover slide open in tab 1
- [ ] Intake page open in tab 2
- [ ] Dashboard open in tab 3
- [ ] Backup recording open in tab 4 (in case we cut to it during the SUBMISSION video too)
- [ ] Phone in airplane mode on the desk (kills accidental ringers)
- [ ] Notifications muted (Slack, Discord, Mail)
- [ ] System volume at exactly 50% (consistent audio level)

---

## 08:30 — Hand off to `submission-checklist.md`

If the smoke tests pass and we have a plan, we're now on `ops/submission-checklist.md` which covers 08:30 → 11:00.

Move there now. **Do not keep iterating on the morning checklist.**

---

## Polish list (during 08:30 – 10:00, if there's time)

Only after the must-haves above. Each line is a "yes/no/cut" decision:

- README pitch line cleanup
- Borough page hero image
- Dashboard scorecard tooltip text
- Drawer animation timing
- Leaderboard top-3 colour palette
- Mobile view of intake page
- Onboarding deck final read-through (we won't use this in the demo, but it's pretty)

**No polish takes more than 10 minutes.** Anything that does, cut.

---

## What dies in this window kills the demo

These three failures during 07:00–08:30 mean we lose hours:

1. **Watcher died overnight + we don't notice until 11:00** — bounty entry's continuity claim breaks publicly. Check at 08:00, not 10:00.
2. **DGX Spark restarted, models unloaded, we don't catch it** — at 11:30 the demo's severity agent has 15s cold-start lag. Check `ollama list` at 08:02.
3. **Live call broken but we record video assuming it works** — submission video shows a broken demo. Test the call before recording the video.

The 30-minute checks here prevent all three.

---

## The one thing to remember

**08:00–08:30 is the most leveraged 30 minutes of the weekend.** Find a problem now, you have 2.5 hours to fix it. Find it at 10:45, you ship broken.

Move with intent. Stay calm.
