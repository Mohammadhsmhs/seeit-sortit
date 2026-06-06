# Pilot Interest Outreach — MPs & Councillors

Two separate emails because the audiences are different:
- **MPs** are political stakeholders, not operators. Their value is endorsement + intros + visibility.
- **Councillors** (especially cabinet members for Environment / Streets / Highways) are operators. Their value is access to a real pilot.

Both emails ask for **one thing**: a two-line "yes, keep me informed when you launch" reply. Low commitment, easy yes.

The goal is to be able to say in the hackathon pitch:
> *"X London councils and Y MPs have indicated they want to pilot or follow this when we complete it."*

---

## EMAIL 1 — For MPs

**Subject:** Would you back a London civic-tech pilot? 90 seconds to read

---

Dear [MP First Name],

I'm Ongun, leading a team at the NVIDIA Hack for Impact London this weekend (5–7 June). We're building something I think would help your constituents materially, and I'd value a one-line yes if it's of interest.

**The problem.** Reporting a pothole or fly-tip in London takes 8–10 clicks, 67–146 category options, and after submitting, residents hear nothing. Most give up.

**What we're building.** An AI agent that turns a photo and a voice note into a filed report — but more importantly, it *closes the loop*:

- Tells the resident their priority position and an honest ETA based on similar reports nearby
- Shows what the council has resolved in the last week, so they see action is happening
- Tracks the SLA and escalates by phone if the council misses it
- Drafts a formal letter to the LGO or MP only if needed

It's privacy-first (all inference on NVIDIA hardware, photos stay on device) and uses London Datastore + TfL collision data to rank severity. We've already scraped 6,000+ historical reports across 24 boroughs and built a public dashboard ranking council performance fairly — not by raw resolution time, but by per-category league position vs peers.

**What I'm asking.** Two lines back: *"Yes, please keep me informed when you launch — happy to consider a constituency pilot."* That's it. No commitment beyond signalling interest.

If you'd be willing to tweet support during the hackathon weekend, even better — but only if you've seen something we've shipped.

We're backed by NVIDIA, HP, and Nebius for the hackathon. The project will be open source and free for any London council to adopt.

A 90-second demo video and 1-page brief are linked below — happy to send them if useful.

Best,
**Ongun Ozdemir**
[Lead developer — London Civic Agent]
[email]
[GitHub link]
[demo video link]

---

## EMAIL 2 — For Councillors (especially Cabinet Members for Environment, Streets, Highways, Public Realm)

**Subject:** Would [Borough Name] consider a 4-week post-hackathon pilot?

---

Dear Councillor [Surname],

I'm Ongun, leading a team at the NVIDIA Hack for Impact London this weekend. I'd value 90 seconds of your time and a two-line reply.

We're building something to **help both residents and council teams** — and I'm reaching out specifically because you hold the [Environment / Streets / Public Realm] portfolio in [Borough].

**The problem councils face.** Your team gets hundreds of FixMyStreet and direct reports a week. Triaging them fairly — pothole on a school route vs graffiti on a side road — eats time. Residents who don't get updates assume nothing's happening, even when work is in progress.

**What we're building.** An agent that helps on both sides:

For residents — files the report cleanly via Open311 (no spam, no duplicates), shows them their honest priority position and an ETA based on historical patterns, and shows them what your team has resolved this week so they see momentum.

For council teams — ranks incoming reports by genuine impact using cited London open data (collision history, school/hospital proximity, footfall, population density). Surfaces priority mismatches in the backlog. Helps your team focus on what matters without us imposing a view.

**Tech.** Runs locally on NVIDIA hardware. Privacy-first — citizen photos and case data don't leave the device. Open source. Backed by NVIDIA, HP, and Nebius for the hackathon, free for any London borough to adopt afterwards.

**What I'm asking.** Two lines: *"Yes, [Borough] would consider a 4-week pilot once you're ready — please follow up after the hackathon."* That's the entire commitment. If a colleague would be better placed to receive a follow-up, please point me to them.

We have a working dashboard already analysing ~6,000 historical reports across 24 boroughs — happy to share what we see specifically for [Borough] if useful.

Best,
**Ongun Ozdemir**
[Lead developer — London Civic Agent]
[email] · [demo link] · [GitHub]

---

## EMAIL 3 — Short follow-up version (for week-later chase)

**Subject:** Quick follow-up — London Civic Agent pilot interest

Dear [First Name],

A quick follow-up on my email last week about the London Civic Agent we built at NVIDIA's London hackathon.

If a pilot in [Borough/Constituency] is worth a conversation, a two-line *"yes, please follow up in [month]"* is all we need — we'll handle the rest.

The dashboard is live at [URL] if you'd like to see what we built for your area specifically.

Best,
**Ongun**

---

## Sending playbook

### 1. Send order (Sunday evening, after the hackathon)
- **Tier 1 MPs** (Joe Powell, Georgia Gould, Feryal Clark, Meg Hillier) — personalised, individual sends
- **All 74 London MPs** — bulk via mail-merge or BCC batches of 20
- **Cabinet members** for Environment / Streets in priority boroughs (Camden, Hackney, Westminster, Southwark, Islington — councils where we already have data) — individual sends

### 2. Avoid these mistakes
- Don't send during parliamentary recess — check the calendar
- Don't email the same person within 5 days
- Don't send to staff emails unless you can't find a personal one
- Don't ask for money or endorsement of a specific policy

### 3. What to track
A simple spreadsheet:

| Recipient | Role | Sent | Reply | Interest level | Notes |
|-----------|------|------|-------|----------------|-------|

"Interest level": *Yes-pilot / Yes-keep-informed / No-thanks / No-reply*

### 4. The pitch-deck line
Once you have replies, the deck line is:

> *"As of [date], X London MPs and Y councillors representing Z boroughs have indicated interest in piloting or being kept informed."*

Even 3-5 yeses is a strong line.

### 5. GDPR / legitimate interest
MPs and councillors publish work emails on official sites. This is legitimate civic communication — not marketing. No consent issues. Keep it factual, don't add anyone to a marketing list.

### 6. Before sending — checklist
- [ ] Demo video uploaded (even 60 seconds is enough)
- [ ] One-page brief PDF ready
- [ ] Dashboard live and accessible (link tested on mobile)
- [ ] GitHub repo public with a readable README
- [ ] Your email signature includes phone number (some MPs prefer phone)
- [ ] Reply-to address is monitored — don't miss a yes

### 7. Council officer angle (post-hackathon, after this round)
Once you have councillor interest, the *real* operators are council officers — Head of Highways, Director of Public Realm. Councillors will introduce you. Don't cold-email officers in round 1.
