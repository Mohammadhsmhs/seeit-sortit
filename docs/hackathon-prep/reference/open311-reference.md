# Open311 Reference — London Boroughs

> Quick-look reference for the submission agent. Spec is **Open311 GeoReport v2**: https://wiki.open311.org/GeoReport_v2/.
>
> mySociety's FixMyStreet Pro deployment pattern: every borough running it exposes Open311 at the same path shape — `{base}/open311/v2/`.

---

## Endpoints (4 boroughs)

| Borough | Base URL | jurisdiction_id | Status |
|---------|----------|-----------------|--------|
| **Camden** | `https://fixmystreet.camden.gov.uk/open311/v2/` | `camden.gov.uk` | ✅ **VERIFIED LIVE** (research call, Saturday) |
| **Hackney** | `https://reportaproblem.hackney.gov.uk/open311/v2/` | `hackney.gov.uk` | High confidence — same Pro pattern |
| **Southwark** | `https://report.southwark.gov.uk/open311/v2/` | `southwark.gov.uk` | High confidence — same Pro pattern |
| **Islington** | `https://fix.islington.gov.uk/open311/v2/` | `islington.gov.uk` | High confidence — same Pro pattern |

Boroughs NOT on Open311 (so submission agent routes them to form / email):
- Tower Hamlets, Kensington and Chelsea, Havering, City of London Corporation, Westminster (explicitly disabled FMS integration)

---

## Endpoints (each base + path)

| Path | Purpose | Method | Auth |
|------|---------|--------|------|
| `services.xml` (or `.json`) | List all available service codes | GET | none |
| `services/{service_code}.xml` | Get one service's details | GET | none |
| `requests.xml` (or `.json`) | Submit a new report | POST | none (email field instead) |
| `requests/{token}.xml` | Look up a submitted report | GET | none |

---

## Discover service codes — do this FIRST Saturday morning

For each target borough, list its services so you know which `service_code` to send:

```bash
curl -s "https://fixmystreet.camden.gov.uk/open311/v2/services.xml?jurisdiction_id=camden.gov.uk" | head -100
```

You'll get XML like:

```xml
<services>
  <service>
    <service_code>POTHOLE</service_code>
    <service_name>Pothole</service_name>
    <description>...</description>
    <metadata>false</metadata>
    <type>realtime</type>
    <keywords>road,highway,pothole</keywords>
    <group>Highways</group>
  </service>
  <service>
    <service_code>FLYTIP</service_code>
    <service_name>Fly-tipping</service_name>
    ...
  </service>
  ...
</services>
```

Camden has 500+ service codes. Map our 18 taxonomy categories to the 18 most-relevant ones and store in `routing_table.json` per `agents/routing-agent-spec.md`.

---

## Submit a report — Camden verified

### Sample request (the actual demo POST)

```bash
curl -X POST "https://fixmystreet.camden.gov.uk/open311/v2/requests.xml" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "jurisdiction_id=camden.gov.uk" \
  --data-urlencode "service_code=FLYTIP" \
  --data-urlencode "lat=51.5390" \
  --data-urlencode "long=-0.1426" \
  --data-urlencode "description=[Sorted — auto-submission on behalf of a resident]

Category: Waste and Fly-Tipping
Severity: 9/10 — near Osmani Primary School, high collision area
Location: Vallance Road, London

What was reported: Pile of dumped mattresses outside the school

Submitted at 2026-06-07T15:30:00Z. Sorted agent reference: BB-a3f2c1." \
  --data-urlencode "email=sorted-hackathon@<our-domain>" \
  --data-urlencode "first_name=Sorted" \
  --data-urlencode "last_name=Agent"
```

### Sample successful response (200)

```xml
<service_requests>
  <request>
    <service_request_id>1234567</service_request_id>
    <token>BBR-abcdef123</token>
    <service_notice>Your report has been received. Council ref: CMDN-2026-09876.</service_notice>
  </request>
</service_requests>
```

Both `service_request_id` and `token` are how we look up the report later. **Save `token` in our `submission_ref` column.**

### Sample error response (422)

```xml
<errors>
  <error>
    <code>422</code>
    <description>service_code unknown. See /open311/v2/services.xml</description>
  </error>
</errors>
```

Most common 422 reasons:
- `service_code` not in this borough's catalogue
- `lat`/`long` outside the borough's bounding box
- `email` missing (required even though no auth)
- `description` blank or under threshold

---

## Required fields (Camden, likely identical for the other 3)

| Field | Required | Notes |
|-------|----------|-------|
| `jurisdiction_id` | **yes** | Must match the URL hostname pattern |
| `service_code` | **yes** | From `services.xml` |
| `lat`, `long` | **yes** | WGS84, decimal degrees |
| `description` | **yes** | Min ~20 chars |
| `email` | **yes** | Anonymous works if email matches a known service-account |
| `first_name`, `last_name` | **yes** | Free text |
| `address_string` | optional | If you provide `lat`/`long`, address can be omitted |
| `media_url` | optional | URL of a public photo — we OMIT this for privacy |
| `phone` | optional | Skip |

---

## Rate limits

Per mySociety's published policy: **no formal rate limit**, but they ask for "polite usage." Our submission agent submits one report per pipeline run — far below any reasonable threshold. For the demo, we submit once.

For testing Saturday, **rate-limit ourselves to one submission per 30 seconds** to avoid flagging.

---

## Look up a submitted report

```bash
curl -s "https://fixmystreet.camden.gov.uk/open311/v2/requests/{token}.xml?jurisdiction_id=camden.gov.uk"
```

Returns the current status (open / in-progress / fixed / closed) and any council updates. Our watcher uses this to detect resolution.

---

## What's special about FixMyStreet Pro Open311

mySociety hosts the white-label deployment. Behind the scenes, the report lands in the council's CRM (Symology / Confirm / Jadu — varies by borough). The Open311 API is a thin polite-shim on top.

**Implication for our pitch:** even though Camden's URL has `fixmystreet` in it, the report DOES end up in the council's internal system. Not the public FixMyStreet site. Worth noting in Q&A if asked.

---

## Submission agent integration (per `agents/submission-agent-spec.md`)

The submission agent reads `routing_table.json`, finds the (borough, category) entry, gets the endpoint + service_code, builds the description with the disclosure prefix, POSTs, parses `<token>`, persists.

Owner-test: dry-run with `DRY_RUN=1` env var, then run live once Saturday afternoon to capture a real `service_request_id` for the dashboard demo state.

---

## What to log when a submission fails

- Full HTTP response body (truncated to 500 chars)
- Borough + service_code attempted
- `stage_errors` table gets the row
- Submission status set to `failed` — orchestrator continues to escalation

We never crash the orchestrator on submission failure. The recorded fallback covers the demo even when Open311 is down.
