# Friday Evening Playbook — Doors Open → Building Closes

> 17:30 → 21:00 at the venue. Three and a half hours. Everything you do tonight is time we don't have to spend Saturday morning.
>
> Bring: laptop, charger, headphones, Twilio-verified phone, notebook, a single A4 page with the locked decisions written by hand.

---

## Pre-arrival (do BEFORE 17:30 — at home or commuting)

- [ ] **Twilio account live** — number purchased, verified IDs added (per `setup/twilio-setup.md`). Trial verification can take 60 min, do it now.
- [ ] **Nebius account live** — API key in `.env` (per `setup/nebius-setup.md`)
- [ ] **ElevenLabs account live** — API key + Conv AI agent stub created (per `setup/elevenlabs-setup.md`)
- [ ] **GitHub repo created** — empty, public, name `sorted`. Add team members as collaborators.
- [ ] **NVIDIA Build account live** at https://build.nvidia.com so we have NIM cloud fallback
- [ ] **Goldman teammate** has Cursor installed and signed in (per `setup/cursor-claude-code-setup.md`)
- [ ] **Phone fully charged** + lightning/USB-C cable in your bag (Twilio test number)
- [ ] **Print three copies** of `decisions-locked.md` page 1 — one per teammate. Whiteboarding is faster from paper.

---

## 17:30 – 18:00 · Doors open

**The minute you're inside:**

1. Scan both QR codes from the kickoff deck → join the Discord `#london-hack-for-impact` + bookmark the Notion. Both shown on screen at kickoff.
2. Grab a desk near a wall socket. Mark it with a notebook so it's yours.
3. Pick up your team's sticker colour:
   - **Red** = still looking for a team — wear if Teammate 2 not confirmed
   - **Green** = full team — wear once Teammate 2 is in
4. Find the staff with **yellow / purple stickers** and introduce yourself. They are your escalation path Saturday.

---

## 18:00 · Kickoff — listen for these specific things

The welcome talk will cover the things you already know from the PDF. The bits to actually pay attention to:

- [ ] **Exact location of our DGX Spark** — write the desk number on your hand
- [ ] **Submission portal URL** — it might be on Notion only. Bookmark immediately.
- [ ] **Code freeze rule clarification** — confirm 11:00 Sunday, confirm "must be written during the hackathon" is interpreted as we understand it
- [ ] **Any updates to track judging criteria** — sometimes announced live

---

## 18:15 · ElevenLabs partner talk — the critical 15 minutes

This is when we secure the bounty edge. **Sit at the front.**

- [ ] Listen for the **exact bounty requirements** (1h 11min agent, Nemotron + ElevenLabs voice, judges test live). Note any wording shifts vs the PDF.
- [ ] At the Q&A, ask: *"What's the hackathon credit pool, and is there a process to enable it on a sandbox account?"* — get it applied to our account TONIGHT.
- [ ] Get the speaker's email or Discord handle. *"If we hit a Conv AI tooling issue Saturday, what's the fastest way to reach you?"* — there will be issues.
- [ ] Snap a photo of any slides showing bounty submission format.

---

## 18:30 · HP talk — quick

Be polite. HP is sponsor #2. We don't have a specific bounty angle for them — listen for any unexpected one. Mention Sorted briefly if you get a chance, since the ZGX Nano is one of the track prizes.

---

## 18:35 · DGX Spark training — take notes

The single most important talk for execution risk.

- [ ] **How to access the Spark** — local console vs SSH (confirm which mode for us)
- [ ] **Pre-loaded models list** — what's already on `ollama list` so we don't waste pull time
- [ ] **OS / Python versions** — confirm vs `dgx-spark-setup.md` assumptions
- [ ] **Memory monitoring command** — `nvidia-smi`, or something Spark-specific
- [ ] **What NOT to do** — they will tell us. Write it down literally.
- [ ] **Who to ping if it dies** — name and Discord handle

---

## 19:00 · Pizza + Team Formation

- [ ] If Teammate 2 not confirmed: do a lap with the red sticker. **Looking for: backend dev OR a designer/PM.** Tell them about Sorted in 30 seconds — the protagonist + the leaderboard. Don't try to sell — judge fit.
- [ ] Once confirmed, **switch all three to green stickers.** Visible signal you're not poaching.
- [ ] Open `docs/hackathon-prep/teammate-2-onboarding.md` (P2 backlog — might not exist yet) and walk them through it. If it doesn't exist, walk through the onboarding deck on the laptop instead.
- [ ] All three: read the locked-decisions A4 page together. Confirm everyone agrees. Anyone disagreeing now is a 5-minute conversation. **Disagreement Saturday is fatal.**

---

## 19:30 – 20:30 · Pre-flight while waiting

Quiet, low-stakes work that pays back massively Saturday:

- [ ] **Pull our models in advance**. SSH to the Spark or sit at it. Start `ollama pull llama3.3:70b`, `ollama pull qwen2.5vl:7b`, `ollama pull nemotron-super:120b` in three parallel tabs. **These can run overnight while we sleep.**
- [ ] **Initial repo scaffolding** — empty folders (`src/agents`, `src/models`, `src/integrations`, `dashboard`, `scraper`, `data`, `demo_data`). Push to GitHub.
- [ ] **Add `.gitignore`** for `.venv`, `__pycache__`, `.env`, `*.db`, `data/raw`, `demo_data/uploads`
- [ ] **Create `requirements.txt`** with the libraries we know we'll need: `requests`, `beautifulsoup4`, `lxml`, `flask`, `pydantic`, `ollama`, `elevenlabs`, `openai`, `pandas`, `openpyxl`, `pyproj`, `shapely`, `pillow`, `exifread`
- [ ] **Verify ngrok account** — token added, test tunnel from `5050` works
- [ ] **End-to-end voice test** — play TTS clip on speakers, record on phone, transcribe via Scribe. Catches any setup bug now.

---

## 20:30 · Place a real Twilio + ElevenLabs test call

This is THE most important Friday-night moment. Per `setup/twilio-setup.md`:

- [ ] Run `trigger_call.py` to your own phone.
- [ ] If it works → log a green light in `docs/DECISIONS.md`: *"Live call works. Saturday plan A confirmed."*
- [ ] If it fails → debug for max 60 minutes. If still not working at 20:30 + 1h, accept that recorded fallback is THE plan. Log it. Move on. **Do not let this consume Saturday.**

---

## 20:45 · Closing remarks

- [ ] Confirm Saturday doors open at 8:00 AM
- [ ] Confirm Sunday code freeze 11:00 AM
- [ ] Capture any new info in the team Discord

---

## 21:00 · Building closes — go home and sleep

Last-minute checklist before leaving:

- [ ] Models are pulling overnight on the Spark (write down which tabs are running)
- [ ] Phone is charged
- [ ] Repo URL + .env + Notion link sent to all teammates' personal phones
- [ ] First Saturday alarm set for 07:30
- [ ] Eat. Hydrate. Sleep.

**Saturday begins at the breakfast table tomorrow.** Show up at 8 AM ready.
