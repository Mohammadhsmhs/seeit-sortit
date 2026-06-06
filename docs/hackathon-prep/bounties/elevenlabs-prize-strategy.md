# ElevenLabs Prize — Strategy

> Win condition: an autonomous agent runs persistently for **≥1 hour 11 minutes** during the event. Stack: **Nemotron + ElevenLabs voice (in/out)**. Judges test live by asking the agent about things that happened earlier in its session.
>
> Our angle: the **escalation agent** is already designed to be persistent. We just have to make it visibly so.

---

## The bounty (read it literally)

From the official slide:
1. **Teams should build an autonomous agent that runs persistently for at least 1 hour and 11 minutes during the event.**
2. **Stack:** NVIDIA Nemotron + ElevenLabs voice interface (in/out).
3. **Test:** Teams submit session logs. Judges test context retention live by asking the agent about specific things that happened earlier in its 1h 11-min session.

So the win is a **continuously running agent**, with **voice in/out**, that **remembers what happened earlier and can answer questions about it**.

---

## Our angle: the "Sorted Watcher"

The escalation agent we're already building IS this agent — we just frame and instrument it for the bounty.

**Frame:** the agent is the **Sorted Watcher**. It runs throughout Saturday afternoon and Sunday morning. It monitors the live CRM. When a citizen submits a report, the Watcher observes it. When an SLA breaches, the Watcher places a phone call. When a call is logged, the Watcher remembers what was said. By demo time, it has lived through dozens of events.

The judges walk up. They put a headset on. They talk to it. It answers using ElevenLabs voice. They ask, *"What was the most recent fly-tipping report?"* It answers from memory. *"Did you call Camden today?"* It answers from memory. *"What did the Tower Hamlets resident say in their voice note?"* It answers from memory.

That is the prize-winning moment.

---

## Architecture (how it stays alive)

```
   ┌──────────────────────────────────────────────────┐
   │      Sorted Watcher Process (always-on)           │
   │                                                  │
   │  Event sources:                                  │
   │   • SQLite reports table (poll every 30s)        │
   │   • Pre-seeded synthetic events (cron-like)      │
   │   • Live submissions from demo flow              │
   │                                                  │
   │  Each event → appended to session_log table      │
   │   + summarised into agent's working memory       │
   │                                                  │
   │  Voice interface:                                │
   │   • ElevenLabs Conv AI WebSocket — agent_id      │
   │   • Custom system prompt referencing memory      │
   │   • Tool: query_memory(text) → returns events    │
   │                                                  │
   │  Brain: Nemotron Super (Q4) on the Spark         │
   │   Context: full session log up to 100K tokens    │
   │   Beyond that: rolling summary + vector recall   │
   └──────────────────────────────────────────────────┘
```

**The agent never sleeps.** It runs as `src/agents/watcher.py` from ~9 AM Saturday onward. By demo time on Sunday it has logged 24+ hours of events — far more than the 1h 11min minimum.

---

## Memory strategy (the only hard problem)

Three layers, in priority of effort:

1. **Full session log in SQLite** (`watcher_session_log` table — timestamp, event_type, payload_json, agent_response). This is what we submit to judges. It's the ground truth.
2. **Append to context** — every new event becomes a line appended to the agent's system prompt: `[14:32] new_report id=1234 borough=Camden category=Pothole severity=8`. Up to Nemotron's context limit.
3. **Tool-based recall (if time)** — if context overflows, expose a `query_memory(question)` tool that does keyword search over the session_log table and returns matches. The agent can call it during conversation.

**Quality bar:** the agent should reliably answer *"what happened at HH:MM?"* and *"how many calls have you placed today?"* If it can do those two, we win. Anything fancier is bonus.

---

## Pre-seeded events (so the log is always rich)

We can't rely on real users to seed enough events for context-retention testing. So we pre-seed:

- A small `seed_events.py` script fires synthetic events into the watcher every 90 seconds, starting Saturday afternoon.
- Events vary: new report submissions, status changes, SLA breach alerts, phone-call outcomes, Rebecca's report (lands at a known time so the demo can reference it).
- Pre-seeded events are tagged `synthetic=true` in the session log so we're transparent in the README.

