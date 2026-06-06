# London Civic Agent — Hackathon Presentation Outline

---

## Slide 1: Title

**Title:** London Civic Agent: AI That Fights For Your Neighbourhood

**Key points:**
- Team name and members
- NVIDIA DGX Spark Hackathon 2026
- Built on Llama 3.3 70B + NeMo + RAG
- Tagline: "From complaint to resolution — AI that holds councils accountable"

**Speaker notes:**
Open with the hook: "Every month, 12,000 Londoners report problems to their council. Most wait over 30 days for a fix. We built an AI agent that changes that." Introduce the team briefly. Keep this slide up for under 30 seconds.

**On screen:** Title card with project name, team, logos (NVIDIA, Llama, NeMo).

---

## Slide 2: The Problem

**Title:** London's Civic Reporting Is Broken

**Key points:**
- Median 30-day resolution time for council-reported issues
- 12,000+ reports per month across London boroughs
- No accountability — reports disappear into a black hole
- Citizens don't know who to contact, which department, or how to escalate
- Vulnerable communities (elderly, disabled, non-English speakers) hit hardest

**Speaker notes:**
Paint the picture: "Imagine you report a dangerous pothole near a school. You wait. And wait. Thirty days later, nothing. You don't know if anyone saw your report, who's responsible, or what to do next. That's the reality for thousands of Londoners every month." Use the FixMyStreet data to back up the numbers — we analysed 2,374 real reports.

**On screen:** Stat cards showing 30-day median, 12K/month volume. Optional: screenshot of a real FixMyStreet report that went unresolved.

---

## Slide 3: The Solution

**Title:** A 5-Agent Pipeline That Does the Work For You

**Key points:**
- Intake Agent: classifies issue into 18 categories with subcategories
- Severity Agent: scores 1-10 using hazard keywords, proximity to schools/hospitals, and location
- Routing Agent: identifies the correct council, department, and TfL vs borough responsibility
- Submission Agent: generates a formal, council-ready report
- Escalation Agent: 3-stage escalation path if the council doesn't act

**Speaker notes:**
Walk through the pipeline end-to-end: "You describe a problem in plain English. Our agents classify it, score its urgency, route it to exactly the right council department, draft a professional submission, and — if the council ignores it — escalate through formal complaints all the way to the Local Government Ombudsman." Emphasise that each agent is specialised and the pipeline is deterministic except for the LLM calls, which are parsed robustly.

**On screen:** Architecture diagram showing the 5-agent pipeline as a flow: User Input -> Intake -> Severity -> Routing -> Submission -> (Escalation). Arrows between agents, with data flowing left to right.

---

## Slide 4: Live Demo — Fly-Tipping Scenario

**Title:** Demo: Illegal Dumping Near a School

**Key points:**
- Input: "Someone dumped a mattress and bin bags on Vallance Road, near a primary school. It's been there 3 days and attracting rats."
- Show classification: Waste and Fly-Tipping / Fly-Tipping
- Show severity: 7/10 (school proximity boost, health hazard keywords)
- Show routing: Tower Hamlets -> Waste and Environmental Services
- Show generated submission text

**Speaker notes:**
Run the actual CLI or web UI live. Narrate each agent's output as it appears. Point out: "Notice the severity got boosted because we detected it's near a school — that's the proximity engine using real OpenStreetMap data, not the LLM guessing." Show the submission text and point out it's council-ready — formal language, all fields populated, map reference included.

**On screen:** Terminal or web UI showing the pipeline running in real time. Highlight the severity justification and the submission text.

---

## Slide 5: Live Demo — Pothole on TfL Road

**Title:** Demo: Pothole on the A205 South Circular

**Key points:**
- Input: pothole on A205, deep, dangerous for cyclists, rain-filled
- Show TfL detection: "A205" and "South Circular" trigger TfL routing, not borough council
- Show routing: Transport for London (TfL) -> TfL Highways
- Show severity: high score due to busy road, cyclist danger, visibility hazard
- Show live disruption data integration (TfL API)

**Speaker notes:**
This demo shows the routing intelligence. "Most citizens would report this to Lambeth Council. But the A205 is a TfL-managed road — Lambeth can't fix it. Our routing agent knows the difference. It detects TfL road references, red routes, and A-roads, and routes directly to TfL Highways." If time permits, show the TfL live disruption data overlay.

**On screen:** Map showing the A205 route with the report location pinned. Side panel showing the routing decision and TfL department assignment.

---

## Slide 6: Borough Leaderboard

**Title:** Public Accountability: Borough Performance Dashboard

**Key points:**
- Aggregated resolution times by borough
- Category breakdown per council (which issues each borough is slow on)
- Comparison across 33 London boroughs
- Data-driven: built from 2,374 real FixMyStreet reports
- Public transparency drives faster resolution

**Speaker notes:**
"Accountability is the missing piece. When citizens can see that Camden fixes potholes in 5 days but Hackney takes 45, that creates public pressure. Our dashboard aggregates real report data into a leaderboard." Show the dashboard — sort by resolution time, filter by category. Point out which boroughs are performing well and which are lagging.

**On screen:** Dashboard UI showing the borough leaderboard table. Bar charts of resolution time by category. Toggle between boroughs.

