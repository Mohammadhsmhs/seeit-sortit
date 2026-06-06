# Outreach Email to London MPs

Goal: introduce the project, get a meeting or pilot interest.
Tone: respectful, concrete, light on jargon, short enough to actually read.

---

## Version A — Standard (bulk-friendly)

**Subject:** A 15-second civic complaint platform for your constituents — built this weekend at NVIDIA's London hackathon

Dear [MP First Name],

I'm Ongun, a developer leading a team at the NVIDIA Hack for Impact London (5–7 June). We're building something I think your constituents would benefit from, and I'd like a few minutes of your time.

**The problem.** Reporting a pothole or fly-tip to a London council takes 8–10 clicks, 5–15 minutes, and 67–146 category options to navigate. No council in London has a "report a problem" button on their homepage. Worst of all: after submitting, nothing happens. Residents have to chase the council manually, and most give up.

**What we built.** A multi-agent AI system that lets a resident take one photo and say "there's a pothole here" — and the agent does the rest: classifies the issue, identifies the correct department, scores severity using London open data (collision history, school proximity, footfall), submits the report directly to the council's CRM via Open311, and tracks the SLA. If the council misses its deadline, the agent escalates by phone, then drafts a formal complaint to the LGO and to you, the MP.

**The differences from FixMyStreet.**
- Acts on behalf of the resident — they don't fill forms
- Ranks reports by impact, not arrival order
- Closes the loop — tracks, calls, escalates
- All inference runs locally on NVIDIA hardware — photos and case data don't leave the device
- Includes a public dashboard ranking councils by resolution performance

**What I'm asking for.**
1. A 20-minute conversation after the hackathon (June 9 onwards) — I'd value your perspective on what councils and constituents most need.
2. If you see promise, would you be willing to pilot it in [Constituency Name]? We'd run it free for six months.
3. Even a single tweet of support during the hackathon weekend would help us reach more local councils.

The project is open source and non-commercial. Our team is unpaid. We're motivated by the fact that everyone we've spoken to has a story about a pothole that took eight months to fix.

Happy to send a 3-minute demo video, our architecture write-up, or a deck — whichever you'd prefer.

Best,
Ongun Ozdemir
[email]
[GitHub link]

---

## Version B — Personalised for Tier 1 targets

Use Version A as the base, but replace the opening paragraph with one of these:

### For Joe Powell (Kensington and Bayswater)
> Given your work leading the Open Government Partnership, I think you'd find this project interesting — it's a direct extension of the OGP principles into local government accountability.

### For Georgia Gould (Queen's Park and Maida Vale)
> As former Leader of Camden Council, you've seen first-hand how hard it is to bridge the gap between citizen reports and council action. We're trying to solve exactly that bridge.

### For Feryal Clark (Enfield North)
> Given your role on AI policy at DSIT, you'll know that the most defensible AI deployments are local-inference, privacy-first, and built on UK open data. That's exactly what we're shipping at NVIDIA's London hackathon this weekend.

### For Meg Hillier (Hackney South and Shoreditch)
> Your PAC work scrutinising government digital programmes was foundational to my thinking on this project — we're trying to build something that works the way those reports said it should.

---

## Version C — Short version (under 100 words, for replies/follow-ups)

**Subject:** 20 minutes after Sunday's NVIDIA hackathon?

Dear [MP First Name],

I'm building an AI agent at NVIDIA's London hackathon (5–7 June) that lets your constituents report a pothole with one photo and one voice note — and tracks the council until it's fixed. Local AI, London open data, open source.

It demonstrates publicly which councils are responsive and which aren't.

Would you have 20 minutes after the weekend to take a look? Happy to come to you.

Thanks,
Ongun Ozdemir

---

## Sending Strategy
1. **Tier 1 (6 MPs)** → Version B, personalised, sent individually
2. **All 75 London MPs** → Version A, BCC batched (max 20 per batch to avoid spam filters), sent over 3-4 days
3. **Track replies** in a simple spreadsheet
4. **Follow up** with Version C after 7 days if no reply
5. **GDPR**: emails are work addresses listed publicly on parliament.uk — this is legitimate constituent / civic communication, not marketing. No consent issues.

## What NOT to do
- Don't send during recess (check Parliament calendar)
- Don't email same MP multiple times in one week
- Don't ask for money
- Don't make policy claims you can't back up with data from our analysis (we have it — use it)
- Don't promise a working live demo unless we have a recorded fallback ready
