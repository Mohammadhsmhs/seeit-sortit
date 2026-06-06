# London Civic Agent
### AI-powered civic complaint resolution for London

---

## The Problem

Every month, over 12,000 civic complaints are filed on FixMyStreet in the UK. Potholes, fly-tipping, broken streetlights, blocked drains. Behind each report is a resident who noticed something wrong and took the time to act.

Most of those reports sit in a queue. Our analysis of 369 resolved reports across four London boroughs found:

- **Median resolution time: 30 days**
- **56% of issues take 1 to 3 months to resolve**
- **10% take over a year**
- Camden's median: 51 days. Islington's worst case: 10.8 years.

The system treats every report the same. A pothole on a quiet cul-de-sac gets the same priority as one on a busy A-road next to a hospital. A pile of dumped waste near a school waits in the same queue as a faded road marking. Residents have no visibility into progress, no escalation path, and no leverage.

## The Solution

London Civic Agent is a multi-agent AI system that acts on behalf of the resident. Photo in, voice note in -- and the agent handles everything: classify, rank, route, file, track, and escalate.

**What it does:**

1. **Intake** -- Photo + voice description parsed into a structured civic issue. Vision model identifies the problem; speech-to-text captures context.
2. **Severity Ranking** -- Not all issues are equal. The agent scores severity 1-10 using real London data: proximity to schools and hospitals, collision history on the road, population density, repeat-report hotspots.
3. **Smart Routing** -- The agent knows which roads are TfL-managed, which department handles which category, and which council is responsible based on coordinates. No more reports bouncing between authorities.
4. **Formal Submission** -- A detailed, evidence-backed report is generated and filed to the correct council portal or FixMyStreet API.
5. **Escalation** -- If the council does not respond within the SLA, the agent follows up. It calls the council by phone. If that fails, it drafts a complaint to the Local Government Ombudsman.
6. **Public Accountability** -- A borough leaderboard and dashboard makes resolution performance visible. Hackney resolves issues in 1.3 days. Camden takes 51. Transparency drives improvement.

## The Differentiator

The key innovation is **severity ranking powered by real London open data**. Every report is scored against:

- **STATS19 collision history** -- roads with prior accidents get higher priority
- **School locations (GIAS)** -- issues near schools are flagged for children's safety
- **Hospital locations (NHS ODS)** -- dark streets near hospitals endanger staff on night shifts
- **Census 2021 population density** -- issues in high-density areas affect more people
- **DfT traffic volumes** -- busy roads mean higher impact from road defects
- **FixMyStreet historical data** -- repeat hotspots indicate systemic neglect

This is not a smarter form. It is an agent that knows things the resident does not.

## The Market

- **12,000+ reports/month** on FixMyStreet alone (UK-wide)
- **369 London borough councils** responsible for civic maintenance
- Potholes alone cost UK motorists an estimated **GBP 1 billion/year** in vehicle damage
- UK councils spent **GBP 1.1 billion** on highway maintenance in 2023-24
- Local Government Ombudsman received **17,000+ complaints** in 2023-24

The initial target is London's 33 boroughs. The model generalises to any UK council area, and the architecture adapts to any city with open civic data.

## The Technology

| Component | Technology | Why |
|-----------|-----------|-----|
| Reasoning / routing / drafting | Llama 3.3 70B (Q4) on DGX Spark | 35-45 tok/s, fully local inference, no data leaves device |
| Vision (photo intake) | Qwen2.5-VL-7B or Llama 4 Scout | Small enough to coexist with main model on 128GB unified memory |
| Speech-to-text | ElevenLabs Scribe | 99 languages -- serves London's multilingual population |
| Phone escalation | ElevenLabs Conversational AI + Twilio | Outbound calls with IVR navigation via DTMF |
| RAG corpus | TensorRT-LLM + local vector store | Pre-loaded London open data for severity enrichment |
| Orchestration | NeMo Agent Toolkit | Multi-agent pipeline with observability |
| Dashboard | Flask + real FixMyStreet data | Borough leaderboard, map view, resolution metrics |

**All LLM inference runs on the NVIDIA DGX Spark.** No civic data leaves the hardware. This is critical for a system handling residents' reports about their neighbourhoods.

## Impact

**For residents:**
- Report an issue in 30 seconds with a photo and voice note
- AI handles classification, routing, and follow-up
- No more wondering which council department to contact
- Automatic escalation when issues are ignored

**For councils:**
- Better-triaged reports with severity context and evidence
- Reduced mis-routing between departments and authorities
- Data-driven visibility into resolution performance

**For communities:**
- Public accountability via borough leaderboard
- Repeat hotspot detection highlights systemic neglect
- Every resident gets the same quality of advocacy, regardless of how well they know the system

---

*London Civic Agent -- because every citizen should have an AI agent advocating for their neighbourhood.*
