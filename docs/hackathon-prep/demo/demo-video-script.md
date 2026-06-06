# 3-5 Minute Submission Video — Script

> Recorded 09:00 Sunday. Submitted by 11:00 Sunday. Watched by judges anywhere from 11:30 Sunday onwards. **Has to stand alone — there's no narrator next to it.**
>
> Target length: **4:00 ± 15 sec.** Hard ceiling: 5:00 (per official rules — videos over 5 min are rejected).
>
> Recorder: Teammate 2 (or Ongun). Voice-over: **Ongun** (consistency with the live demo if a judge watches both).

---

## Difference from the live demo script

| Live demo (3 min) | Submission video (4 min) |
|-------------------|--------------------------|
| Narrator IS in the room | Voice-over only |
| Judges ask follow-ups | Must answer the obvious questions inside the video |
| Phone call is the visceral moment | Phone call is the visceral moment — same |
| 5 demo beats | 6 scenes — adds an explicit "what's under the hood" |
| Sorted opener | Sorted opener — same |

---

## Production setup

- **Tool:** QuickTime screen recording + microphone audio
- **Resolution:** 1920×1080 (1080p)
- **Mic:** AirPods Pro lavalier mode or a dedicated USB mic. Test for sibilance.
- **Background noise:** notifications off, Discord muted, phone in airplane mode
- **B-roll source:** dashboard screenshots from `demo_data/dashboard_screenshots/` + the recorded phone call MP4
- **Cuts:** minimal — one cut between scenes, maybe two. Avoid montage. This is a working-software video, not a Kickstarter campaign.

---

## The 6-scene script

Total target: **4 minutes**. Each scene has its own slack at the end.

### Scene 1 — Hook (0:00 – 0:20)

**On screen:** Sorted cover frame, then crossfade to a black-and-white photo of Vallance Road (or any dumped fly-tipping shot).

**Voice-over:**

> *"In London, residents file over 6,000 civic complaints every month — potholes, fly-tipping, broken streetlights. Most never hear back. The average resolution time is 28 days. The longest report we found took 11 years.*
>
> *We're Sorted. In two days at NVIDIA Hack for Impact, we built the system that doesn't stop until the council acts."*

**Notes:** No on-screen text. Just imagery + voice. The opener has to grab a judge mid-scroll.

---

### Scene 2 — Meet Rebecca (0:20 – 0:50)

**On screen:** the intake app's capture screen. Rebecca's photo (dumped mattresses) appears, then her voice-note button glows.

**Voice-over:**

> *"This is Rebecca's experience. She lives in Tower Hamlets. Her daughter walks past dumped mattresses on Vallance Road every morning. She's reported it three times. She's heard nothing back.*
>
> *Watch what happens when she uses Sorted."*

Tap the photo. Tap the mic icon. Tap Send. **30 seconds total — pace it.**

---

### Scene 3 — The agent at work (0:50 – 2:00)

**On screen:** the processing view. Each agent's output appears in sequence with a brief lower-third label.

**Voice-over (over the live processing):**

> *"One tap. The intake agent — Qwen 2.5 vision, ElevenLabs Scribe — classifies the issue, extracts GPS, structures the report.*
>
> *NVIDIA's Nemotron Super, running locally on our DGX Spark, scores severity nine out of ten — and cites why. Osmani Primary is 44 metres away. Seven serious injuries in STATS19 within 500 metres. Population density 17,000 per square kilometre. Every claim grounded in London open data.*
>
> *The routing agent identifies Tower Hamlets Waste & Environmental Services. The submission agent POSTs directly to the council's Open311 endpoint. Ticket filed.*
>
> *Rebecca's address never left the device."*

**Lower-thirds appear and disappear** as each agent runs. The Nemotron + Llama comparison flashes briefly at 1:20 — the README has the full evidence.

---

### Scene 4 — Time-jump → THE PHONE CALL (2:00 – 3:00)

**On screen:** dark transition card: *"14 DAYS LATER. NO RESPONSE."* → cuts to the live phone-call dashboard view from `demo_data/recorded_call.mp4`.

**Voice-over (before the call audio plays):**

> *"Most civic apps stop here. We don't. Two weeks pass — Camden hasn't responded — and the Sorted Watcher decides to escalate.*
>
> *Listen."*

**The recorded call plays at full volume.** No narration over the call itself. Let the agent's voice + the council rep's response speak for themselves. Includes:
- Agent's introduction
- Reference to the ticket number
- Council rep's "scheduled for collection Tuesday"
- Agent's polite confirmation
- Hang up

**Voice-over (after the call ends, over the watcher log update on screen):**

> *"That call was placed by an autonomous agent — Nemotron Super on the DGX Spark, voice on ElevenLabs Conversational AI. It has been running continuously since Saturday afternoon. It remembers every event in its session. It will keep escalating until Rebecca's report is closed."*

---

### Scene 5 — The accountability layer (3:00 – 3:30)

**On screen:** the public council leaderboard. Greenwich at #1 (composite 100). Camden glowing at #13 (45.3). The BETA badge visible.

**Voice-over:**

> *"And every report Sorted handles updates a public leaderboard. We score every London council on five fair dimensions — not just speed, but per-category performance versus peers, long-tail burden, and reports-per-ten-thousand residents. Camden ranks thirteenth out of thirty-three. The pressure to improve is now public, and accurate, and updated continuously.*
>
> *No other civic app does this."*

---

### Scene 6 — Under the hood + close (3:30 – 4:00)

**On screen:** A diagram or animated build of the architecture: 5 agents, with the model labels under each (Qwen, Scribe, Nemotron, Llama, ElevenLabs Conv AI). Sponsor logos along the bottom.

**Voice-over:**

> *"Five agents. Local inference on NVIDIA's DGX Spark. NVIDIA Nemotron Super for grounded severity reasoning. ElevenLabs Conversational AI for the voice that does not give up. Nebius for cloud overflow when we need it. All built between Saturday morning and Sunday morning at NVIDIA Hack for Impact London.*
>
> *Sorted. We finish what Babbage started.*
>
> *The repo, the dashboard, and the Sorted Watcher's full session log are linked below."*

End card: black background, cream text — `SORTED.` + a single QR code to the GitHub repo + sponsor names.

---

## After recording

- [ ] Watch it back ONCE. End-to-end. No pausing.
- [ ] Total length check: 4:00 ± 15 sec
- [ ] Upload to YouTube **unlisted** (per `submission-checklist.md`)
- [ ] Save MP4 to `demo_data/submission_video.mp4`
- [ ] Save MP4 to USB + Teammate 1's laptop
- [ ] Put the YouTube link in the README AND the submission portal field
- [ ] Test the YouTube link in an incognito tab — if it says "processing" wait until it plays

**No re-edits after 10:00.** If something's wrong, document it in `docs/DECISIONS.md` and ship.

---

## Anti-patterns

- ❌ Reading bullet points from the screen
- ❌ "Hi, we are team Sorted and we are going to show you..." — already on the cover slide. Skip.
- ❌ More than 2 cuts per minute
- ❌ Music behind the voice-over (jury-rigged production)
- ❌ Animated emoji
- ❌ Closing with "thank you for watching" — the end card does the closing
- ❌ Going over 4:30 — every extra second is risk
