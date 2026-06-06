# Twilio Setup — UK Number + ElevenLabs Outbound Calling

> Owner: same as escalation-agent owner. Done by **15:00 Saturday**. **Start Friday evening if possible** — Twilio account verification can take an hour and sometimes asks for ID.
>
> Prerequisite: `elevenlabs-setup.md` complete, Conv AI agent ID in `.env`.

---

## The end state

When you finish this doc, you can run this in Python:

```python
trigger_call("+44 7xxx xxx xxx")
# → a phone rings somewhere in the world
# → Sorted Watcher (ElevenLabs voice) answers when picked up
# → conversation logged
```

That's the demo. Two-line Python from our escalation agent.

---

## Step 1 — Twilio account (10 min — do Friday evening)

1. Sign up: https://www.twilio.com/try-twilio
2. Verify your email
3. Verify your phone (Twilio texts a code)
4. **Free trial gives ~$15 credit** — enough for the hackathon if we don't blow through it on tests
5. Console → Account Info → save these to `.env`:

   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxx
   ```

⚠️ If Twilio asks for a business verification or ID upload — **this is why we start Friday**. It can take an hour. Don't get blocked Saturday.

---

## Step 2 — Buy a UK number (5 min, costs ~$1)

1. Console → **Phone Numbers** → **Buy a number**
2. Filter: Country = **United Kingdom**, capabilities = **Voice**
3. Pick any free number with voice capability — UK landline (+44 20) or mobile (+44 7)
4. Confirm purchase (~$1.00 from trial credit)
5. Copy the number to `.env`:

   ```bash
   TWILIO_FROM_NUMBER=+44XXXXXXXXXX
   ```

**Note:** Trial accounts can only call **verified** numbers. Add Ongun's mobile + every teammate's mobile under **Phone Numbers → Verified Caller IDs** before testing outbound calls. Otherwise the call won't connect.

---

## Step 3 — ngrok webhook tunnel (5 min)

Twilio needs to call back to our laptop when something happens. ngrok is the fastest way to expose a local Flask endpoint to the public internet.

```bash
# Install — macOS
brew install ngrok

# OR Linux
curl -fsSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/ngrok.gpg \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update && sudo apt install ngrok

# Sign up at ngrok.com (free), copy auth token, then:
ngrok config add-authtoken <your-token>

# Tunnel local port 5050 (where our Flask app runs)
ngrok http 5050
```

ngrok prints something like:

```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:5050
```

Save that HTTPS URL — that's our **public webhook base**. It changes every time you restart ngrok, so **leave ngrok running**. If you restart, you must update the Twilio webhook (Step 4).

---

## Step 4 — Wire Twilio number → ElevenLabs (10 min)

Two options, in order of preference:

### Option A: ElevenLabs-native Twilio integration (preferred)

ElevenLabs has built-in Twilio support for Conv AI agents. No webhook plumbing on our side.

1. ElevenLabs dashboard → **Conversational AI** → your `Sorted Watcher` agent
2. **Settings → Phone numbers** → **Connect Twilio**
3. Paste your Twilio Account SID + Auth Token + the UK number you bought
4. ElevenLabs handles inbound + outbound through their backend

Done. **You can call your Twilio number now and the agent will answer.** Test by dialling your UK number from your phone.

### Option B: Manual webhook (fallback)

If Option A is missing for our Conv AI tier or doesn't show up:

1. Twilio Console → Phone Numbers → your number → **Voice Configuration**
2. **A Call Comes In**: Webhook → `https://<ngrok-url>/twilio/incoming` (POST)
3. We need a tiny Flask route that returns TwiML telling Twilio to connect the caller to ElevenLabs Conv AI WebSocket. The route is owned by escalation-agent code — see `escalation-agent-spec.md` for the snippet.

**Default to Option A unless it's not available.**

---

## Step 5 — First outbound call (5 min — *this is the moment*)

With Option A configured, in Python:

```python
# trigger_call.py
import os, requests

resp = requests.post(
    "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
    headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
    json={
        "agent_id": os.environ["ELEVENLABS_AGENT_ID"],
        "agent_phone_number_id": os.environ["ELEVENLABS_PHONE_ID"],  # from ElevenLabs dashboard once Twilio is linked
        "to_number": "+44 7xxx xxx xxx",  # one of your verified caller IDs
    },
)
print(resp.status_code, resp.json())
```

Run it. Your phone should ring in 5-15 seconds. Pick up. You should hear the agent's first message ("Hi, this is an automated call on behalf of a Tower Hamlets resident..."). Have a 30-second chat. Hang up. **This is your demo.**

---

## Step 6 — Hand off to escalation-agent-spec.md

You're done with infra. The escalation agent owns:
- Deciding *when* to call (SLA breach detection)
- Calling `trigger_call(...)` with the right ticket context
- Logging the call outcome to `watcher_session_log`

That logic is in `docs/hackathon-prep/agents/escalation-agent-spec.md` (coming next in the backlog).

---

## What can go wrong (and the fix)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `trigger_call` returns 401 | API key wrong / not loaded | Re-check `.env` (both keys), restart Python |
| Call rings but cuts off after 3 sec | "to_number" not verified | Add to Twilio Verified Caller IDs |
| Agent silent when answered | ElevenLabs agent ID wrong | Re-check `ELEVENLABS_AGENT_ID` |
| Call doesn't ring at all | Trial credit exhausted, number not voice-capable | Console → Account → Usage; verify number's capabilities |
| ngrok URL not reaching Flask | Flask not running on 5050 | Start the dashboard: `python dashboard/app.py` |
| Twilio account flagged for "fraud" | Trial limits / lots of failed calls | Add credit card (~$20) to unblock |

---

## What you should NOT do

- ❌ Buy a premium phone number. Cheapest UK voice-only is fine.
- ❌ Call an actual UK council during testing. Use teammate phones. (And **never** in the demo unless we get permission — pre-recorded fallback is the plan per `decisions-locked.md`.)
- ❌ Spam outbound calls during dev. Each call costs cents and the trial credit dies fast.
- ❌ Leave ngrok unattended on a public URL with secrets — kill it when not testing.

---

## Exit criterion

By 15:00 Saturday, the team can:

1. Dial the UK Twilio number from a personal phone and hear the Sorted agent answer
2. Run `trigger_call.py` and have a phone ring with the agent on the other end
3. Hand off to escalation-agent-spec.md for the orchestration

If 1 and 2 both work — **the killer demo moment is unlocked.**

If neither works by 15:00 — pre-recorded fallback becomes the demo (per `risks/fallback-plan.md` once it exists). Document the failure, move on.
