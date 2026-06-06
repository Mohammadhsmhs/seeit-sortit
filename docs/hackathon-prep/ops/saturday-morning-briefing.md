# Saturday 9 AM Briefing — 15-minute Sorted huddle

> Last alignment before hacking starts at 9:30 AM. Timebox is real — stop the meeting at 9:15. Everyone leaves with one clear job and nothing to re-litigate until 1 PM standup.
>
> **Owner**: Ongun runs it. Whiteboard up. Everyone standing. No laptops.

---

## 09:00 – 09:02 · Roles confirmed (2 min)

State out loud — no debate, just confirm:

| Person | Lane | Today's deliverable |
|--------|------|---------------------|
| **Ongun** | Agent pipeline + orchestrator + demo lead | All 5 agents wired and end-to-end working by 5 PM |
| **Teammate 1** (Goldman) | Data + UI canvas | Scraper running by 11 AM, dashboard with map by 5 PM, ticket drawer by 8 PM |
| **Teammate 2** (TBD) | Assigned at 9:00 sharp based on skills | See section 2 below |

**Teammate 2 assignment decision (60 seconds at the start of this huddle):**
- If they're a designer / frontend → **demo recording + pitch deck + intake UI polish**
- If they're backend → **escalation agent (phone) + Twilio/ElevenLabs wiring**
- If they're a PM / generalist → **demo data, council-side dashboard, judge Q&A prep, submission package**

→ Decision: `____________________________` (write it on the whiteboard)

---

## 09:02 – 09:04 · Pipeline at a glance (2 min)

Pull up `docs/architecture.svg`. Walk the 5 agents in 20 seconds each:

1. **Intake** — photo + voice → classified, GPS, structured. (Ongun)
2. **Severity** — RAG over London open data → cited score. (Ongun)
3. **Routing** — borough + category → council + channel. (Ongun)
4. **Submission** — Open311 POST to council CRM. (Ongun)
5. **Escalation** — SLA breached → ElevenLabs phone call → drafted letters. (Ongun or Teammate 2 depending on assignment)

Teammate 1 owns the canvas (scraper + dashboard) — without it nothing is visible.

**One thing everyone must remember:** the canvas (dashboard) and the pipeline write to the same SQLite DB. The pipeline puts processed issues *in*, the dashboard reads them *out*. That's the integration point.

---

## 09:04 – 09:06 · Demo target (2 min)

**Protagonist:** Rebecca, Tower Hamlets, dumped mattresses on Vallance Road.

**The 5 demo beats** (we shoot for all five, fall back gracefully if any breaks):

1. **0:00–0:20** Rebecca opens the app, snaps photo, says one sentence. *"There's a pile of dumped rubbish outside my daughter's school."*
2. **0:20–0:50** Agent classifies, cites severity (collisions, school proximity), routes to Tower Hamlets Waste, submits via Open311.
3. **0:50–1:15** Time jump card: "14 days later, no response."
4. **1:15–2:30** **Phone call plays.** Agent calls Camden's switchboard (or pre-recorded). References the ticket. Polite, identifies as automated. *This is the moment.*
5. **2:30–3:00** Cut to public leaderboard. "Camden #13 of 33. The pressure works."

**Pre-recorded phone-call fallback must exist by 18:00 Saturday.** That's a hard checkpoint, not a stretch goal.

---

## 09:06 – 09:09 · Decisions LOCKED (3 min)

Read these out. Nobody re-opens any of these today. If anyone wants to change one, they wait until tomorrow's submission package conversation.

| Decision | Locked answer |
|----------|---------------|
| Reasoning model | Llama 3.3 70B (fits Spark Q4) — swap to Nemotron Super if it loads and we have time |
| Vision model | Qwen2.5-VL-7B |
| STT | ElevenLabs Scribe |
| Voice agent | ElevenLabs Conversational AI |
| Telephony | Twilio (UK number) |
| Web framework | Flask + vanilla JS + Leaflet + Chart.js |
| Data store | SQLite, single file |
| Submission channel | Open311 (Camden verified live, Hackney pattern) |
| Demo protagonist | Rebecca, Tower Hamlets |
| Demo borough for submission | Camden (Open311 works) — story still references Tower Hamlets |
| Sponsor bounties chasing | ElevenLabs (1h 11min agent), Nemotron (best use), Public Services track |

**Out of scope today (cut without discussion):**
- Native iOS app
- Council-side prioritisation dashboard (only as a slide in the pitch)
- Love Clean Streets scraping
- Multilingual UI (Scribe handles input; pitch claims it but UI stays English)
- Real LGO / MP letter sending (drafts only)

---

## 09:09 – 09:13 · Time budget (4 min)

Real building hours: **~14.5 total** (Sat 9:30-21:00 = 11.5h + Sun 8:00-11:00 = 3h).

| Block | Hours | Goal | Exit criterion at the end |
|-------|-------|------|----------------------------|
| **Sat 09:30–13:00** | 3.5h | Scaffolding | Scraper running, DGX models pulled, repo public, 5 agent files stubbed, dashboard skeleton serving the map |
| **Sat 13:00–17:00** | 4.0h | Each agent works alone with mock data | Each agent has 1 input/output cycle running. Submission agent can POST to a fake endpoint and Camden Open311 sandbox. Dashboard shows real scraped reports. |
| **Sat 17:00–21:00** | 4.0h | Integration | Orchestrator wires all 5 agents. End-to-end smoke test runs at 19:00. Demo backup recording shot at 20:30. |
| **Sun 08:00–10:00** | 2.0h | Submission package | Demo video recorded, README polished, GitHub public, project description written, video uploaded to durable URL |
| **Sun 10:00–11:00** | 1.0h | **SUBMIT** | 10:45 cut-off for code changes, 11:00 submission must be done. 15-min buffer is for inevitable issues. |

**Checkpoints (set phone alarms):**
- 13:00 — scaffolding sign-off
- 17:00 — agents sign-off
- 19:00 — end-to-end smoke
- 20:30 — backup video recording
- 21:00 — kicked out of building
- 08:00 Sun — back in
- 10:45 Sun — pencils down

---

## 09:13 – 09:15 · Comms, cut decisions, kick-off (2 min)

**Comms:**
- Discord: `#sorted` for everything
- Decision log: append to `docs/DECISIONS.md` (one line: date + decision + who decided)
- If you're blocked > 15 min, post in #sorted immediately. Don't burn through it alone.

**Cut decisions at each checkpoint:**
- 13:00 not done with scaffolding → cut RAG corpus (use 3 hardcoded data points instead of real datasets)
- 17:00 agents not working → cut routing intelligence (hardcode "Camden → highways")
- 19:00 no end-to-end → record dashboard-only demo, agent demo becomes slides
- 20:30 phone call still broken → recorded fallback is the demo, no live attempt

**Tiebreaker:** Ongun. If we deadlock, he calls it and we move.

**Now go.** Hacking starts in 15 minutes. Get your laptops, water, snacks. Be at your desk at 9:25.

---

## After the meeting

- Whiteboard the locked decisions on the wall — visible to all.
- Whoever is most awake takes a photo of the whiteboard, drops in `#sorted`.
- Ongun starts a 25-min Pomodoro at 09:30 sharp.
