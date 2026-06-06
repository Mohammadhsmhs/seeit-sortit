# ElevenLabs Setup — From Zero to Working Voice Agent

> Owner: escalation-agent owner (Teammate 2 if backend, else Ongun). Done by **14:00 Saturday**. This unlocks the ElevenLabs bounty and the killer demo moment.
>
> Twilio specifics live in `twilio-setup.md`. This doc gets the ElevenLabs side ready and ends at "ready to wire up Twilio."
>
> NVIDIA partnered with ElevenLabs for this hackathon, so we likely get **bonus credits or sandbox access** — ask at the ElevenLabs partner talk Friday 18:15.

---

## What we need ElevenLabs to do for us

1. **Scribe** — speech-to-text on Rebecca's voice note in the intake flow
2. **Voice synthesis** — text-to-speech for the agent's voice on the phone call
3. **Conversational AI agent** — the "Sorted Watcher" persistent agent that judges talk to (ElevenLabs bounty)
4. **Outbound calling** — agent calls the council, integrated through Twilio

We will use all four. They're all on the same account, same API key.

---

## Step 1 — Account + API key (5 min)

1. Sign up at https://elevenlabs.io — use a team-owned email (not personal)
2. **At the Friday partner talk, ask:** "We're Team Sorted at NVIDIA Hack for Impact — what's the bonus tier / hackathon credits arrangement?" Get it applied before any usage.
3. Dashboard → top-right profile → **API Keys** → "Create Key" → name it `sorted-hackathon`
4. Save to repo `.env`:
   ```bash
   ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxxxxxx
   ```
5. **NEVER commit `.env`.** Make sure `.gitignore` includes it. Triple-check.

---

## Step 2 — Voice synthesis sanity test (5 min)

Verify TTS works with a 6-line Python script:

```python
# tts_smoke.py
from elevenlabs.client import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # default British male — change later
    model_id="eleven_flash_v2_5",       # low-latency model, ~150ms first chunk
    text="Hello, this is an automated call on behalf of a Tower Hamlets resident.",
)
with open("test.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
print("Wrote test.mp3 — open it to verify.")
```

```bash
pip install elevenlabs
python3 tts_smoke.py
open test.mp3   # macOS — or play it however
```

You should hear a British-accented voice say the line. **If yes — TTS is unblocked.**

---

## Step 3 — Scribe STT sanity test (5 min)

For the intake voice note:

```python
# stt_smoke.py
from elevenlabs.client import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
with open("voice_note.m4a", "rb") as f:           # record a short clip on your phone
    transcript = client.speech_to_text.convert(
        file=f,
        model_id="scribe_v1",
    )
print(transcript.text)
```

Record a 5-second voice note on your phone saying *"There's a pile of dumped mattresses outside my daughter's school on Vallance Road."* AirDrop or drag-and-drop to your laptop. Run the script. You should get the transcript back. **If yes — STT is unblocked.**

---

## Step 4 — Conversational AI agent (15 min — this is the bounty work)

Now create the **persistent agent** that powers the phone call AND the ElevenLabs-bounty live test.

1. Dashboard → **Conversational AI** → **Create Agent**
2. Name: `Sorted Watcher`
3. **System prompt** (paste this — refine Saturday):

   ```
   You are the Sorted Watcher — an autonomous AI agent that monitors
   civic complaints in London and contacts councils when service-level
   agreements are breached.

   You speak briefly, politely, and identify yourself as automated on every
   call. You reference specific ticket numbers, dates, and locations from
   your session context. You never claim to be human.

   If you don't know something, say so. Do not invent ticket numbers,
   addresses, or call outcomes.

   Your context window contains a session log of every civic event you've
   observed today. When asked a question, search that log and answer based
   on what you saw.
   ```

4. **Voice**: pick a calm British voice. Test a few. Save your choice.
5. **First message** (what the agent says when answered):

   ```
   Hi, this is an automated call on behalf of a Tower Hamlets resident.
   I'm following up on a FixMyStreet report — could you confirm the current
   status? I'll only need a minute of your time.
   ```

6. **Tools** (advanced — try Saturday afternoon if time):
   - `query_session_log(query: str)` — searches our local SQLite session_log table for the agent
   - `lookup_ticket(ticket_id: str)` — returns ticket details from our DB

   These integrate via the ElevenLabs Conv AI tool-calling spec. **If we can't get this wired in 60 minutes, skip — the system prompt + voice alone is enough for the demo.**

7. Save. Copy the **Agent ID** to `.env`:

   ```bash
   ELEVENLABS_AGENT_ID=agent_xxxxxxxxxxxxxxxx
   ```

---

## Step 5 — Test the agent in the dashboard sandbox (5 min)

ElevenLabs has a built-in "talk to your agent" widget in the dashboard.

1. Click **Test** on your agent
2. Allow mic access
3. Say *"What was the most recent fly-tipping report you saw?"* — the agent should respond.
4. Say *"How long have you been running?"* — agent answers from system prompt time logic.

If responses come back voiced, sub-3-second latency, and on-character — **agent is unblocked.**

If responses are slow (>5 sec) or off-character → adjust the model under **Settings → LLM** (start with `gpt-4o-mini` for speed, swap to `claude-3.5-sonnet` later if quality matters more). Note: ElevenLabs hosts the LLM for Conv AI — our local Nemotron is for the OTHER agents in our pipeline.

---

## Step 6 — Twilio handoff (1 min)

This is where this doc ends. Read **`twilio-setup.md`** next. By the time you're done with that, you'll have:
- A UK Twilio number
- That number wired to your ElevenLabs agent
- The ability to trigger an outbound call programmatically from Python

That's the demo. Two API calls, two services, one phone ringing.

---

## What can go wrong (and the fix)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| TTS smoke test returns 401 | API key wrong or not loaded | Check `.env`, re-export, re-run |
| Scribe returns empty transcript | File format unsupported | Convert to mp3/wav with `ffmpeg -i in.m4a out.mp3` |
| Conv AI agent says generic "I am an AI" | System prompt not saved | Refresh dashboard, re-save |
| Sandbox agent silent for 10+ seconds | LLM cold start | Wait 30 sec, test again — second call is faster |
| Hackathon credits not applied | Asked too late | Find ElevenLabs staff (Friday 18:15 partner talk is your moment) |

---

## What you should NOT do

- ❌ Pay for a higher tier subscription if usage is metered. We're hoping for hackathon credits.
- ❌ Build a custom STT/TTS pipeline. Use ElevenLabs' SDK. We don't have time.
- ❌ Switch to a self-hosted voice model. Out of scope.
- ❌ Train a custom voice. Use the stock British voice. It's good enough.

---

## Exit criterion

By 14:00 Saturday, you can:

1. Talk to the agent in the ElevenLabs dashboard sandbox and get on-character responses
2. Generate a voice clip from Python in <5 seconds
3. Transcribe a voice note from Python in <5 seconds
4. Move on to `twilio-setup.md`

If you can't do all four by 14:00 — escalate. Cut order is in `decisions-locked.md` and the cut-list.
