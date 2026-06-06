# Demo Data Package — What We Pre-Stage

> Inventory of every asset the demo touches. **All of it must be on three machines** (Ongun's laptop + Teammate 1's laptop + a USB stick) by 20:30 Saturday so a single hardware failure doesn't kill the demo.
>
> Owner: **Teammate 2 if frontend/PM**, else Ongun. Done by **20:30 Saturday**.

---

## The protagonist — Rebecca H.

| Field | Locked value |
|-------|--------------|
| First name | Rebecca |
| Last name initial (on-screen, in calls) | H. |
| Borough (story) | Tower Hamlets |
| Address (story) | Vallance Road, near Osmani Primary School |
| Approximate coords | **51.521, -0.0656** (matches Vallance Road) |
| Persona detail | Single mum, daughter walks to school |

Rebecca is **not real**. The README discloses that. Treat her as a composite of the ~6,000 real Rebeccas in our scraper data.

---

## Asset 1 — The photo

| | |
|---|---|
| **File path** | `demo_data/rebecca_photo.jpg` |
| **What's in it** | A pile of dumped mattresses + bin bags on a residential pavement, with a brick wall and railings visible. Looks like London. |
| **Source** | One of: (a) take it yourself on Vallance Road (best — real EXIF including GPS), (b) one of the scraped photos in `scraper/photos/flytipping/` re-encoded with synthetic EXIF GPS for 51.521, -0.0656 |
| **EXIF GPS** | Required. If from scraper, use `exiftool` to inject. If self-shot, don't strip. |
| **Size** | Compress to <2 MB so vision inference is snappy |

```bash
# Inject EXIF GPS into a scraped photo
exiftool -GPSLatitude=51.521 -GPSLatitudeRef=N \
         -GPSLongitude=0.0656 -GPSLongitudeRef=W \
         demo_data/rebecca_photo.jpg
```

Backup copies: `demo_data_backup/rebecca_photo.jpg` on USB.

---

## Asset 2 — The voice note

| | |
|---|---|
| **File path** | `demo_data/rebecca_voice.m4a` |
| **Transcript (locked)** | *"Hi, there's a pile of dumped mattresses and bin bags outside my daughter's school on Vallance Road. It's been there three days. Could someone come and clear it?"* |
| **Length** | ~10-12 seconds |
| **Recorded by** | Whoever on the team has a non-Ongun voice — judges shouldn't match the narrator's voice to the protagonist |
| **Format** | m4a (iPhone Voice Memo default) — Scribe handles this directly |

**Backup transcript path:** if Scribe fails live, the orchestrator falls back to a hardcoded transcript matching the above text. Implement this fallback or you risk a silent demo.

---

## Asset 3 — The location

```python
LOCATION = {
    "latitude":  51.521,
    "longitude": -0.0656,
    "address":   "Vallance Road, Tower Hamlets, London E1",
    "borough":   "Tower Hamlets",
    "near":      ["Osmani Primary School", "Thomas Buxton Primary School"],
    "lsoa":      "Tower Hamlets 023A",  # for density citation
}
```

These are **real** coordinates on Vallance Road. The schools are real. The LSOA is real. The severity citations the demo shows reference real data points.

---

## Asset 4 — The submission target (Camden Open311 sandbox)

Per `decisions-locked.md`: routing says Tower Hamlets honestly, but the actual API call goes to Camden's Open311 sandbox. The README discloses.

