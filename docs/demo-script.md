# Demo Script -- London Civic Agent
## NVIDIA Hack for Impact London | 5 minutes

---

### OPENING HOOK (0:00 -- 0:30)

**[Slide: "30 days." in large text]**

> "In London, the median time to resolve a civic complaint is 30 days. A pothole, a pile of dumped rubbish outside a school, a broken streetlight on a dark road near a hospital -- 30 days.
>
> Some issues take over a year. Camden's average is 51 days. Islington has reports open for over 10 years.
>
> We scraped 369 resolved reports from FixMyStreet across four London boroughs. The data is real. The problem is real.
>
> What if every citizen had an AI agent that could classify, rank, route, file, and escalate civic issues -- in seconds, not months?"

**[Transition: live terminal]**

---

### DEMO SCENARIO 1: Fly-Tipping (0:30 -- 2:00)

**Setup:** "Let me show you. A resident walks past a pile of dumped rubbish on Vallance Road in Tower Hamlets. They take a photo and leave a voice note."

**[Run scenario 1 -- fly-tipping]**

```
python -m src.demo.run_demo
```

**Talk through the output as it appears:**

1. **Intake Agent** -- "The vision model sees the photo: mattress, broken furniture, bin bags blocking the pavement. The voice transcription adds context -- near a primary school, been there three days, attracting rats. The intake agent classifies this as Waste and Fly-Tipping, subcategory Fly-Tipping."

2. **Severity Agent** -- "Here is where it gets interesting. The base score for fly-tipping is 4 out of 10. But the agent runs a proximity check against our RAG corpus of London open data -- schools, hospitals, collision history, population density. It finds a primary school within 300 metres. That bumps severity by 2 points. The description mentions 'dangerous' and 'children' -- two more hazard keywords. It checks our scraped FixMyStreet data and finds prior reports in the same area -- a repeat hotspot. Final score: 9 out of 10."

3. **Routing Agent** -- "The coordinates place this in Tower Hamlets. The agent maps category to department: Waste and Environmental Services. It knows this is not a TfL road, so it routes to the London Borough of Tower Hamlets directly."

4. **Submission Agent** -- "A formal report is generated with all evidence, severity justification, and exact coordinates. Ready to submit to the council portal or via the FixMyStreet API."

**Key point:** "That entire pipeline -- intake, severity, routing, submission -- ran on the DGX Spark. No cloud calls for the reasoning layer. Your data stays on-device."

---

### DEMO SCENARIO 2: Dangerous Pothole (2:00 -- 3:30)

**Setup:** "Second scenario. A driver reports a deep pothole on the A205 South Circular."

**[Scenario 2 runs automatically]**

**Talk through:**

1. **Intake** -- "Classified as Roads and Highways, subcategory Pothole. The description mentions 30cm across, 10cm deep, cyclists at risk."

2. **Severity** -- "Roads and Highways starts at base 6. Pothole subcategory adds 1. But watch: the text mentions 'A205' -- that is a major road. The agent detects hazard keywords: 'dangerous', 'busy road', 'urgent'. And the proximity check finds King's College Hospital within 800 metres. Final score: 10 out of 10. Maximum severity."

3. **Routing** -- "This is the critical difference. The agent detects 'A205' and 'South Circular' -- these match our TfL road keyword list. This is a red route. The report does not go to the local borough council. It routes to Transport for London, TfL Highways department. Without our system, a resident would file this with Lewisham Council, who would tell them it is TfL's responsibility, and the report would bounce for weeks."

4. **Submission** -- "The formal report goes to TfL with collision data context and severity justification built in."

**Key point:** "The system knows things the resident does not. It knows which roads are TfL-managed. It knows the collision history. It knows there is a hospital nearby. This is not a form -- it is an agent."

---

### DEMO SCENARIO 3: Phone Escalation (3:30 -- 4:30)

