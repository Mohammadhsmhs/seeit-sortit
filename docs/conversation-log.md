# Conversation Log

## 2026-06-01 — Session 1: Project Kickoff + Feasibility

### Context
Ongun shared the full project brief for London Civic Agent — a multi-agent civic complaint system for NVIDIA Hack for Impact London (5–7 June 2026). Directory was empty; no code yet.

### Key Decisions
1. **Assessed feasibility across hardware, APIs, data, and time.** Verdict: feasible at reduced scope (5 agents, not 8–10).
2. **Nemotron Ultra is out** — doesn't fit on a single DGX Spark. Options: Llama 3.3 70B (primary) or Nemotron Super 120B-A12B (NVIDIA-branded, MoE).
3. **FixMyStreet is NOT a government service** — it's by mySociety (charity). We are a competing platform, not an integration partner.
4. **FixMyStreet reports are public** — photos and content visible on their site. Conflicts with privacy pitch if we upload to them.
5. **Scraping FixMyStreet is a strategic asset** — public reports can serve as training data, severity signal, and evidence for escalation letters.
6. **Footfall data is restricted** — need a proxy (TfL station entry/exit counts).
7. **City of London open data portal doesn't exist** at the URL listed in the brief — use London Datastore instead.

### Open Items
- Team still unconfirmed (need 3–5)
- Model choice for reasoning layer not finalised (Llama 3.3 70B vs Nemotron Super)
- FixMyStreet scraper scoped as a task but not started
- Public dashboard + council leaderboard scoped as a task but not started

### Feature Addition: Public Dashboard + Council Leaderboard
Added a public-facing dashboard that tracks issue resolutions across London boroughs, with a leaderboard ranking councils by performance. Fed by FixMyStreet scraped data + the platform's own submissions. Creates public accountability pressure — councils that ignore issues are visibly ranked lower. Strong demo visual and differentiator from FixMyStreet.

### UX Complexity Analysis (added 2026-06-02)
Researched the full step-by-step reporting flows for FixMyStreet, Islington Council, and Camden Council. Key findings:
- No London council has "report a problem" on their homepage
- 8-10 clicks minimum to report a single issue
- 67-146 category options to navigate
- Reporting a pothole AND fly-tipping on the same street requires 2 different platforms and up to 2 accounts
- Users must know which department handles their issue (Roads vs Recycling vs Environmental)
- Created before-vs-after comparison diagram and detailed flow documentation in docs/ux-complexity/

### Scope Recommendation
Cut to P0 (intake + severity ranking + routing + submission) + phone escalation for demo wow-factor. Drop multilingual, NeMo Guardrails, and LGO/MP escalation unless ahead of schedule by Saturday morning.