---

## Slide 7: Escalation Path

**Title:** When Councils Don't Act: 3-Stage Escalation

**Key points:**
- Stage 1 — Follow-up: automated phone script and follow-up letter template after 14 days
- Stage 2 — Formal complaint: generates a formal complaint letter citing council obligations under the Highways Act / Environmental Protection Act
- Stage 3 — LGO/MP referral: drafts a complaint to the Local Government Ombudsman or the citizen's MP
- Each stage includes specific legal references and deadlines
- The agent tracks days-open and triggers escalation automatically

**Speaker notes:**
"Most people give up after the first report. Our escalation agent doesn't. After 14 days with no response, it generates a follow-up. After 28 days, a formal complaint. After 42 days, it drafts a referral to the Local Government Ombudsman or the citizen's MP. Each letter cites the specific legislation the council is failing to uphold." Walk through the 3-stage visual. Emphasise this is where real impact happens.

**On screen:** Visual timeline showing the 3 escalation stages with day markers (14, 28, 42). Example escalation letter on the right side.

---

## Slide 8: Data Foundation

**Title:** Built on Real London Data

**Key points:**
- 2,374 real civic reports scraped from FixMyStreet (London only)
- 39,961 RAG chunks indexed for retrieval
- 6 integrated datasets: FixMyStreet reports, borough boundaries, council contact info, TfL road network, issue taxonomy (18 categories), OpenStreetMap POIs
- Issue taxonomy with 18 top-level categories and 60+ subcategories
- Every report is a real Londoner's complaint — real language, real locations

**Speaker notes:**
"This isn't synthetic data. We scraped 2,374 real reports from FixMyStreet London, built a taxonomy of 18 categories with 60+ subcategories based on actual council structures, and indexed 39,961 chunks for RAG retrieval. The routing engine uses real borough boundary polygons and the TfL road network. When we say 'Vallance Road, Tower Hamlets' — that's a real reverse geocode, not a guess."

**On screen:** Infographic with the data numbers. Small map of London with report locations dotted. Category taxonomy tree.

---

## Slide 9: Architecture

**Title:** Technical Architecture

**Key points:**
- NVIDIA DGX Spark as the compute platform
- Llama 3.3 70B via NIM (NVIDIA Inference Microservices)
- NeMo guardrails for input/output safety
- RAG pipeline: text chunking -> embedding -> FAISS index -> retrieval
- Robust LLM parser: handles JSON, markdown, verbose output, numbered lists, fuzzy matching
- 65 parser unit tests + 40 pipeline integration tests

**Speaker notes:**
"Under the hood: Llama 3.3 70B running on DGX Spark through NIM. NeMo guardrails prevent off-topic or harmful outputs. The RAG pipeline indexes 39K chunks for contextual retrieval. And because real LLMs produce messy output — JSON sometimes, markdown sometimes, verbose explanations sometimes — we built a robust parser layer with 65 unit tests covering every format we've seen." Briefly touch on the parser strategies: exact match, prefix stripping, contains match, JSON extraction, fuzzy word-overlap.

**On screen:** Architecture diagram: User -> NeMo Guardrails -> 5-Agent Pipeline -> LLM (Llama 3.3 70B via NIM) -> RAG (FAISS) -> Output. DGX Spark box around the compute layer.

---

## Slide 10: Impact

**Title:** Why This Matters

**Key points:**
- Faster resolution: correct routing means issues reach the right team on day 1, not day 15
- Public accountability: borough leaderboard creates transparency and competitive pressure
- Citizen empowerment: anyone can file a professional, legally-informed complaint
- Accessibility: plain English input, no knowledge of council structures required
- Scalable: works for any London borough, any issue category

**Speaker notes:**
"The impact is threefold. First, faster resolution — because the report goes to the right department immediately, not bouncing between desks. Second, public accountability — the leaderboard means councils can't hide poor performance. Third, citizen empowerment — a pensioner in Tower Hamlets can now file a complaint as professionally as a solicitor in Westminster." End with a real anecdote from the FixMyStreet data if time allows.

**On screen:** Three impact pillars as large icons: Speed (clock), Accountability (leaderboard), Empowerment (raised hand). Key metric: "Right department on day 1."

---

## Slide 11: What's Next

**Title:** Roadmap

**Key points:**
- Mobile app: photo-first reporting with GPS, submit in 30 seconds
- London-wide deployment: cover all 33 boroughs with live data feeds
- Council system integration: direct API connections to council CRM systems (e.g., Confirm, Salesforce)
- Multi-language support: 50+ languages spoken in London — LLM-powered translation
- Open data: publish aggregated resolution data as open datasets for researchers and journalists

**Speaker notes:**
"We've built the foundation. Next: a mobile app where you snap a photo and the agent does the rest in 30 seconds. Integration with council CRM systems so reports land directly in their workflow. Multi-language support for London's 50+ language communities. And open data publication — because sunlight is the best disinfectant." Close with: "London Civic Agent: AI that fights for your neighbourhood. Thank you."

**On screen:** Roadmap timeline showing Q3 2026 through Q1 2027 milestones. Mobile app mockup on the right. "Thank you" with contact info.