**Setup:** "What happens when the council does not respond? Scenario 3 -- a broken streetlight on Lambeth Palace Road near St Thomas' Hospital. Reported two weeks ago. Nothing done."

**[Scenario 3 runs -- show classification and severity]**

**Talk through the classification and routing (brief):**

> "Street Lighting and Traffic. Severity 10 -- near a hospital, described as unsafe, repeat issue. Routed to Lambeth Council."

**[Show escalation path -- either live phone demo or recorded fallback]**

> "Now the escalation layer. The report is filed. A 7-day SLA timer starts. If no acknowledgement, the agent escalates. It calls the council on the resident's behalf using ElevenLabs Conversational AI and Twilio."

**[Play audio or describe the call flow]**

> "The agent introduces itself, provides the reference number, describes the issue, requests a timeline. If the call connects to an IVR, it navigates the menu using DTMF tones. If it reaches a human, it hands off context and records the outcome."

> "If the phone call does not resolve it, the next escalation tier generates a formal complaint letter to the Local Government Ombudsman, with all evidence and timeline attached."

**Key point:** "This is the full loop. Report, classify, rank, route, file, follow up, call, escalate. The resident does nothing except take a photo and say what they see."

---

### DASHBOARD REVEAL (4:30 -- 5:00)

**[Switch to browser -- dashboard at localhost:5050]**

> "All of this feeds into a public accountability dashboard."

**Show:**

1. **Borough Leaderboard** -- "Hackney resolves issues in a median of 1.3 days. Camden takes 51. These are real numbers from our scraped data. Public accountability changes behaviour."

2. **Map view** -- "Every report is geolocated. You can see the hotspots -- clusters of fly-tipping, corridors of potholes."

3. **Resolution metrics** -- "56% of issues take 1 to 3 months. 10% take over a year. The dashboard makes this visible."

---

### TECHNICAL DEEP-DIVE (5:00 -- 5:20)

**[Slide: architecture diagram]**

> "Under the hood: four agents -- Intake, Severity, Routing, Submission -- orchestrated through a pipeline running on NVIDIA DGX Spark. Llama 3.3 70B quantized to Q4, running at 35 to 45 tokens per second locally. RAG over London open data: STATS19 collision history, DfT traffic volumes, school locations from GIAS, hospitals from NHS ODS, Census 2021 population density. Vision model for photo intake. ElevenLabs Scribe for voice transcription. Twilio for outbound calls. All reasoning stays on-device -- no civic data leaves the hardware."

---

### CLOSE (5:20 -- 5:30)

> "12,000 civic reports are filed on FixMyStreet every month in the UK alone. Behind every one is a person who took time out of their day to say something is wrong. Most of those reports sit in a queue for 30 days. Some for a year. Some forever.
>
> We believe every citizen should have an AI agent advocating for their neighbourhood. Not a form. Not a portal. An agent that knows the data, knows the system, and does not give up.
>
> London Civic Agent. Thank you."

---

## BACKUP PLANS

| Risk | Mitigation |
|------|------------|
| Live phone demo fails | Pre-recorded audio clip of successful call, rehearsed |
| DGX Spark model loading slow | Pre-warm model before demo; mock provider as instant fallback |
| Dashboard DB missing | Static screenshot backup slides |
| Network issues | All LLM inference is local; dashboard runs on localhost |

## PRESENTER NOTES

- Rehearse the terminal demo until the talking points sync naturally with output appearance
- Have the dashboard open in a browser tab before starting
- Keep the architecture slide simple -- one diagram, no bullet points
- The emotional arc is: problem (frustration) -> demo (wow, it works) -> vision (this could help everyone)
- If a judge asks about accuracy: "Our mock mode uses keyword matching. With Llama 3.3 70B on the Spark, we get LLM-quality classification. The severity scoring is rule-based with RAG enrichment -- deterministic and auditable."
- If a judge asks about privacy: "Photos are processed by the vision model on-device. The description is sent to the council, not the photo. No civic data leaves the DGX Spark."
