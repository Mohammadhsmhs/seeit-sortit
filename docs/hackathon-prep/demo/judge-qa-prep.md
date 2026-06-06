# Judge Q&A Prep — Rehearsed Answers

> The 3-min demo lands at 2:30 ish. The next 5-7 min belongs to whoever's asking questions. **Most judges ask the same 10 questions.** Memorise the answers to the top 5, paraphrase the rest. Each answer is 20-30 sec — confident, specific, defensible.
>
> **Rule:** the answer ends on a hook back to one of our 3 differentiators (closed-loop / leaderboard / privacy). Don't ramble. Land.

---

## Tier 1 — These will be asked (rehearse cold)

### 1. "How does this use NVIDIA Nemotron?"

> *"The severity ranking agent runs on Nemotron Super 120B-A12B, locally on the DGX Spark. We picked Nemotron specifically because severity needs grounded reasoning over four heterogeneous London open datasets — collisions, schools, hospitals, density — and must produce a cited rationale. In our comparative tests Nemotron quoted specific facts where Llama 3.3 paraphrased. The repo has the side-by-side."*

**Don't say:** "It works really well." "We used it for everything."

**Land:** *"It's the only thing in the pipeline that needs that quality of reasoning — everything else is Llama 3.3."*

---

### 2. "How does this use ElevenLabs?"

> *"Three places. Scribe transcribes the resident's voice note at intake. Voice synthesis powers the phone call. And our Sorted Watcher is a persistent agent built on ElevenLabs Conversational AI — it's been running since Saturday afternoon, currently {{ X }} hours, with {{ Y }} events in its session log. Judges can talk to it directly and ask about any event in its memory. The session log is in the repo at `watcher_session.json`."*

**Don't say:** "We just call their API." (Underplays the bounty entry.)

**Land:** *"This is our ElevenLabs bounty submission — the agent never sleeps."*

---

### 3. "How is this different from FixMyStreet?"

> *"FixMyStreet is a form. Sorted is a closed loop. Three differences. FixMyStreet asks the user to fill in a form with 67 to 146 category options — Sorted takes a photo and a voice note. FixMyStreet files the report and stops — Sorted tracks the SLA, places a phone call to the council, and drafts complaints when the council ignores it. And FixMyStreet has no accountability layer — Sorted publicly ranks every London council on a multi-dimensional scorecard so residents see who's actually performing."*

**Don't say:** "It's better." (Vague.) "We're a competitor." (Adversarial.)

**Land:** *"It's a different product category — they make submission easier, we make resolution happen."*

---

### 4. "What did you actually build in 24 hours?"

> *"Five agents end-to-end on the DGX Spark — intake, severity ranking, routing, Open311 submission, persistent escalation. A public dashboard with a fair scorecard ranking all 33 London boroughs. ~6,000 scraped FixMyStreet reports as the data backbone. Four loaded RAG datasets. Verified live Open311 submission to Camden. And the Watcher has been running continuously since Saturday afternoon. All written between 09:30 Saturday and 11:00 Sunday."*

**Don't say:** "We didn't quite finish X." (Don't volunteer gaps.)

**Land:** *"Every component runs. The demo is live, not pre-recorded."* (assuming live works — adjust if recorded)

---

### 5. "What would you do with another month?"

> *"Three things. One — pilot conversations with three London councils we've already been in touch with via constituent MPs. Two — wire up the eleven other London boroughs that run FixMyStreet Pro and inherit Open311 endpoints, plus Playwright form-fill for the holdouts like Tower Hamlets. Three — the persistent agent serves the resident, not just the council. After the Watcher places the SLA call, it texts Rebecca with the update. The closed loop closes back to the citizen, not just the council."*

**Don't say:** "More features." "Refactor."

**Land:** *"The accountability layer is the moat — that's the part nobody else has, and that's what we'd double down on."*

---

## Tier 2 — Plausible follow-ups (paraphrase, don't memorise)

### "How do you handle privacy?"

All inference is local on the Spark. The photo and voice note never leave the device. The only thing that does is the structured report — and it goes to the one council CRM that needs it. No third-party analytics. ElevenLabs touches synthesised audio for the phone call, not citizen audio.

### "What about councils that aren't on Open311?"

We have four channels in our routing table — Open311 (primary), Love Clean Streets, bespoke web forms (Playwright-fillable post-hackathon), and email as the universal fallback. ~12 London boroughs run FixMyStreet Pro and inherit Open311 automatically. The other 21 get email-with-disclosure today.

### "Doesn't FixMyStreet already publish data?"

Public report data, yes. Per-borough performance comparison, no. We built the fair scorecard — five dimensions normalised for borough size and category mix. Greenwich ranks number one. Camden number thirteen. Nobody else publishes that view.

### "How does the agent disclose itself?"

Every outbound phone call opens with *"Hi, this is an automated call on behalf of a {borough} resident."* The submission text always starts *"[Sorted — auto-submission on behalf of a resident]."* It's in the spoken script and in the Open311 payload. Required by AI ethics.

### "What if a council asks Sorted to stop calling?"

There's a `do_not_call` flag in the routing table. We respect it. The Watcher's call-trigger logic checks it before every dial. For the hackathon we haven't been asked — we're not actually calling councils live during normal operation, just during the demo and against a test number.

---

## Tier 3 — Gotcha questions (be ready)

### "Did the agent really call a real council?"

> *"For the demo we call our own number through Twilio. We tested against Camden's customer-service IVR on Friday evening for protocol confirmation. We do NOT spam real councils in production-without-permission — that's an integrity line we don't cross. The bounty entry's Watcher process places calls to numbers we own."*

### "Is the resident's voice synthesised?"

> *"No. Rebecca's voice note is a real recording from one of our team — Scribe transcribes it. The synthesised voice is only the agent on the phone call."*

### "Could a council just block this?"

> *"Open311 is a standard a council chose to publish. Blocking us would mean blocking residents — and FixMyStreet uses the same endpoint we use. They can deprioritise Sorted-tagged submissions, but the AI ethics disclosure lets them filter if they want to."*

### "What if the model returns garbage?"

> *"The orchestrator catches per-stage failures and uses the previous stage's output. The severity agent has a hardcoded fallback rationale. The pipeline never crashes — at worst, a citizen gets a less-cited submission. We tested with malformed inputs Saturday evening."*

### "Aren't there 6 other teams who built this?"

> *"NVIDIA ran the same hackathon in Toronto two weeks ago. Six teams built civic complaint tools — none won the Public Services track. The winner, Belong, was a dementia care companion that picked one person, replaced something expensive, and led with privacy. We did all three: Rebecca, the £200/hour ombudsman, on-device. Plus the accountability leaderboard nobody else built."*

---

## Anti-patterns under questioning

- ❌ "I think" / "We tried" / "Hopefully" — indicative voice
- ❌ Filler: "kind of," "sort of," "basically"
- ❌ Apologising for what we didn't build
- ❌ Talking longer than 30 sec on any one question
- ❌ Saying "good question" — say the answer
- ❌ Defensive body language — palms open, slow nods
- ❌ Inviting follow-ups by trailing off

---

## The escape hatch

If a judge asks something you genuinely don't know:

> *"I don't know — that's a real question we'd answer in week one of a pilot. What's the right way to get a quick answer to that for you?"*

Honest, redirects to their expertise, signals we want their feedback. Beats fumbling.