| | |
|---|---|
| Endpoint | `https://fixmystreet.camden.gov.uk/open311/v2/requests.xml` |
| `jurisdiction_id` | `camden.gov.uk` |
| `service_code` | `FLYTIP` (verify exact code from Camden's `services.xml` Saturday morning) |
| `email` field on payload | `sorted-hackathon@<our-throwaway-domain>` |
| Expected ticket prefix | `BB-<8-hex>` (we generate this; council assigns their own ID too) |

**Pre-flight Saturday afternoon:** fire one real test submission so we know the workflow + we have a real `submission_response` for the dashboard to show. **Do this before the live demo so we're not first-call-of-the-day.**

---

## Asset 5 — The pre-recorded phone call (FALLBACK)

| | |
|---|---|
| **File path** | `demo_data/recorded_call.mp4` |
| **Length** | 60-75 seconds |
| **Format** | MP4 video showing the dashboard's call view + audio of the conversation |
| **Recorded** | Saturday 20:30 — see `saturday-evening-review.md` for the recording session |
| **What's in it** | The full agent call to a teammate's mobile, agent introduces itself, references ticket, gets the "scheduled Tuesday" response, hangs up. Same script as live. |
| **Used when** | Live call fails or skips (per `decisions-locked.md`, this is the default plan and live is the bonus) |

Backup: same file on USB + uploaded to a private YouTube unlisted link so we can pull from any laptop.

**Production rule:** the recording is the demo. The live call is the bonus take. Don't burn time pursuing a live demo at 11:30 AM if the recording works perfectly.

---

## Asset 6 — Seed events for the Watcher

`src/data/seed_events.py` (per `agents/escalation-agent-spec.md`) pre-seeds the watcher's session log with ~50 events between Saturday 13:00 and Sunday 11:00. The DETERMINISTIC ones are:

| Time | Event | Purpose |
|------|-------|---------|
| Sat 13:00 | watcher_start | proves session started |
| Sat 14:30 | new_report (Rebecca, Vallance Road, fly-tip, severity 9) | the protagonist's submission gets seeded if not live |
| Sat 14:45 | submission_response received (Camden ack) | shows the council took it |
| Sun 09:00 | sla_breach (Rebecca's report, simulated time) | the trigger for the demo phone call |
| Sun 09:01 | outbound_call_start | matches the demo timing |
| Sun 09:02 | outbound_call_outcome (scheduled_collection_tuesday) | the answer the agent has on file |

Plus 40+ filler events (other boroughs, other categories) so the log isn't suspiciously thin.

---

## Asset 7 — Dashboard "real" data behind the story

The dashboard's map shows ~6,000 scraped FixMyStreet reports. **One of those reports is repurposed as Rebecca's** — we pick a Tower Hamlets fly-tipping ticket with photos and updates, and clone its UI into the demo flow.

| | |
|---|---|
| Source FixMyStreet ID | TBD — pick by Saturday 17:00 from `scraper/fixmystreet.db` |
| Selection criteria | `borough='Tower Hamlets' AND category LIKE '%flytipping%' AND photo_urls IS NOT NULL` |
| Why we mirror an existing ticket | The drawer needs real photo carousel + real comments for visual depth |

---

## Pre-flight checklist (Sat 20:30)

- [ ] `rebecca_photo.jpg` exists, EXIF GPS verified with `exiftool demo_data/rebecca_photo.jpg | grep GPS`
- [ ] `rebecca_voice.m4a` plays cleanly, ~10 sec
- [ ] `recorded_call.mp4` plays — agent voice, council voice, full arc
- [ ] One real Camden Open311 test submission completed, response captured to dashboard
- [ ] Source FixMyStreet ticket ID chosen and saved to `demo_data/source_ticket_id.txt`
- [ ] All seven assets copied to USB + Teammate 1's laptop + Ongun's laptop
- [ ] `seed_events.py` ran a dry-run print and outputs look correct

---

## What can go wrong

| Symptom | Fix |
|---------|-----|
| Photo has no GPS during demo | Inject EXIF with exiftool earlier in the day, not at 11:30 Sun |
| Voice note unintelligible | Re-record with a different teammate; quiet room; check volume |
| Camden submission returns 5xx | Recorded fallback shows a pre-captured success response |
| Recorded call video stutters | MP4 not MOV; bitrate <8 Mbps; play locally not from cloud |
| Seed events out of order | Sort by ts on insert; replay from sorted list |

---

## Hand-off

The demo data lives in `demo_data/` in the repo (gitignored if sensitive — but most of this is public-grade). The demo script (`demo-script-3min.md`) references these paths directly. Anyone running a fresh laptop at the demo just needs:

```bash
git clone <repo>
cp -r /Volumes/usb/demo_data ./demo_data    # restore from USB
python -m src.agents.watcher --new-session  # start with a fresh-but-seeded session
open dashboard/index.html
```

…and the demo is reproducible from a cold start in under 2 minutes.
