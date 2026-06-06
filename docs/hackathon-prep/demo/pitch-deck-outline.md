# Live Pitch Deck — Slide-by-Slide for Sunday Judging

> **This is NOT the team onboarding deck.** That deck told the team why we're here. THIS deck supports the 3-minute live demo at the judging fair, plus 5-7 minutes of Q&A.
>
> **Format:** Keynote / Google Slides. **One slide per demo beat + 6 Q&A backup slides.** Total: 11 slides.
>
> **Owner:** Teammate 2 (or Ongun if Teammate 2 is on video). Build during 08:30 – 10:00 Sunday.
>
> **Design language:** matches the Sorted brand brief (`sorted-identity.md`) — monochrome cog aesthetic, navy + orange accents, JetBrains Mono for code, Inter for text.

---

## Slides 1-5 — Live demo support (during the 3-min demo)

These appear on screen as Ongun speaks. Minimal text, big imagery. Each slide stays up for one demo beat.

### Slide 1 — COVER (during 0:00-0:20)

**Title slide.** Stays up while Ongun delivers the 40-word opener.

- Background: deep navy (#0b1d4e), barely-visible texture
- Big monogram in cream: `SORTED.` (period included, all caps)
- Small subtitle: *We finish what Babbage started.*
- Bottom-right: tiny sponsor strip — NVIDIA · HP · Nebius · ElevenLabs (logos OR text)

**No bullets. No icons. No transitions.** The opener IS the slide.

### Slide 2 — INTAKE (during 0:20-1:00)

Replaces with the actual intake app being mirrored from the phone via QuickTime. **This "slide" is the live app**, not PowerPoint.

If the live mirror breaks: switch to a Slide 2 backup that shows a screenshot of the Done state ("Filed to Camden, severity 9/10…"). Same effect.

### Slide 3 — TIME-JUMP CARD (during 1:00-1:15)

The transition card. Stays up 15 sec.

- Background: dark (#0e1119)
- Big text in cream: **"14 DAYS LATER. NO RESPONSE."**
- Subtitle in lighter grey: *Camden missed its SLA. The Sorted Watcher decides to escalate.*

Subtle slow fade in. Hold. Cut to Slide 4.

### Slide 4 — PHONE CALL VIEW (during 1:15-2:30)

Split-screen on screen mirrored from the demo laptop:
- Left half: live transcript scrolling
- Right half: watcher session log ticking
- Green pulsing dot indicating active call

If live → it's the dashboard view. If recorded → it's the same view but driven by the MP4. Visually identical to the judge.

No PowerPoint slide here either — it's the live dashboard. **Pre-arrange the laptop windows BEFORE the demo starts.**

### Slide 5 — LEADERBOARD (during 2:30-3:00)

Either the live leaderboard view OR a pre-rendered version if the live one is having a bad day.

If you must build a Keynote backup for this:
- Title: *Sorted Public Leaderboard — All 33 London Boroughs*
- The screenshot from `demo_data/dashboard_screenshots/leaderboard.png`
- Pull out three specific cells with arrows: Greenwich #1 (100.0), Camden #13 (45.3), Barking and Dagenham #16 (2.0)

---

## Slides 6-11 — Q&A backup (NOT shown during the 3 minutes — only if judges ask)

These slides answer the questions judges always ask. Stay ready to cut to them.

### Slide 6 — "How does this use Nemotron?"

- Title: *Severity ranking — powered by NVIDIA Nemotron Super 120B-A12B*
- Two-column comparison table screenshot from `bounties/nemotron-bounty-strategy.md`:
  - Llama 3.3: "near schools and busy roads, so it's important"
  - Nemotron: "Osmani Primary is 44m from the location; 7 STATS19 serious injuries within 500m..."
- Footer: *Comparative evidence on a 3-report sample. Full evidence in the repo.*

### Slide 7 — "How does this use ElevenLabs?"

- Title: *Sorted Watcher — persistent agent since [Saturday start time]*
- Three things on the slide:
  - Continuous runtime since `<start ts>` → `<demo ts>` = `<XX>` hours
  - Number of events in session log
  - Sample voice interactions (judges talked to it earlier today)
- Bottom: *Stack — Nemotron Super + ElevenLabs Conv AI · Session log → `watcher_session.json` in the repo*

### Slide 8 — "How is this different from FixMyStreet?"

| | FixMyStreet | Sorted |
|---|---|---|
| Who does the work | User fills the form | Agent does it |
| What happens after | Nothing | Tracks, calls, escalates |
| Severity | First come first served | Cited London open data |
| Privacy | Photos public | Local-first |
| Accountability | None | Public leaderboard |

Title: *Different product category. FixMyStreet is a form. Sorted is a closed loop.*

### Slide 9 — "What did you actually build in 24 hours?"

- Title: *What ships at 11 AM Sunday*
- 5 lines:
  - 5-agent pipeline running locally on the DGX Spark
  - Public dashboard with fair multi-dimensional scorecard
  - Direct Open311 submission to Camden (verified live)
  - Persistent voice agent on ElevenLabs Conv AI
  - ~6,000 scraped FixMyStreet reports + 4 RAG datasets
- Footer: *All code written between 09:30 Saturday and 11:00 Sunday. ~14.5 hours of build time.*

### Slide 10 — "What's next?"

- Title: *Post-hackathon — 30/60/90 days*
- 30 days: pilot conversations with 3 London councils (already in outreach)
- 60 days: production Open311 integrations for 12 boroughs that run FixMyStreet Pro
- 90 days: per-resident dashboard, MP escalation flow, multi-language at runtime
- Footer: *Open source. Sponsored by NVIDIA, HP, Nebius, ElevenLabs.*

### Slide 11 — THANK YOU

- Background: same as cover (deep navy)
- *Thank you — NVIDIA, HP, Nebius, ElevenLabs.*
- Below: *Sorted. We finish what Babbage started.*
- QR code to the live dashboard
- QR code to the GitHub repo

This is the slide that stays up while judges walk to the next team. The QR codes are how they take the project home.

---

## Build instructions for whoever owns the deck

1. Use the existing palette from `static/style.css` — navy `#0b1d4e`, accent orange `#ff5722`, NVIDIA green `#76b900`
2. Inter for body, JetBrains Mono for any code / numbers
3. Each slide must work as a screenshot — assume some judges only see one
4. Export as `sorted_pitch_deck.pdf` AND `sorted_pitch_deck.key` (or .pptx)
5. Both files in `demo_data/deck/` by 10:00 Sunday
6. PDF also in the GitHub repo so judges who read offline see it

---

## Anti-patterns

- ❌ More than 6 words per slide line
- ❌ Animations that take >0.5 sec to complete
- ❌ Build-in / build-out for bullet points — slows you down
- ❌ Stock photos
- ❌ Code on slides 1-5 (those are live demo support, no code)
- ❌ Logos from other AI tools (no Llama logo, no OpenAI, no Anthropic) — only our four sponsors
