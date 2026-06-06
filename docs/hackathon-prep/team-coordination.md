# Team Coordination — Sorted

> How we work together over 14.5 hours. Read once, follow without thinking.

---

## Ownership map

Every part of the project has exactly **one** owner. If two people are "co-owning" something, neither is.

| Component | Owner | Reviewer | Backup if owner stuck |
|-----------|-------|----------|----------------------|
| Repo, README, branches, secrets | Ongun | Teammate 1 | — |
| DGX Spark, model loading, NIM | Ongun | — | Pre-load Friday evening |
| Intake agent (vision + STT) | Ongun | Teammate 2 | Mock with fixed output |
| Severity agent (RAG + scoring) | Ongun | — | Hardcoded score |
| Routing agent | Ongun | — | Hardcoded "Camden → highways" |
| Submission agent (Open311) | Ongun | — | Skip live POST, log only |
| Escalation agent (phone) | Teammate 2 (if backend) **or** Ongun | Ongun | Pre-recorded call |
| Orchestrator wiring all agents | Ongun | — | — |
| Scraper + SQLite schema | Teammate 1 | Ongun | Smaller borough sample |
| Public dashboard (map + leaderboard) | Teammate 1 | Teammate 2 | Static demo HTML |
| Ticket drawer modal | Teammate 1 | — | Simplified popup |
| Intake UI (consumer-facing) | Teammate 2 (if frontend) **or** Teammate 1 | Ongun | Skip entirely, dashboard is enough |
| RAG corpus download | Teammate 1 | Ongun | 3 hardcoded examples |
| Demo video (3-5 min submission) | Teammate 2 | Ongun | Screen-record dashboard only |
| Pitch deck (live judging) | Teammate 2 | Ongun | Use the onboarding deck as fallback |
| Judge Q&A prep | Teammate 2 | Ongun | Wing it |
| Pre-recorded phone call backup | Teammate 2 | Ongun | **MUST exist by 20:30 Saturday** |
| Submission package (README, video, links) | Ongun | All | — |

**Rule:** if you're not the owner, you don't change the file without telling the owner in `#sorted` first.

---

## Standups (set phone alarms)

Five non-negotiable check-ins. Each is **5 minutes max**, standing, no laptops.

| Time | Day | Focus | Output |
|------|-----|-------|--------|
| **09:00** | Sat | Kick-off briefing (the one-pager) | Locked decisions, lanes confirmed |
| **13:00** | Sat | Scaffolding sign-off | Cut decision: drop RAG corpus if not running |
| **17:00** | Sat | Agents sign-off | Cut decision: drop routing intelligence if behind |
| **20:30** | Sat | Pre-record demo backup | Recorded backup video MUST exist by now |
| **08:00** | Sun | Final-push plan | Who polishes what before 10:45 cut-off |

If you can't physically be at a standup (bathroom, food run), post the same info in `#sorted` within 5 minutes. No silent absences.

---

## Comms channels

| Channel | Use for |
|---------|---------|
| **Discord `#sorted`** | Default for everything. Status updates, blockers, decisions, snippets. |
| **Discord voice** | If something needs a 2-minute conversation. Hop in, hop out. |
| **In-person taps on shoulder** | If you can see the person. Faster than typing. |
| **GitHub commits** | Don't use commit messages for coordination — use Discord. Commits are for code history. |

**The 15-minute rule.** If you're stuck for more than 15 minutes, post in `#sorted` immediately. Format: *"Stuck: [thing]. Tried: [things tried]. Current guess: [theory]."* Someone unblocks you within 5 minutes or we pivot the approach.

---

## Git strategy

**One repo, one main branch, frequent commits.** No PRs. No feature branches. No merge conflicts at 11 AM Sunday.

```
git pull --rebase           # before you start a chunk of work
git add . && git commit -m "intake: classify mock photo end-to-end"
git push                    # every 20-30 minutes
```

**Commit message convention** (low ceremony):
- `intake: <what>` — intake agent changes
- `severity:`, `routing:`, `submission:`, `escalation:` — other agents
- `dash:` — dashboard
- `scraper:` — scraper
- `data:` — RAG corpus / SQLite
- `demo:` — demo materials
- `docs:` — README, docs
- `chore:` — env, deps, infra

**If you push broken code by accident.** Don't panic. Push a fix immediately and tell `#sorted`. Don't `git revert` — too risky under pressure.

**Two people MUST NOT edit the same file at the same time.** Check `git pull --rebase` before starting any chunk. If you see someone else has changes pending in your file, ping them first.

---

## Decision log (`docs/DECISIONS.md`)

Everything we decide that we don't want to re-litigate goes here. One line per decision. Append-only.

**Format:**

```
2026-06-07 14:23 | Ongun | Switched submission agent to mock Camden POST (live API rate-limited)
2026-06-07 13:05 | Teammate 1 | Dashboard uses 1000 sampled reports (full set too slow on Leaflet)
2026-06-06 21:00 | All | LOCKED at briefing — see saturday-morning-briefing.md for full list
```

If you make a decision that affects someone else's work, **add it to this file before continuing**. The decision is invisible until it's logged.

---

## Pair-programming policy

**Default: don't pair.** Two people = one project moving at half speed. Each owner works alone.

**Exceptions where pairing IS worth it:**
- DGX Spark first model load (Ongun + whoever is closest)
- ElevenLabs + Twilio first successful outbound call (escalation owner + Ongun)
- Recording the demo video (Teammate 2 + Ongun)
- Final submission package (Ongun + 1 other person to catch typos)

---

## Conflict resolution

**Tiebreaker:** Ongun.

**Process:**
1. Anyone can raise a disagreement in `#sorted`.
2. Each side gets ONE message stating their case (no debates).
3. Ongun decides. The decision goes in `docs/DECISIONS.md`.
4. Total elapsed time: under 5 minutes.

This is a hackathon, not a tech-lead promotion case.

---

## "Anti-patterns" we will not do

- ❌ Long Slack/Discord threads. If it's more than 3 messages, switch to voice.
- ❌ Pull requests. Commit to main.
- ❌ "Let me refactor this first." We refactor on Tuesday.
- ❌ Writing tests. We smoke-test the demo flow.
- ❌ Pretty error pages. The error is "the demo crashes" — fix the cause.
- ❌ Working past 21:00 Saturday. The building closes. Use the forced break.
- ❌ Touching the model load script after it's working. Treat it as sacred.
- ❌ Surprise commits to other people's files. Tell them first.

---

## When you finish your owned task ahead of schedule

In order:
1. Run the demo end-to-end yourself. Find the next break.
2. Polish your component's edges (loading states, error fallbacks).
3. Ask in `#sorted` who needs a pair of hands.
4. Update `docs/DECISIONS.md` if you noticed anything that needs locking in.
5. Sleep is a feature. If it's 23:00 Saturday and you're hammered, the demo is 11 AM tomorrow.
