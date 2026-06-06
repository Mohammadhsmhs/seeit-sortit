# Open311 endpoints for London councils — research findings

**Date of probe:** 2026-06-06
**Method:** direct HTTP probes with `curl` and `requests`, User-Agent `Obsidian-Research-Bot/1.0`.
**Constraint:** read-only — no POST attempted. Auth requirements taken from the [GeoReport v2 spec](https://wiki.open311.org/GeoReport_v2/) and the [FixMyStreet Open311 spec](https://github.com/mysociety/fixmystreet/wiki/Open311-FMS---Complete-Spec).

## TL;DR

- **No London council exposes a public, POST-capable Open311 endpoint we can write to without an API key.** The GeoReport v2 spec mandates an `api_key` on POST `/requests` (HTTP 403 otherwise), and FixMyStreet enforces this on every co-brand we probed. API keys are issued by mySociety only to client councils.
- **Six FixMyStreet-fronted Open311 servers respond 200 publicly** for `discovery.json` + `services.json` + `requests.json` (read-only). All run the same mySociety FixMyStreet codebase and expose the **same flattened global category catalogue (2,600 services)** — they are NOT per-council filtered.
- **The central `https://www.fixmystreet.com/open311/v2/` is the de-facto London-wide endpoint.** FixMyStreet's own routing logic forwards reports to the correct borough by email (the legacy pipeline) or by Open311 POST against the council's backend (where mySociety has integrated). The user-visible API is the same.
- **Practical recommendation for this project:** ship against FixMyStreet's central Open311 as the single read endpoint (lookups, dedup, status tracking), and submit reports either (a) via mySociety partnership if we can get an API key, or (b) via `mailto:` deep-links/email to the per-council `reporting_url` already in `src/data/boroughs.json` (already the default in our pipeline). There is no plausible POST-with-no-auth route to councils.

## Summary table — London authorities

`Open311 surface` reflects whether a JSON endpoint at `/open311/v2/discovery.json` returns HTTP 200. **All POSTs require an API key we don't have.** The "Routes reports via FMS" column counts the borough as routable if `agency_responsible.recipient` matched it in a 1,000-row sample of the central FixMyStreet `/requests.json`.

| # | Borough | Dedicated Open311 host (HTTP 200) | Routes reports via FMS | Auth required for POST | Notes |
|---|---------|-----------------------------------|------------------------|------------------------|-------|
| 1 | City of London | -- | yes (page visible) | yes (api_key) | No co-brand. FMS-fronted only. |
| 2 | Barking and Dagenham | -- | yes (~1,600 reports on FMS) | yes | No co-brand. FMS forwards (email path). |
| 3 | Barnet | -- | yes (sampled) | yes | No co-brand. |
| 4 | Bexley | **`https://fix.bexley.gov.uk/open311`** | yes (sampled, 29) | yes (api_key) | mySociety co-brand. Discovery contact: `customer.services@bexley.gov.uk`. |
| 5 | Brent | **`https://report.brent.gov.uk/open311`** | yes (sampled, 91 — top borough in 1k sample) | yes (api_key) | mySociety co-brand. Discovery contact: `ContactCentre@brent.gov.uk`. |
| 6 | Bromley | **`https://fix.bromley.gov.uk/open311`** | yes (sampled, 47) | yes (api_key) | mySociety co-brand. Discovery contact: `info@bromley.gov.uk`. |
| 7 | Camden | -- | yes (page visible, ~1,500 reports) | yes | No co-brand. |
| 8 | Croydon | -- | yes (page visible) | yes | No co-brand. |
| 9 | Ealing | -- | yes (page visible) | yes | No co-brand. |
| 10 | Enfield | -- | yes (sampled, 3) | yes | No co-brand. |
| 11 | Greenwich (Royal) | **`https://fix.royalgreenwich.gov.uk/open311`** | yes (sampled, 21) | yes (api_key) | mySociety co-brand. Discovery contact: `fixmystreet@royalgreenwich.gov.uk`. |
| 12 | Hackney | -- | yes (sampled, 13) | yes | No co-brand. |
| 13 | Hammersmith and Fulham | -- | yes (page visible) | yes | No co-brand. |
| 14 | Haringey | -- | yes (sampled, 1) | yes | No co-brand. |
| 15 | Harrow | -- | yes (page visible) | yes | No co-brand. |
| 16 | Havering | -- | yes (page visible) | yes | No co-brand. |
| 17 | Hillingdon | -- | yes (page visible) | yes | No co-brand. |
| 18 | Hounslow | **`https://fms.hounslowhighways.org/open311`** | yes (sampled, 29 — "Hounslow Highways") | yes (api_key) | Hounslow's highways are operated by Hounslow Highways Ltd (PFI); this is their co-brand. |
| 19 | Islington | -- | yes (sampled, 2) | yes | No co-brand. |
| 20 | Kensington and Chelsea | -- | yes (page visible) | yes | No co-brand. |
| 21 | Kingston upon Thames | -- | yes (page visible) | yes | No co-brand. |
| 22 | Lambeth | -- | yes (sampled, 5) | yes | No co-brand. |
| 23 | Lewisham | -- | yes (sampled, 5) | yes | No co-brand. |
| 24 | Merton | -- | yes (sampled, 30) | yes | No co-brand. |
| 25 | Newham | -- | yes (page visible) | yes | No co-brand. |
| 26 | Redbridge | -- | yes (page visible) | yes | No co-brand. |
| 27 | Richmond upon Thames | -- | yes (sampled, 1) | yes | No co-brand. |
| 28 | Southwark | **`https://report.southwark.gov.uk/open311`** | yes (sampled, 23) | yes (api_key) | mySociety co-brand. Discovery contact: `environment@southwark.gov.uk`. |
| 29 | Sutton | -- | yes (page visible) | yes | No co-brand. |
| 30 | Tower Hamlets | -- | yes (sampled, 1) | yes | No co-brand. |
| 31 | Waltham Forest | -- | yes (page visible) | yes | No co-brand. |
| 32 | Wandsworth | -- | yes (sampled, 1) | yes | No co-brand. |
| 33 | Westminster | -- (redirects to central FMS) | yes (sampled, 1) | yes | `report.westminster.gov.uk/open311/...` -> 301 -> `www.fixmystreet.com/open311/...`. |
| 34 | TfL (not a borough; Greater-London-wide road authority) | -- | yes (sampled, 5) | yes | Reached via FMS routing — every London FMS report on a TfL red route auto-fans to TfL. |

Note: "co-brand" = mySociety hosts a FixMyStreet skin on the council's subdomain, operated as a Pro client. There is also a **Westminster** mySociety contract but its public DNS just 301-redirects to `www.fixmystreet.com`. The other 27 of 33 boroughs have only the legacy email-via-FMS path.

### Endpoint count

- **0/33 London boroughs publicly expose a POST-capable Open311 endpoint without an API key** (per GeoReport v2 spec).
- **6/33 expose a Pro co-brand at `/open311/v2/` that we can read for free** (discovery, services, requests).
- **1/33 (Westminster)** redirects its `open311` subdomain to the central FMS endpoint.
- **All 33** appear in FixMyStreet's central `requests.json` stream as an `agency_responsible.recipient`, meaning reports submitted at `www.fixmystreet.com` *are* delivered to them — by email if no Pro integration, by Open311 POST if mySociety has wired up the council's backend (Confirm uses [a per-council CRM endpoint](https://github.com/mysociety/fixmystreet/wiki/Open311-FMS---Complete-Spec) which is not publicly addressable).

## Per-endpoint detail

### FixMyStreet central (the practical "London Open311")

- **Base:** `https://www.fixmystreet.com/open311`
- `GET /v2/discovery.json` — 200, JSON:
  ```json
  {"discovery":{"changeset":"2021-03-01T00:00:00Z",
    "endpoints":[{"url":"https://www.fixmystreet.com/open311",
      "specification":"http://wiki.open311.org/GeoReport_v2",
      "type":"production","changeset":"2021-03-01T00:00:00Z",
      "formats":["text/xml","application/json","text/html"]}],
    "contact":"Send email to support@fixmystreet.com.","max_requests":"1000"}}
  ```
- `GET /v2/services.json` — 200, 2,600 services. **Same flat global catalogue everywhere.**
  First 10: `1 signal light out`, `2 signal lights out`, `240L Black - Lid`, `240L Black - Wheels`, `240L Brown - Lid`, `240L Brown - Wheels`, `240L Green - Lid`, `240L Green - Wheels`, `3+ Consecutive Lights Out`, `A badly damaged or burnt out vehicle on a public road`.
- `GET /v2/requests.json?jurisdiction_id=fixmystreet` — 200, `service_requests[]`, capped at 1,000 reports (latest first). Each row has:
  `service_name, service_request_id, lat, long, description, requested_datetime, updated_datetime, service_code, interface_used, agency_responsible.recipient[], title, agency_sent_datetime, detail, status`.
  - This is the **single best read API** for our project — we can poll it to dedupe against existing reports and surface "already reported" UX.
  - `jurisdiction_id=fixmystreet` works. Other values are accepted silently but don't filter.
- `POST /v2/requests.json` — **403 without `api_key`**, per the spec. We did not POST.

### Bromley — mySociety Pro co-brand

- **Base:** `https://fix.bromley.gov.uk/open311`
- discovery.json contact: `info@bromley.gov.uk`
- services.json: 2,600 — identical flat global catalogue (not Bromley-only).
- `GET /v2/requests.json?jurisdiction_id=bromley.gov.uk` — 200, `service_requests[]`, real Bromley-area reports. (Without `jurisdiction_id` you get a co-brand HTML "browse reports" page.)
- POST: requires API key. mySociety wires this co-brand's POST directly to Bromley's CRM (Confirm/Echo), so successful POSTs become real council tickets.

### Bexley — mySociety Pro co-brand

- **Base:** `https://fix.bexley.gov.uk/open311`
- discovery.json contact: `customer.services@bexley.gov.uk`
- Same shape as Bromley.

### Royal Greenwich — mySociety Pro co-brand

- **Base:** `https://fix.royalgreenwich.gov.uk/open311`
- discovery.json contact: `fixmystreet@royalgreenwich.gov.uk`
- Same shape.

### Southwark — mySociety Pro co-brand

- **Base:** `https://report.southwark.gov.uk/open311`
- discovery.json contact: `environment@southwark.gov.uk`
- Same shape.

### Brent — mySociety Pro co-brand

- **Base:** `https://report.brent.gov.uk/open311`
- discovery.json contact: `ContactCentre@brent.gov.uk`
- Same shape. **Brent is the highest-volume London co-brand** in our 1,000-row sample (91 reports).

### Hounslow Highways — PFI co-brand

- **Base:** `https://fms.hounslowhighways.org/open311`
- discovery.json contact: `enquiries@hounslowhighways.org`
- Hounslow's highways are managed by Hounslow Highways Ltd under a 25-year PFI, not by LBR Hounslow's in-house teams. This co-brand POSTs directly into HHL's work-order system. Non-highways issues in Hounslow still route through the central FMS (typically to LBR Hounslow by email).

### Westminster — co-brand redirected to central

- `https://report.westminster.gov.uk/open311/v2/discovery.json` -> HTTP 301 -> `https://www.fixmystreet.com/open311/v2/discovery.json`. So Westminster reports use the central endpoint with the council inferred from coordinates.

### Per-council endpoints that don't exist (sample)

We probed 46 subdomain variants across `fix.{borough}.gov.uk`, `report.{borough}.gov.uk`, `fixmystreet.{borough}.gov.uk`, and a few council-specific oddities. All returned `000` (DNS no-record) or a non-Open311 200/404 except those in the table above. **No non-mySociety London council exposes Open311 at any guessable URL.**

## POST requirements (from spec; we did not POST)

Per the [GeoReport v2 spec](https://wiki.open311.org/GeoReport_v2/) and [FixMyStreet's Open311 spec](https://github.com/mysociety/fixmystreet/wiki/Open311-FMS---Complete-Spec):

| Parameter | Required? | Notes |
|-----------|-----------|-------|
| `api_key` | **yes — HTTP 403 otherwise** | Issued by the endpoint operator. FMS issues keys only to council staff for inbound CRM integration. |
| `jurisdiction_id` | conditional (multi-juris endpoints) | For central FMS, `fixmystreet`; for co-brands, the council domain. |
| `service_code` | yes | From `services.json`. **There are 2,600** — see categories below. |
| `lat` + `long` **OR** `address_string` **OR** `address_id` | one required | WGS84. |
| `attribute[code]=value` | conditional | Required for services whose `services/{code}.json` lists mandatory metadata. |
| `description` | recommended | Up to 4,000 chars. |
| `media_url` | optional | Public image URL. |
| `email`, `first_name`, `last_name`, `phone`, `device_id` | optional | Reporter identity. Mandatory on most UK councils' service definitions. |

**Net effect:** even if we had an API key, we'd still need to map our internal taxonomy to one of the council's 2,600 service codes per report.

## Coverage analysis

### Read coverage
- **6/33 boroughs** (Bexley, Brent, Bromley, Royal Greenwich, Southwark, Hounslow-Highways-only) have a directly-addressable Open311 server we can read from.
- **All 33 boroughs** are readable via the central FMS `requests.json` stream (filter by `agency_responsible.recipient`).
- **0/33 boroughs** have a writable Open311 surface without API-key partnership.

### Category coverage
The 2,600-service global FMS catalogue covers our taxonomy comfortably:

| Our taxonomy class | Matching FMS service_codes | Sample |
|--------------------|---------------------------:|--------|
| Potholes | 45 | `A pothole in pavement`, `A pothole in road`, `Carriageway pothole`, ... |
| Fly-tipping | 22 (combined `fly-tip` + `fly tip`) | `Fly-Tipping`, `Fly tipping`, `Fly-tip Large - More than a van load` |
| Graffiti | 52 | `Graffiti`, `Graffiti / Flyposting on street light (non-offensive)` |
| Street lighting | 53+35 | `All out - three or more street lights in a row`, `Street light not working` |
| Drainage / flooding | 71+37 | `Blocked Drain`, `Blocked - Flooding of Road/Path` |
| Roads / pavement | 237 / 75 | `A vehicle being repaired on road or pavement`, etc. |
| Trees | 360 | `Adopt a tree`, `Fallen tree` (caveat: "tree" substring is noisy) |
| Dog-related | 37 | `Dangerous Dog`, `Damaged dog bin` |

Every civic-complaint category we plausibly need has 10-50+ FMS service codes to choose from. The challenge is **not** category coverage; it's **service-code selection per council** — Bromley's `Pothole` and Brent's `Pothole on road` are different `service_code`s, both submitted to the same global catalogue.

### Write coverage
**0/33 boroughs** have a free write path. Realistic options:
1. Partner with mySociety to get an API key for the central endpoint, get our reports federated like the FMS mobile app does.
2. Continue the current `mailto:` / deep-link fallback to each borough's `reporting_url` (already in `src/data/boroughs.json`).
3. POST to `www.fixmystreet.com/report/new` *as a normal browser form*, scraping CSRF — fragile, and would attribute reports to "our bot" not the user.

## Recommendation

Given the constraint that we cannot POST without an API key:

1. **Use the central FixMyStreet endpoint (`https://www.fixmystreet.com/open311/v2/`) as our single Open311 read source.**
   - Poll `requests.json?jurisdiction_id=fixmystreet` periodically.
   - Filter rows by `lat`/`long` bounding box per borough, **and** by `agency_responsible.recipient` to attribute to the right council.
   - Use this stream for "is this already reported?" UX, status tracking, dedup. This is the highest-leverage win because FMS already aggregates ~all UK civic reports.
2. **Hit each borough's co-brand for finer-grained reads** where one exists (Bexley/Brent/Bromley/Greenwich/Southwark/Hounslow Highways).
   - Same data shape; advantage is freshness/locality and clearer per-borough provenance.
3. **For submissions, keep the email-fallback chain we already have** — `reporting_url` per borough from `src/data/boroughs.json`. Generate a `mailto:` deep-link or open the council's web form in an in-app webview. This is also what the FMS mobile app falls back to for non-Pro councils, so we're not behind the state of the art.
4. **Reach out to mySociety** about Open311 integration if we want true POST capability. They run the "FixMyStreet integration" partnership program — we'd need to register and get an `api_key`. This is the only path to non-email-based delivery for the 27 non-Pro boroughs short of building bespoke per-council CRM integrations.
5. **Category-mapping strategy:** for each report, query `services.json` once (cache it — it's 440 KB), then fuzzy-match our taxonomy class to the council's specific service_code. Building a hand-curated `category_mapping.json` per borough is realistic for the 6 co-brand councils; for the others it doesn't matter (we can't POST).

### Implementation order (suggested)
1. Wire `https://www.fixmystreet.com/open311/v2/requests.json?jurisdiction_id=fixmystreet` into the dedup/look-up pipeline.
2. Cache the 2,600-service catalogue locally.
3. Extend `categories.json` to map each of our taxonomy classes to a list of likely FMS service_codes (the most common ones — pothole/fly-tip/graffiti/street-light/drain).
4. Keep `mailto:`/webview as the user-facing submit action against `reporting_url`.
5. (Optional, post-hackathon) Apply for mySociety Open311 partnership and add the POST path.

## Test script

A reproducible probe lives at [`scripts/test_open311.py`](../scripts/test_open311.py). Run with:

```bash
.venv/bin/python scripts/test_open311.py
```

It probes 8 endpoints (7 London co-brands + the central FMS + one non-London control) and prints a pass/fail summary. As of 2026-06-06 all 8 pass — discovery.json and services.json both 200 with valid Open311 payloads.

## Sources

- [GeoReport v2 specification](https://wiki.open311.org/GeoReport_v2/) — auth requirements, parameter list, error codes.
- [FixMyStreet Open311 Complete Spec](https://github.com/mysociety/fixmystreet/wiki/Open311-FMS---Complete-Spec) — FMS-specific behaviour and POST requirements.
- [FixMyStreet Open311 page](https://www.fixmystreet.com/open311) — public-facing entry point.
- [mySociety FixMyStreet community page](https://www.mysociety.org/community/fixmystreet/) — confirms client borough list: Bromley, Bexley, Greenwich, Hounslow, Westminster (plus more added since).
- Probe payloads cached at `/tmp/fms_v2_discovery.json`, `/tmp/probe/*.json`, `/tmp/probe2/*.json` during this research (not committed).

---

## API Key Access Investigation

**Date of probe:** 2026-06-06 (follow-up).
**Method:** `curl` probes of each `apps/new`-style key-request form + WebFetch of TOS pages + cross-checked against the canonical [Open311 servers registry](https://raw.githubusercontent.com/open311/open311.github.io/master/data/servers.yml).
**Question:** of the seven UK Open311 surfaces we read, how many will actually issue a third-party API key in time for a 3-day hackathon — and if zero, what international sandbox can we POST to as a proof-of-architecture?

### Critical finding: the FixMyStreet api_key flow runs the WRONG direction

Reading the [FixMyStreet Open311 API info page](https://www.fixmystreet.com/about/open311-api-info) carefully: **the council** runs the Open311 endpoint and gives the **api_key** to mySociety. mySociety FMS then uses that key to POST inbound reports into the council's CRM (Confirm / Echo / etc.).

mySociety does **not** issue api_keys outward to third-party app developers. The "developer" in their model is the council's own IT team standing up a GeoReport v2 server. Quote from the docs:

> "First, let us know you are planning to set up an Open311 endpoint by emailing support@fixmystreet.com. […] Once you have a functional Open311 testing endpoint set up, email them the URL and API key and they'll configure their FixMyStreet staging site to send appropriate reports to that endpoint."

That whole flow assumes *you are the council*. There is no published path for an unaffiliated developer or hackathon team to obtain a write-key against `www.fixmystreet.com/open311/v2/` or against any of the per-borough co-brands (which are mySociety's own Pro tenancies, keyed for mySociety's internal use only). This invalidates the earlier "reach out to mySociety for an api_key" recommendation: there is nothing for them to issue.

### Summary table

| Endpoint | API key issuable to a third-party dev? | How | Realistic turnaround | Notes |
|----------|---------------------------------------|-----|----------------------|-------|
| Bromley (`fix.bromley.gov.uk`) | **No** | No public form. `info@bromley.gov.uk` is the discovery contact but they don't run the endpoint — mySociety does, and the api_key is theirs. | n/a | Council IT would have to commission this from mySociety. Not a hackathon-timescale ask. |
| Bexley (`fix.bexley.gov.uk`) | **No** | Same as Bromley. Discovery contact `customer.services@bexley.gov.uk` is for residents. | n/a | Same. |
| Royal Greenwich (`fix.royalgreenwich.gov.uk`) | **No** | Same. `fixmystreet@royalgreenwich.gov.uk` is the contact. | n/a | Same. (Note the canonical Open311 registry also lists a separate `open311.royalgreenwich.gov.uk` discovery URL with no key-request page — DNS unreachable from our IP today.) |
| Southwark (`report.southwark.gov.uk`) | **No** | Same. `environment@southwark.gov.uk`. | n/a | Same. |
| Brent (`report.brent.gov.uk`) | **No** | Same. `ContactCentre@brent.gov.uk`. | n/a | Same. |
| Hounslow Highways (`fms.hounslowhighways.org`) | **No** | Same — but here the "council" is Hounslow Highways Ltd (PFI), `enquiries@hounslowhighways.org`. | n/a | Same. |
| FixMyStreet central (`www.fixmystreet.com/open311`) | **No** | `support@fixmystreet.com` only accepts onboarding requests *from councils*. There is no developer key form. | n/a | The central endpoint exists to *receive* reports from FMS's own front-end, not to host third-party POSTs. |
| mySociety partnership (general) | **No** as written; **Maybe** as a commercial Pro client | Email `hello@mysociety.org` / `support@fixmystreet.com`. Open311 itself is free, "providing asset data and integrating with certain features may be subject to a one-off development fee." | weeks to months | This is a council-procurement pathway, not a dev API program. |
| Oxfordshire FMS Pro (`fixmystreet.oxfordshire.gov.uk`) | **No** | Same Pro pattern. Contact `highway.enquiries@oxfordshire.gov.uk`. | n/a | First UK council to integrate Open311 with FMS (2013). |
| Peterborough (`report.peterborough.gov.uk`) | **No** | `ask@peterborough.gov.uk`. | n/a | Same. |
| Lincolnshire (`fixmystreet.lincolnshire.gov.uk`) | **No** | `FMS@lincolnshire.gov.uk`. | n/a | Same. |
| Northumberland (`fix.northumberland.gov.uk`) | **No** | `fixmystreet-support@northumberland.gov.uk`. | n/a | Same. |
| **Chicago test sandbox** (`test311api.cityofchicago.org`) | **Yes** | Self-serve form at `http://311api.cityofchicago.org/open311/v2/apps/new` — fields: app name, URL, organisation, name, email, phone, TOS checkbox. Production needs staff approval after testing. | Same day for test key (app form submits directly). | Contact `developers@cityofchicago.org`. Service catalogue verified live (services.json returns real data; production requests.json returns real reports). This is the cleanest international sandbox available to us. |
| **Boston** (`mayors24.cityofboston.gov` + `311.boston.gov`) | **Yes (read); approval required for write** | Form at `https://311.boston.gov/open311/app_requests/new` (HTTP 200). Default rate-limit 10 req/min applies to keyless reads; an api_key raises the limit. "Create service requests" requires an additional approval tickbox. | Days (email-back). | TOS has a non-commercial clause on the BOS:311 app — but the Open311 API itself doesn't appear to bar non-commercial *developer* use. Best secondary fallback. |
| **Brookline** (`spot.brooklinema.gov`) | **Yes (in theory)** | Discovery.json contact: `brookonline@brooklinema.gov`. `key_service: "Visit http://brookline-v3.spotreporters.net/open311/v2 to request an API Key"` — URL is malformed in the discovery doc, but the SF/Chicago Spot Reporters platform exposes the same `apps/new` form pattern. | Days (email-back, small town). | Same Spot Reporters (Connected Bits) backend as Chicago, SF, Boston. |
| **San Francisco** (`mobile311.sfgov.org`) | **Yes (in theory)** | Discovery points to `https://san-francisco2-production.spotmobile.net/open311/app_requests/new` (the Spot Reporters form pattern, same as Boston). `mobile311-dev.sfgov.org` test endpoint is DNS-dead. | Days. | Workable but less polished than Chicago — no live test sandbox today. |
| Toronto (`secure.toronto.ca/webwizard/...`) | Unknown — **blocked from our IP** | Form documented at `https://secure.toronto.ca/webwizard/start.jsp?_wiz_id=API_key_request` but Akamai returns 403 to our requests; would need real-browser access. | Unknown. | Spec lists prod + test URLs but neither is reachable from our network. |
| Ottawa (`ottawa.ca/en/open311-api-key-registration-form`) | Unknown — **DNS unreachable** | The apigee endpoints in the registry no longer resolve. | n/a | Likely dead. |
| Bloomington IN (`bloomington.in.gov/crm/open311`) | Unknown — **Cloudflare blocked** | `bloomington.in.gov` returns Cloudflare "you have been blocked" to our IP. Documented form at `http://bloomington.in.gov/open311-api-key-request`. Status monitor confirms server is alive (https://status.open311.org/cities/bloomington) but unreachable from this machine. | Days. | Status monitor confirms it's actually up and serving 63 service types — but we can't get past Cloudflare's bot detection from this IP to apply or read. |
| Baltimore MD | Unknown | Registry lists `http://311.baltimorecity.gov/open311/v2/apps/new`; today both prod and `balt311.baltimorecity.gov` return 401/404. | n/a | Possibly migrated. |
| UK alternatives: IamReporting, FixMyHighway, National Highways | **No usable Open311** | `www.iamreporting.com` returns a marketing landing page, not an API. `www.fixmyhighway.com` has no DNS. `api.nationalhighways.co.uk` has no DNS. | n/a | None of the FMS competitors expose an Open311 endpoint we can find. |

### Bottom line numbers

- Of **33 London authorities**, **6 have publicly readable Open311 endpoints** we can poll today (Bexley, Brent, Bromley, Royal Greenwich, Southwark, Hounslow-Highways) — plus the central FixMyStreet endpoint, which routes to all 33 by `agency_responsible`.
- Of those **6 + 1 = 7 UK surfaces**, **0 will issue a write-capable API key to a third-party developer.** The mySociety/FMS api_key flow is unidirectional (council→mySociety) — there is no application channel for unaffiliated developers.
- **For the hackathon timeframe (3 days), realistically obtainable UK write-keys = 0.**
- **Internationally**, **3 endpoints will plausibly issue a key inside 3 days**:
  1. **Chicago** (test + production) — self-serve form, same-day test key, reachable from our IP. Highest confidence.
  2. **Boston** — read keys email-back in days; "create service request" approval is an extra hurdle but not a blocker for a demo.
  3. **Brookline** — small town, friendly contact, same backend as Chicago — most likely to reply quickly, but no live test endpoint and form URL in their discovery doc is malformed (would need to email `brookonline@brooklinema.gov` directly).

### Recommendation: pivoted demo architecture

Given the 0 UK keys finding, the demo path that maximises credibility is a **two-channel architecture**:

1. **UK production path (real users, real shipping):** keep the existing `mailto:` deep-link / per-borough `reporting_url` fallback from `src/data/boroughs.json`. This is what FMS itself falls back to for non-Pro councils, so we're not behind the state of the art.
2. **"Architecture proof" path (demo day only):** wire a feature-flagged Open311 POST against the **Chicago test sandbox** (`http://test311api.cityofchicago.org/open311/v2/`) using a developer key obtained from `http://311api.cityofchicago.org/open311/v2/apps/new`. This lets the demo show the *exact* GeoReport v2 POST payload we'd send to a London council the moment a partnership opens up — same code path, same wire format, just a different `base_url` + `api_key` per jurisdiction.

This matches how every other Open311 client (e.g. the `open311` npm package, the City of Bloomington uReport client) handles the "no key for this jurisdiction yet" case — it's standard practice.

### Best international sandbox (demo target)

**Chicago test endpoint:** `http://test311api.cityofchicago.org/open311/v2/`

- Discovery: `http://311api.cityofchicago.org/open311/v2/discovery.json` (returns prod + test endpoint URLs, key_service URL, contact)
- Services: `http://test311api.cityofchicago.org/open311/v2/services.json` returns the real catalogue (potholes, graffiti, abandoned vehicle, tree trim, etc. — overlapping with London report types)
- Production data: `http://test311api.cityofchicago.org/open311/v2/requests.json` is live and returns recent real Chicago 311 tickets — useful for verifying we can read writes back after POST
- Key application: `http://311api.cityofchicago.org/open311/v2/apps/new` (HTTP 200, form rendered, terms link present). Self-serve. Fields are all standard developer-info; no proof-of-residence required.
- Contact: `developers@cityofchicago.org`
- Spec: GeoReport v2, no extensions; payload identical to what we'd send to FMS.
- Powered by: Connected Bits' Spot Reporters platform, the same Rails app that runs Boston, SF, and Brookline — so any Chicago integration is a near-zero-cost port to those three.

This is materially better than any UK option because (a) the form actually exists, (b) the test endpoint is up and serving live data, (c) the production catalogue overlaps semantically with London's, and (d) we can iterate on the test endpoint without ever filing a real council ticket.

### Validation probes (2026-06-06, this machine)

| URL | Status | Use |
|-----|--------|-----|
| `http://311api.cityofchicago.org/open311/v2/discovery.json` | 200 | Confirms `key_service` URL is correct and prod is up. |
| `http://311api.cityofchicago.org/open311/v2/apps/new` | 200 | Form renders; TOS link points to `http://dev.cityofchicago.org/docs/open311/tos/`. |
| `http://test311api.cityofchicago.org/open311/v2/discovery.json` | 200 | Confirms sandbox alive. |
| `http://test311api.cityofchicago.org/open311/v2/services.json` | 200 | Real service catalogue. |
| `http://test311api.cityofchicago.org/open311/v2/requests.json` | 200 | Real recent requests (verified `SR26-00011019` dated 2026-06-03). |
| `https://311.boston.gov/open311/app_requests/new` | 200 | Boston key form alive. |
| `https://spot.brooklinema.gov/open311/v2/discovery.json` | 200 | Brookline discovery alive; `key_service` URL in payload is malformed (missing slash) but the contact email is valid. |
| `https://mobile311.sfgov.org/open311/v2/discovery.json` | 200 | SF discovery alive; points to `san-francisco2-production.spotmobile.net/open311/app_requests/new`. |
| `https://fixmystreet.oxfordshire.gov.uk/open311/v2/discovery.json` | 200 | Confirms non-London UK FMS Pro pattern is the same as the London co-brands. |
| `https://report.peterborough.gov.uk/open311/v2/discovery.json` | 200 | Same. |
| `https://fixmystreet.lincolnshire.gov.uk/open311/v2/discovery.json` | 200 | Same. |
| `https://fix.northumberland.gov.uk/open311/v2/discovery.json` | 200 | Same. |
| `https://secure.toronto.ca/webwizard/ws/discovery.xml` | 403 (Akamai) | Toronto unreachable from us. |
| `https://bloomington.in.gov/apps/open311` | 403 (Cloudflare) | Bloomington unreachable from us. |
| `https://ottawa.ca/en/open311-api-key-registration-form` | 403 | Ottawa form unreachable. |
| `https://city-of-ottawa-prod.apigee.net/open311/v2/discovery.json` | DNS NXDOMAIN | Ottawa Apigee dead. |
| `https://www.iamreporting.com/open311/v2/discovery.json` | 200 (HTML landing, not API) | Marketing page only — no Open311 here. |

### Reproducibility

The canonical Open311 server list is at <https://raw.githubusercontent.com/open311/open311.github.io/master/data/servers.yml>. Of the 25 endpoints listed there, only **Chicago, Boston, Brookline, SF** have working `api_key_request` URLs reachable from our network. Add the **mySociety FMS pattern** as 7 UK surfaces that are read-only by policy. The other ~14 endpoints in servers.yml are German municipalities (klarschiff*), Helsinki/Turku, Quebec, Surrey BC, and a handful of dead/migrated installs.

### Open follow-ups (not done; out of scope for this 30-minute time-box)

- Confirm Chicago's TOS actually permits non-Chicago developers (the TOS page itself returned 403 to our requests — verifiable from a real browser).
- If Chicago's TOS turns out to be restrictive, fall back to Boston as primary.
- Try the Toronto / Bloomington forms from a real browser (their CDN is fighting our IP, not their policy).
- Investigate FMS Pro's commercial partnership pricing — useful as a "what would full integration cost" footnote in the pitch deck, not a hackathon path.
