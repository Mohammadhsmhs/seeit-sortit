# Fallback Plan — When Things Break During the Demo

> Different from `saturday-cut-list.md` (build-time scope cuts). This is the **live demo-day recovery playbook**. The demo is happening, something just broke, you have 5-10 seconds to react.
>
> Print this. Tape it to the edge of the demo laptop. Read it once before bed Saturday.
>
> **Rule #1: never apologise. Never say "uh." Pivot smoothly, narrate the pivot, keep moving.**

---

## The 10-second decision tree

```
Something breaks during the demo
   ↓
Is it visible to the judge yet?
   ├─ NO  → silently recover, keep talking
   └─ YES → say "I'll switch to our cached version" and pivot
```

Never: silence, panic, debug, blame, apologise. Always: narrate the pivot in one sentence.

---

## Failure 1 — The live phone call fails

| | |
|---|---|
| **Symptom** | Trigger button pressed, phone doesn't ring after 15 sec |
| **First action** | Cmd+Tab to the open `demo_data/recorded_call.mp4` |
| **Say** | *"The live call is our bonus take — here's the recording we made yesterday."* |
| **Then** | Play the MP4 at full volume. Same narration over the top as if it were live. |
| **Acceptance** | Recording playing within 5 seconds of the trigger button |

**Pre-arm this:** the recording is open in a hidden Chrome tab BEFORE the judge approaches. Cmd+Tab is 1 keystroke.

---

## Failure 2 — DGX Spark crashes / unreachable

| | |
|---|---|
| **Symptom** | Vision call hangs, severity call returns 500, dashboard says agent isn't responding |
| **First action** | The orchestrator already has the NIM cloud fallback — **flip `MODEL_PROVIDER=nim`** in the running process via SIGHUP / restart |
| **Say** | *"While the Spark recovers, the agent is running on NVIDIA NIM cloud — same model, same output."* |
| **Then** | Continue. The README discloses NIM as the cloud overflow per `nebius-setup.md` + `nemotron-bounty-strategy.md`. |
| **Acceptance** | Next agent call completes within 10 seconds |

**Pre-arm this:** `NVIDIA_NIM_API_KEY` exported in the demo terminal at 11:00 Sun. Test that the fallback works at 09:00 Sun.

---

## Failure 3 — Model returns garbage / wrong JSON

| | |
|---|---|
| **Symptom** | Severity JSON parse fails, category is "fly_tipping" not "Waste and Fly-Tipping", citations are empty |
| **First action** | The orchestrator already catches per-stage failures and uses the previous stage's output. Severity score falls back to a heuristic ("near a school + high density = 9") and the rationale falls back to a hardcoded one |
| **Say** | nothing — judges won't notice. The dashboard still shows a score and a rationale. |
| **Then** | The hardcoded fallback rationale is: *"This report is near a primary school and in a high-density residential area, warranting urgent attention."* Generic but defensible. |
| **Acceptance** | Pipeline emits a `processed_issues` row regardless |

**Pre-arm this:** the hardcoded fallback is in the severity agent's exception handler. Test by injecting a malformed model response Saturday evening.

---

## Failure 4 — Twilio rate-limited / outage

| | |
|---|---|
| **Symptom** | `trigger_call` returns 429 or 503 |
| **First action** | Same as Failure 1 — switch to recorded call |
| **Say** | *"We've made enough test calls today that Twilio is rate-limiting our trial account — here's the production-quality recording."* (truthful, judge-friendly) |
| **Then** | Continue with recording. |
| **Acceptance** | < 5 sec from the 429 to the recording playing |

---

## Failure 5 — Dashboard won't load / Flask crashed

| | |
|---|---|
| **Symptom** | `localhost:5050` returns connection refused |
| **First action** | In the other terminal: `python dashboard/app.py` to restart. Should take 5 sec. |
| **Meanwhile** | Open the screenshot folder `demo_data/dashboard_screenshots/` and walk through the static images on screen. |
| **Say** | *"The dashboard is restarting — let me walk you through what it shows from the screenshots while it loads."* |
| **Acceptance** | Either the live dashboard is back in 10 sec OR screenshots are visible |

**Pre-arm this:** screenshot every panel of the dashboard at 09:30 Sun and save to `demo_data/dashboard_screenshots/`.

---

## Failure 6 — Ollama OOM

| | |
|---|---|
| **Symptom** | Model call returns "out of memory" |
| **First action** | In the terminal: `ollama stop <other-model>` to unload whatever else is loaded. Retry the call. |
| **Say** | *"Time-slicing between models — the Spark has 128 GB but we're running three at once."* (true) |
| **Then** | If still OOM after unload, switch to NIM cloud (Failure 2 playbook) |
| **Acceptance** | Call completes within 30 sec |

**Pre-arm this:** know in advance which model unload to do. Most likely it's the vision model — keep reasoning hot.

---

## Failure 7 — Internet drops

| | |
|---|---|
| **Symptom** | ngrok, ElevenLabs API, NIM all fail. WiFi icon shows trouble. |
| **First action** | Switch laptop to phone hotspot. **Have this preconfigured.** |
| **Say** | *"Switching to our backup network — give me 5 seconds."* |
| **Meanwhile** | Continue the demo on local-only data — the dashboard renders from local SQLite, the recording plays from local disk. The agent pipeline can run on local Ollama with no internet. |
| **Acceptance** | Recording + dashboard work even with zero connectivity |

**Pre-arm this:** **Test the demo on aeroplane mode Saturday evening.** If anything breaks, fix it BEFORE the demo.

---

## Failure 8 — ElevenLabs Conv AI agent silent / unresponsive

| | |
|---|---|
| **Symptom** | Agent picks up but doesn't speak |
| **First action** | Hang up. Switch to recorded call. |
| **Say** | *"The agent's cloud lag spiked — here's the recording."* |
| **Acceptance** | Same as Failure 1 |

---

## Failure 9 — Demo laptop dies entirely

| | |
|---|---|
| **Symptom** | Black screen, won't boot |
| **First action** | Teammate 1's laptop becomes the demo laptop. Per `demo-data-package.md`, all 7 assets are mirrored there. |
| **Say** | *"Switching laptops — bear with me 30 seconds."* |
| **Then** | Continue demo from the second laptop |
| **Acceptance** | Second laptop is unlocked, charged, and the demo runs from it in < 60 seconds |

**Pre-arm this:** **Saturday 21:00 — fully rehearse the demo on the second laptop.** Don't trust the mirror until you've seen it work.

---

## Failure 10 — A judge asks the agent a question and the agent fails

| | |
|---|---|
| **Symptom** | Judge says "ask it what it was doing at 14:30 yesterday" — agent silent or wrong |
| **First action** | Don't pretend it worked. Show the session log on screen instead. |
| **Say** | *"The voice agent's hosted on ElevenLabs — sometimes it lags. The session log it's reading from is right here — let me show you the entry for 14:30."* |
| **Then** | Open `watcher_session.json` and read the relevant entry out loud. |
| **Acceptance** | Judge sees the data the agent SHOULD have answered with |

**Pre-arm this:** keep `watcher_session.json` open in a code editor on a second monitor during the live test.

---

## The pre-demo briefing (read aloud to the team at 11:00 Sun)

> *"If anything breaks during a demo, we don't panic. We pivot. The recording is one keystroke away. The cloud is one env var away. The second laptop is right there. We have ten different things that could go wrong and we have a thirty-second answer for each. The judge will not remember the failure — they'll remember the recovery. So when something breaks, narrate the pivot and keep moving."*

Stand. Say it. Mean it. Then walk to the demo desk.
