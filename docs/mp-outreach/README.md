# MP Outreach

Research and assets for the "Contact your MP" feature and the hackathon outreach campaign.

## Contents
- `mps-research.md` — Findings, data sources, priority targets
- `fetch_mps.py` — Script to pull the full 75 London MPs from the UK Parliament API
- `london_mps.json` — Generated dataset (run the script to populate)
- `outreach-email.md` — Email draft to send to London MPs
- `priority-targets.md` — Shortlist of MPs to prioritise for cold outreach

## Why
1. **Product feature**: when an SLA is breached or escalation is needed, the agent can draft a formal letter to the resident's MP. This requires a postcode → constituency → MP lookup.
2. **Hackathon outreach**: emailing London MPs to gauge interest in piloting the platform in their constituency, or backing the project.

## Sources
- UK Parliament Members API: https://members-api.parliament.uk/index.html (no auth)
- ONS Open Geography Portal (constituency ↔ borough lookup): https://geoportal.statistics.gov.uk
- Wikipedia (Parliamentary constituencies in London) — used as cross-reference only
