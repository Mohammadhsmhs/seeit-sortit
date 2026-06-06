# Agent 04 — Submission

> Owner: **Ongun**. Time budget: **75 min** (14:15–15:30 Saturday).
> Hands off to: escalation agent (via the CRM — the new ticket lands in `processed_issues` and the watcher sees it).

---

## What it does

Take a routed issue. Submit it through the channel routing chose. Capture the council's response. Persist everything.

```
INPUT
  CivicIssue (with submission_channel, submission_endpoint, submission_metadata, etc.)

OUTPUT
  CivicIssue (mutated)
    - submission_status: "submitted" | "failed" | "queued"
    - submission_ref: str | None         # council's ticket ID if returned
    - submission_response: str           # raw response body, truncated
    - submitted_at: datetime
```

---

## Channel dispatch

```python
match issue.submission_channel:
    case "open311":           submit_open311(issue)
    case "love_clean_streets": submit_lcs(issue)   # cut for hackathon — falls through to email
    case "form":              submit_form(issue)   # Playwright — cut to email if no time
    case "email":             submit_email(issue)
    case _:                   submit_email(issue)  # safe default
```

---

## Open311 (the demo path)

### Payload — Camden verified live

```
POST https://fixmystreet.camden.gov.uk/open311/v2/requests.xml
Content-Type: application/x-www-form-urlencoded

jurisdiction_id=camden.gov.uk
service_code=POTHOLE                # from routing_table service_code
lat=51.5390
long=-0.1426
description=Pile of dumped mattresses outside Osmani Primary School. Reported by Sorted on behalf of resident.
email=sorted-hackathon@<our-domain>
phone=
first_name=Sorted
last_name=Agent
media_url=                          # optional. We omit for privacy story.
```

### Python implementation

```python
import requests, time

def submit_open311(issue):
    payload = {
        "jurisdiction_id": _jurisdiction_from_endpoint(issue.submission_endpoint),
        "service_code": issue.submission_metadata.get("service_code", "OTHER"),
        "lat": issue.latitude,
        "long": issue.longitude,
        "description": _format_description(issue),
        "email": SUBMIT_EMAIL,
        "first_name": "Sorted",
        "last_name": "Agent",
    }
    r = requests.post(issue.submission_endpoint, data=payload, timeout=15)
    if r.status_code == 200 or r.status_code == 201:
        ref = _extract_ref(r.text)  # parse XML <token>X</token>
        return SubmissionResult(status="submitted", ref=ref, response=r.text[:500])
    return SubmissionResult(status="failed", ref=None, response=f"{r.status_code} {r.text[:500]}")
```

### Description format (locked)

```
[Sorted — auto-submission on behalf of a resident]

Category: {category}
Severity: {severity_score}/10 — {one_line_rationale}
Location: {address or lat,lon}

What was reported: {voice_transcript or photo_description}

Severity grounded in: {top 2 citations}

Submitted at {timestamp}. Sorted agent reference: BB-{hash8}.
```

Including "Sorted — auto-submission on behalf of a resident" is required for the AI disclosure ethics line. **Do not strip it.**

### Endpoint mapping (the four we care about)

| Borough | Endpoint | jurisdiction_id |
|---------|----------|-----------------|
| Camden | `https://fixmystreet.camden.gov.uk/open311/v2/requests.xml` | `camden.gov.uk` ✅ verified live |
| Hackney | `https://reportaproblem.hackney.gov.uk/open311/v2/requests.xml` | `hackney.gov.uk` (high confidence — same Pro pattern) |
| Southwark | `https://report.southwark.gov.uk/open311/v2/requests.xml` | `southwark.gov.uk` (high confidence) |
| Islington | `https://fix.islington.gov.uk/open311/v2/requests.xml` | `islington.gov.uk` (high confidence) |

---

## Demo-borough special handling

Per `decisions-locked.md`: the **routing decision** is honest (Tower Hamlets → form channel), but the **actual API call** in the live demo goes to Camden's Open311.

```python
# Orchestrator (NOT the submission agent itself)
if os.getenv("DEMO_MODE") == "1" and issue.borough == "Tower Hamlets":
    issue.demo_actual_target = "Camden"
    issue.submission_endpoint = CAMDEN_OPEN311
    issue.submission_metadata = {"service_code": "FLYTIP"}
    issue.submission_channel = "open311"
```

