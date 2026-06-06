# Saturday Evening Review — 20:00 → 21:00

> The building closes at 21:00. This is the last hour we have together before sleep + the Sunday-morning push. **Everything we record / mirror / commit tonight is one less thing we hope works tomorrow.**
>
> Owner: **Ongun** runs the meeting. 60 min, sharp.

---

## What we expect to be true at 20:00

If the checkpoints have been hit:

| Component | State at 20:00 |
|-----------|----------------|
| Scraper | Done. ~6,000 reports in `scraper/fixmystreet.db`. |
| RAG corpus | Done. 4 tables loaded. Osmani Primary findable. |
| Dashboard | Map + leaderboard + drawer working. |
| Intake (Rebecca's photo + voice → CivicIssue) | Works on Rebecca's demo inputs. |
| Severity (Nemotron) | Returns cited score on Rebecca. |
| Routing | Returns "Tower Hamlets" for Rebecca's coords. |
| Submission | Mocked or live POST to Camden Open311 works. |
| Watcher | Running for ~5h, session log has 50+ events. |
| Phone call (live) | Tested twice, succeeded both times. **OR** decision already locked to recorded-only. |

If 7+ are green, we're on track. If <5 are green, we cut and record. The cut-list (`risks/saturday-cut-list.md`) is the order.

---

## The 60-minute agenda

### 20:00 – 20:05 · State of the union (5 min)

Each person, one sentence:
- *"My component is at [state]. Risk is [X]. By 21:00 I will [Y]."*

Ongun marks each on the table in the meeting room — green / amber / red.

Reds get triaged in the next 10 minutes.

### 20:05 – 20:15 · Triage reds (10 min)

For each red:
- Cut to the next item in `saturday-cut-list.md` (e.g. severity broken → use Llama + screenshot Nemotron)
- Or extend to Sunday morning if it's safe to defer
- **No solo heroics.** Two people on each red.

### 20:15 – 20:30 · End-to-end dry run (15 min)

**The most important 15 minutes of the day.**

Sit at the demo laptop. Run the full 3-minute demo with the recorded fallback ready. Time it.

Things to confirm:
- [ ] Cover slide opens in <2 sec
- [ ] Intake form accepts Rebecca's photo + voice
- [ ] Processing completes in <15 sec OR pre-cached state is visible
- [ ] Severity shows cited rationale on screen
- [ ] Routing + submission display
- [ ] Time-jump card transitions cleanly
- [ ] Live call rings (or recorded plays at full volume)
- [ ] Leaderboard close hits the right beat at 2:30-2:45
- [ ] Total demo length is **3:00 to 3:30**

If the dry run is over 3:30 — trim narration, not features. The phone call segment can be 60 sec, not 75.

### 20:30 – 20:45 · Record the backup video (15 min) — HARD CHECKPOINT

This is non-negotiable per `demo-data-package.md`. By 20:45 a working 60-sec recorded phone call MP4 must exist.

- **Recorder**: Teammate 2 (or whoever has best mic)
- **Tools**: QuickTime screen recording + iPhone Voice Memos for the call audio
- **Script**: same as the live demo phone segment from `demo-script-3min.md`
- **Storage**:
  1. `demo_data/recorded_call.mp4` in the repo
  2. USB stick
  3. Teammate 1's laptop
  4. YouTube unlisted upload (optional, before 21:00)

**If you only do one thing in this hour, do this.** Everything else can recover. A missing backup video can't.

### 20:45 – 20:55 · Capture demo screenshots (10 min)

Open the dashboard. Take screenshots of every panel:

- [ ] Full-page map view with Rebecca's marker visible
- [ ] Leaderboard with Greenwich #1, Camden mid-pack
- [ ] Borough page for Camden
- [ ] Ticket drawer open on Rebecca's report
- [ ] Watcher session log timeline
- [ ] Severity drawer with the Nemotron-cited rationale on screen

Save them to `demo_data/dashboard_screenshots/`. Mirror to USB + second laptop.

These are the **slides we walk through when the dashboard breaks live** (per Failure 5 in `risks/fallback-plan.md`).

### 20:55 – 21:00 · Mirror everything to two laptops + USB

- [ ] `git push` everything you've touched
- [ ] On Teammate 1's laptop: `git pull` and verify the demo still runs there
- [ ] Copy `demo_data/` to USB drive
- [ ] Confirm USB drive boots / mounts on at least two laptops
- [ ] Phone numbers, .env, API keys: noted somewhere durable (1Password / Notion / printed)

---

## What we record TONIGHT vs leave for Sunday morning

| Recorded tonight | Sunday morning |
|------------------|----------------|
| Backup phone call MP4 | The 3-5 min submission video |
| Dashboard screenshots | README polish |
| End-to-end demo dry run | Final pitch deck polish |
| `watcher_session.json` snapshot | Final smoke test from a fresh clone |

**Why the submission video is Sunday, not tonight:** the watcher needs to have run continuously for the ElevenLabs bounty's 1h 11min — and by Sunday morning that's been running 18 hours. Sunday's session log is much richer than tonight's, so Sunday's video tells a stronger story. Per `bounties/elevenlabs-prize-strategy.md`.

---

## Cut decision points at this review

If at 20:00 we are CLEARLY behind, we cut now. Don't wait for tomorrow morning's adrenaline.

Triggers for evening cuts:
- **Severity isn't returning anything reasonable** → swap to Llama 3.3, write the README NIM-comparison line, move on (Cut #5)
- **Watcher session log empty** → seed it tonight with hardcoded synthetic events (Cut #11 saves the bounty)
- **Submission agent not posting** → mock it, README discloses (Cut #4)

**Document every cut in `docs/DECISIONS.md` before leaving the building.** Tomorrow's you will not remember.

---

## Pre-departure protocol (21:00 sharp)

- [ ] All laptops + USBs accounted for
- [ ] Ongun has the demo USB drive in his backpack
- [ ] Teammate 1 has the mirror USB
- [ ] Models still loading on the Spark overnight? Leave them. (We'll know in the morning.)
- [ ] Watcher process kept running? **YES — it earns hours toward 1h 11min**
- [ ] Phones charged for tomorrow morning's Twilio test
- [ ] Set alarm for 07:00 Sunday
- [ ] Eat. Walk home. Sleep 7+ hours.

---

## Anti-patterns during this review

- ❌ "Let me just fix one more thing." 21:00 is hard. Leave.
- ❌ Saying "I think it works" without running it. Demo it now.
- ❌ Promising tomorrow-morning fixes for things that need 90 minutes. Cut them tonight.
- ❌ Not recording the backup MP4 because "the live call works fine." It won't tomorrow under stress. Record it.

---

## The closing line

Ongun, before everyone packs up:

> *"We have a demo. We have a backup. We have a plan. Tomorrow we polish, record the submission video, and ship by 11. Sleep is the last feature."*

Then go home.
