# Submission Checklist — Sunday 08:00 → 11:00

> Owner: **Ongun**. Tiebreaker on every decision in this window.
> **11:00 AM Sunday is code freeze + submissions due.** Late submissions not accepted (per the official PDF).
> Submissions take 10-15 min through the portal — so **the real building cutoff is 10:45**.
>
> Print this. Tick boxes with a pen. Anything not ticked at 10:45 is cut.

---

## The 3-hour timeline

```
08:00 — back in the building. Coffee. Catch-up standup (5 min).
08:30 — Decision: live phone call or recorded fallback. Lock the answer.
09:00 — Record the demo video (HARD start time).
10:00 — Video uploaded somewhere durable. README finalised.
10:30 — Final smoke test on a fresh clone of the repo.
10:45 — PENCILS DOWN. Open the submission portal.
11:00 — Submission complete.
```

---

## 08:00 — Catch-up standup (5 min)

Stand. One sentence each:

- *"My component is at [state]. The risk is [thing]. By 10:00 I will [action]."*

Ongun confirms or vetoes. Move.

---

## 08:30 — Decision: live call vs recorded

- If live phone call worked perfectly twice in a row Sunday morning → keep live as plan A, recorded as instant fallback.
- Otherwise → recorded is the demo. Don't pretend.

Log the decision in `docs/DECISIONS.md`. No re-litigation.

---

## 09:00–10:00 — Record the demo video

Per the official rules: **3-5 minute video demo** is part of the submission.

| Spec | Locked |
|------|--------|
| Length | 3:30-4:30 (do not exceed 5:00 — submission rejected) |
| Resolution | 1080p min |
| Format | MP4 (H.264 + AAC) |
| Tool | QuickTime (Mac) or OBS — NOT Loom (no offline guarantee) |
| Narrator | Ongun |
| Script | Same arc as the live demo (`demo-script-3min.md`), expanded with 60-90 sec of "what we built" walk-through after the leaderboard close |

**Where to upload (in order of preference):**

1. **YouTube unlisted** — most durable, judges can stream
2. **Google Drive shared link** (anyone with link, view)
3. **GitHub release asset** as a tagged version — only if both above fail

Upload to YouTube first. Drop the link in `docs/DECISIONS.md` AND in the README before 10:00.

**Sanity check the upload:** open the link in an incognito window. If it loads and plays, it's good. If "video unavailable" — fix immediately.

---

## 09:00–10:30 — README finalisation

The README is the first thing judges read. It sells the project in 200 words then proves it works.

Use the template from `docs/hackathon-prep/ops/github-readme-template.md` (in P1 backlog — if not built yet, use these required sections):

- [ ] **One-line pitch** (from `decisions-locked.md` — "Every Londoner just got a £200/hour ombudsman…")
- [ ] **Demo video link** — clickable
- [ ] **Live dashboard link** — if dashboard is hosted (ngrok URL or Vercel deploy)
- [ ] **Sponsors line** — "NVIDIA · HP · Nebius · ElevenLabs" — in that order
- [ ] **What's in the box** — bullet list of the 5 agents + dashboard + scraper
- [ ] **Powered by NVIDIA Nemotron Super 120B-A12B** section (for the Nemotron bounty — verbatim from `bounties/nemotron-bounty-strategy.md`)
- [ ] **Sorted Watcher — ElevenLabs bounty submission** section (for the ElevenLabs bounty — verbatim from `bounties/elevenlabs-prize-strategy.md`)
- [ ] **Honest disclosures**:
  - Demo submission goes to Camden's Open311 sandbox even though Rebecca's story is Tower Hamlets
  - Seed events are tagged `synthetic=true` in the watcher session log
  - Demo `DEMO_TIME_FACTOR` compresses 14 days into 14 seconds
- [ ] **Setup instructions** — minimum: `python -m pip install -r requirements.txt && python dashboard/app.py`
- [ ] **Team** — names and roles

---

## 10:00 — Repo public + clean

- [ ] Repo set to **public** on GitHub
- [ ] `.env` is in `.gitignore` and **no secrets in commit history** (run `git log --all -p | grep -iE "key|token|password|secret" | head` — should be empty)
- [ ] `requirements.txt` works from a fresh `python -m venv`
- [ ] README renders correctly on the GitHub page
- [ ] Demo video link in the README opens in incognito
- [ ] `watcher_session.json` is committed (the ElevenLabs bounty artifact)

---

## 10:30 — Final smoke test (on a different machine if possible)

**Clone, install, run.** In a fresh terminal:

```bash
git clone <repo-url> /tmp/sorted-final
cd /tmp/sorted-final
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python dashboard/app.py &
sleep 3
curl -s http://localhost:5050/api/reports | head -c 200
```

If that returns JSON with reports — we pass.

If it crashes — debug only the install issue. **Do not add features.** Do not refactor.

---

## 10:45 — PENCILS DOWN

Stop coding. Right now. Even if mid-line.

Open the submission portal (link in the Hackathon Notion — bookmarked Friday evening). Submitter is Ongun. Have these ready:

1. **GitHub repo URL** — paste exact
2. **Project description** (~150-250 words):
   *Sorted is a London civic-complaint AI agent built at NVIDIA Hack for Impact. One photo and one voice note from a resident triggers a 5-agent pipeline — intake (Qwen2.5-VL + ElevenLabs Scribe), severity ranking (Nemotron Super on cited London open data), routing, Open311 submission to council CRMs, and a persistent escalation Watcher that places phone calls via ElevenLabs Conversational AI when council SLAs are breached. The Watcher has been running continuously since [start time] and answers judge questions about events in its session log. We also publish a fair multi-dimensional council scorecard that ranks all 33 London boroughs on responsiveness — the accountability layer none of our competitors have. Stack: NVIDIA DGX Spark (local inference), Nemotron + Llama 3.3 + Qwen2.5-VL, ElevenLabs Conv AI + Scribe + Twilio, Nebius Studio for overflow, SQLite + Flask + vanilla JS. All inference runs locally on NVIDIA hardware — citizen photos and addresses never leave the device.*
3. **Video link** — YouTube unlisted
4. **Track**: Public Services
5. **ElevenLabs bounty entry**: yes — link to `watcher_session.json`
6. **Nemotron bounty entry**: yes

Read everything before clicking submit. Have a second person eyeball.

---

## 11:00 — Submission complete

- [ ] Confirmation email received
- [ ] Screenshot the confirmation, drop in `#sorted` Discord
- [ ] Go eat. Demo fair is 11:30 — you have 30 minutes.

**Do not touch the repo after 11:00.** Even to fix a typo. The judges may be reviewing already.

---

## If something fails AFTER submission

- Demo video doesn't load → switch to Google Drive backup link, update the README via GitHub web UI (this is allowed for README-only fixes per typical hackathon rules — confirm with staff if you're unsure)
- Repo accidentally still private → make public, screenshot the time, message the staff
- Submission portal accepted but the project page is missing fields → screenshot, message staff in `#sorted` Discord

**Don't panic. Document. Ask.**

---

## After demo fair (14:00)

- Awards at 14:00. Be at the front.
- If we win — first thank: NVIDIA, HP, Nebius, ElevenLabs. In that order. Always.
- If we don't — still tweet a thank-you to all four with our demo video link. The MP outreach plan starts Monday.

---

## What this checklist guarantees

If every box is ticked by 10:45, we have:
- A working repo judges can clone and run
- A video judges can watch even if our laptops vanish
- A submission accepted before the deadline
- Both bounty entries logged
- 45 minutes of breathing room before the demo fair

If any box is unticked at 10:45 → we cut, we submit what we have, we move.
