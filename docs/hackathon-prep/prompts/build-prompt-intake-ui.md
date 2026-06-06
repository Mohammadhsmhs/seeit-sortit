# Build Prompt — Consumer Intake UI

> Paste into Cursor by **Teammate 2 (if frontend)** or the second-pair dev at **14:00 Saturday**. Estimated build time: **90 min** total over 2 turns.
>
> This is Rebecca's experience. It's the FIRST 15 seconds of the demo. It has to feel native, fast, and trustworthy.

---

## What you're about to build

A single page at `/app` (mobile-first, PWA-installable) with three states:

1. **Capture** — tap the big camera circle, take a photo. Tap a mic icon, record voice. Tap "Send."
2. **Processing** — quick spinner while the agent runs.
3. **Done** — green checkmark, the agent's summary (category + severity + which council it went to + ETA).

That's the entire UX. No login. No forms. No category dropdown. The agent handles everything else.

---

## Turn 1 — Capture flow (45 min)

```
GOAL: Build the consumer intake page at /app for the Sorted civic agent.
Mobile-first. Camera + voice + GPS capture. One "Send" button. Posts a
multipart/form-data request to /api/intake-submit.

CONSTRAINTS:
- Routes (add to dashboard/app.py):
  - GET /app -> render app/intake.html
  - POST /api/intake-submit -> accepts multipart with fields:
      photo (file), voice (file), lat (float), lon (float)
    Saves photo + voice to demo_data/uploads/{timestamp}/, calls
    Orchestrator().process(...), returns JSON of the resulting CivicIssue
- File: dashboard/templates/app/intake.html (single file, ≈300 lines)
- Vanilla JS, no build step. Use camera via navigator.mediaDevices.getUserMedia
  with { video: { facingMode: 'environment' } }. Photo capture by drawing
  video frame to a hidden canvas and toBlob.
- Voice via MediaRecorder API. Record button starts/stops. Max 30 sec
  (auto-stop after 30s). Show a tiny waveform or pulsing dot during recording.
- GPS via navigator.geolocation.getCurrentPosition. Show "Locating…" then
  green checkmark when set.
- Visual: full-screen iPhone-style. Single navy button "Send to Sorted"
  becomes enabled only when (photo OR voice) AND GPS exist.
- Privacy line at the bottom in small grey type:
  "All processing happens on the device. Your photo and address never go to
  any third party — only the structured report leaves, to the one council
  that needs it."
- No CSS frameworks. System font stack. iOS-feel.

ACCEPTANCE:
- Open localhost:5050/app on a phone (via ngrok if needed) or in Chrome with
  device emulation
- Tap the camera circle -> permission prompt -> camera preview appears
- Take a photo (tap shutter overlay) -> thumbnail appears
- Tap mic icon -> permission -> recording starts; tap again to stop
- "Send to Sorted" is disabled until you have at least one input + GPS
- Tap Send -> POST goes to /api/intake-submit, response logged in console
```

After Turn 1 works, commit. Move to Turn 2.

---

## Turn 2 — Processing + Done states + PWA polish (45 min)

```
GOAL: Add Processing and Done states, plus PWA manifest so "Add to Home
Screen" creates a native-feeling app icon.

CONSTRAINTS:
- After Send is tapped: hide the capture UI, show a centered spinner with
  text "Sorted is processing…". Poll or await the /api/intake-submit
  response.
- On response, switch to Done state:
  - Big green checkmark animation (CSS only, no Lottie)
  - "We've filed your report to {council}." (from the response)
  - "Severity {score}/10 — {one-line rationale}" (also from response)
  - "Estimated resolution: {ETA based on category}" — use a hardcoded
    lookup: fly-tipping=5 days, pothole=14 days, default=14 days
  - "Track this report" link to /dashboard/report/{id}
  - Small grey "Submit another" button -> resets to capture state
- PWA setup:
  - Add dashboard/static/manifest.json with name "Sorted", short_name
    "Sorted", theme_color #1a237e, background_color #ffffff, display
    "standalone", icon set (192x192 + 512x512 PNG of a single black cog
    on cream background)
  - Add to intake.html <head>:
    <link rel="manifest" href="/static/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#1a237e">
    <link rel="apple-touch-icon" href="/static/sorted-icon-180.png">
- Service worker is OPTIONAL — skip if it adds friction. The other PWA
  tags work without one for "Add to Home Screen" on iOS.

ACCEPTANCE:
- Tap Send -> spinner appears within 100ms
- After backend returns, switch to Done state within 200ms
- "Submit another" resets cleanly
- Open the page in iOS Safari, tap Share -> Add to Home Screen -> icon
  appears on home screen with cog
- Tapping the home-screen icon opens the app full-screen (no Safari chrome)
```

---

## Common AI corrections during these turns

| If AI generates | Correct with |
|-----------------|--------------|
| React Native or Capacitor | "Plain HTML + vanilla JS. PWA only." |
| `getUserMedia` without `facingMode: 'environment'` | "Use the back camera by default" |
| File input instead of live camera | "Use the camera API, not a file picker" |
| jQuery for the audio waveform | "Plain JS — just a pulsing dot is fine" |
| Complicated state management library | "Two state variables: currentState ('capture'|'processing'|'done') and capturedData" |
| Loading animation libraries | "Plain CSS spinner — 4 lines of @keyframes" |

---

## Browser permissions on iOS — gotcha

iOS Safari requires HTTPS for camera/mic access. **ngrok provides HTTPS automatically** — when sharing the dev URL, always copy the `https://` one, not `http://`.

Also: Safari is more strict than Chrome. **Test on a real iPhone before the demo**, not just Chrome device emulation. The camera permission flow is subtly different.

---

## Time budget

- Turn 1: 45 min
- Turn 2: 45 min
- Real-iPhone testing: 15 min
- Commit + brief note in `docs/DECISIONS.md`: 5 min

Total: ~110 min. If you're past 2.5 hours — **commit what works and stop**. A working capture flow with a simple "Submitted." screen beats a half-built PWA.

---

## Hand-off

The page POSTs to `/api/intake-submit`, which calls the orchestrator. The orchestrator does its 5-stage thing and returns the CivicIssue. The Done state displays the result.

The data ends up in `processed_issues`, the watcher sees it, and (eventually) the SLA breach triggers a phone call.

That's the closed loop, started by one tap of a green button.