The dashboard ticket drawer shows BOTH: "Routed to: Tower Hamlets Waste & Env Services" and "Actually submitted to: Camden (sandbox)". README discloses this is for demo purposes only — production removes the special-case.

---

## Form fallback (Tower Hamlets, etc.) — CUT for hackathon

Playwright form-filling is ~3 hours of work. We **cut this** by default. If the routing decision is "form", we degrade to "email" with a note in the description: *"This council does not expose Open311. Sorted logged the submission and will follow up by email."*

The README acknowledges Playwright support is roadmap, not demo.

---

## Email fallback — minimal viable

```python
import smtplib
from email.message import EmailMessage

def submit_email(issue):
    msg = EmailMessage()
    msg["From"] = "sorted-civic-agent@<our-domain>"
    msg["To"] = issue.submission_endpoint
    msg["Subject"] = f"[Sorted] {issue.category} — {issue.address or 'reported location'}"
    msg.set_content(_format_description(issue))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return SubmissionResult(status="submitted", ref=None, response="email sent")
```

For the demo, the email target is `sorted-hackathon@<our-test-inbox>` so we can verify delivery.

---

## Cursor build prompt (paste at 14:15)

```
GOAL: Build the submission agent. Given a routed CivicIssue, submit through
the channel routing chose. Capture council response. Persist submission status.

CONSTRAINTS:
- File: src/agents/submission.py
- Dispatch by issue.submission_channel: "open311" | "email" | (others fall
  through to email)
- Open311 endpoint, jurisdiction_id, and service_code come from
  issue.submission_endpoint, issue.submission_metadata.
- POST with requests.post(...data=payload, timeout=15). Use form-encoded body.
- Parse XML response with regex (not full xml.etree — keep it simple):
  re.search(r"<token>([^<]+)</token>", r.text)
- Description format MUST start with the literal line
  "[Sorted — auto-submission on behalf of a resident]"
- Email fallback uses smtplib via SMTP_SSL to smtp.gmail.com:465
- Persist to processed_issues table: submission_status, submission_ref,
  submission_response (truncated to 500 chars), submitted_at.
- On any exception, set status="failed", capture exception text in
  submission_response. NEVER crash the orchestrator.

ACCEPTANCE:
- python -c "
   from src.agents.submission import SubmissionAgent
   from src.models.intake import CivicIssue
   issue = CivicIssue(
       latitude=51.5390, longitude=-0.1426,
       category='Waste and Fly-Tipping',
       photo_description='Pile of mattresses', voice_transcript='',
       photos=[], raw_voice_text='',
       borough='Camden', council='London Borough of Camden',
       department='Waste',
       submission_channel='open311',
       submission_endpoint='https://fixmystreet.camden.gov.uk/open311/v2/requests.xml',
       submission_metadata={'service_code': 'FLYTIP'},
   )
   r = SubmissionAgent().process(issue)
   assert r.submission_status in ('submitted','failed','queued')
   print(r.submission_status, r.submission_ref)
   "

CONTEXT:
- decisions-locked.md says Camden Open311 is the demo target. Form channel
  degrades to email (Playwright is out of scope).
- agents/routing-agent-spec.md shows the routing_table shape and how
  submission_endpoint / submission_metadata get populated.
- The Sorted disclosure line in the description is required for AI ethics.
```

---

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Open311 returns 422 | Missing required field | Inspect response body — usually service_code or jurisdiction_id wrong |
| 404 from Open311 | Endpoint changed | Pin that borough to email channel temporarily |
| SMTP auth fails | Gmail blocking | Use Gmail app-specific password, NOT the account password |
| Token parse returns None | Council returned plain text | OK — keep `submission_status="submitted"`, just no ref |
| Network timeout | Slow council CMS | 15-sec timeout; on timeout, status="queued", retry in 60s |

---

## Smoke test

```python
# tests/smoke_submission.py — uses a known Camden sandbox endpoint
# Will actually POST to Camden — only run during the demo or test windows.
```

Add a `DRY_RUN=1` env var that logs the request but doesn't POST. Use this for development. Disable for the live demo.

---

## Hand-off

The submission agent writes to `processed_issues`. The **escalation agent / Sorted Watcher** is polling that table every 30 seconds. When a new row appears with `submission_status="submitted"`, the Watcher starts the SLA clock on it. That's the hand-off — no direct call, just shared state.