By demo time, the log has 200-500 entries.

---

## Voice interface (ElevenLabs Conv AI)

**Option A (preferred):** ElevenLabs Conversational AI agent — they host the agent, we configure it with our system prompt and tools. WebSocket connection from our laptop drives the headset interaction.

**Option B (fallback):** Build our own loop: WebRTC mic → ElevenLabs Scribe STT → Nemotron (on Spark) → ElevenLabs TTS → speaker. More work, more brittle, more in our control.

Decision at 14:00 Saturday based on whether Option A's tool integration supports our `query_memory` function calls.

---

## Session log — the format we submit

```json
{
  "agent_name": "Sorted Watcher",
  "session_start": "2026-06-06T13:00:00Z",
  "session_end": "2026-06-07T11:00:00Z",
  "duration_minutes": 1320,
  "stack": ["nemotron-super-120b", "elevenlabs-conv-ai"],
  "events": [
    {"ts": "2026-06-06T13:00:01Z", "type": "watcher_start", "note": "Polling reports table every 30s"},
    {"ts": "2026-06-06T13:01:32Z", "type": "new_report", "report_id": 4078347, "borough": "Lewisham", "category": "Fly-tipping", "severity": 9, "synthetic": false},
    {"ts": "2026-06-06T13:05:00Z", "type": "sla_breach_alert", "report_id": 4011, "days_open": 30, "decision": "place_call"},
    {"ts": "2026-06-06T13:06:12Z", "type": "outbound_call", "to": "+44 20 7974 4444", "council": "Camden", "duration_s": 87, "outcome": "scheduled_collection_tuesday"},
    ...
  ],
  "voice_interactions": [
    {"ts": "2026-06-07T10:30:00Z", "who": "judge", "asr": "what was the most recent fly-tipping report?"},
    {"ts": "2026-06-07T10:30:03Z", "who": "agent", "answer": "The most recent fly-tipping report is 4078347, filed in Lewisham at 13:01 yesterday."},
    ...
  ]
}
```

The README links to this file. Judges open it before the live test.

---

## Anticipated judge questions (rehearse these)

1. *"How many phone calls have you placed today?"* → exact count from log
2. *"What was the most recent SLA breach you handled?"* → most recent breach event
3. *"Tell me about Rebecca's report."* → Rebecca's seed event by name
4. *"What's the severity score of the Camden pothole report at 2 PM?"* → look up by timestamp
5. *"Did anyone get back to you from Tower Hamlets today?"* → call outcomes log
6. *"What were you doing at 14:30 yesterday?"* → event window from log
7. *"How long have you been running?"* → `now - session_start`

Pre-test the agent on all seven on Saturday evening.

---

## Risk: what if the agent crashes mid-test?

- **Always restart from log.** The session_log is the source of truth. On restart, the agent reloads its context from the log file.
- **Log heartbeat every 60s.** A `watcher_heartbeat` event proves continuity even if no civic events happened.
- **Recovery script** — `python watcher.py --resume <session_id>` rebuilds context from log and reconnects to ElevenLabs.

---

## What goes in the README (make the win obvious)

In the README, add a section titled **"Sorted Watcher — ElevenLabs Bounty Submission"**:

- Stack: Nemotron Super + ElevenLabs Conv AI (in/out)
- Continuous runtime: from `<start>` to `<end>` (> 1h 11min by demo time)
- Session log: link to `watcher_session.json`
- How to test: open the headset, ask any question from the suggested list
- Why this matters for our project: the escalation agent is the one that closes the civic-complaint loop. Persistent memory is what makes it credible.

Drop a screenshot of the session log running in the README too.

---

## What ONLY this strategy needs (added to the build plan)

- `src/agents/watcher.py` — the always-on process
- `src/data/seed_events.py` — synthetic event firer
- `src/integrations/elevenlabs_convai.py` — agent configuration + WebSocket
- `watcher_session.json` — submission artifact

These are owned by **Teammate 2 if backend, else Ongun**. Cut order: voice interface (Option A → recorded fallback), pre-seeded events, then the watcher itself. **The watcher must exist** — we either ship this or we don't enter the bounty.
