# Current State: Reporting a Civic Issue in London

## The Problem in One Line

A London resident who spots a pothole and a dumped mattress on the same street needs **two different platforms, two different accounts, and 15+ clicks** to report both — and must already know which council department handles which issue.

---

## FixMyStreet (fixmystreet.com)

### Flow: Report a Pothole
| Step | Screen | User Input | Decisions |
|------|--------|-----------|-----------|
| 1 | Homepage | Enter postcode or street | Choose input method |
| 2 | Map view | Click exact location on map | Pin precision required |
| 3 | Category selection | Pick from 20-23 top-level categories | "Pothole" is NOT a top-level option — must know it's under "Roads, Pavements and Highway matters" |
| 4 | Subcategory selection | Pick from 8 subcategories | Find "Pothole" among Bridges, Footways, Highway Schemes, Ice/Snow, Manhole, etc. |
| 5 | Duplicate detection | Check if already reported | Review nearby reports |
| 6 | Council criteria | Read minimum size criteria (40mm depth, 150mm diameter) | Does it qualify? |
| 7 | Photo upload | Upload photo (optional) | Take/find photo |
| 8 | Problem details | Write summary + full description (2 fields) | Compose text |
| 9 | Personal info + submit | Name, email, phone, password, visibility toggle | 5 fields + checkbox |

### Totals
- **9 screens** (5 mandatory, 2-3 conditional)
- **8 clicks minimum** to submit
- **7 form fields** to fill
- **67-83 total categories** (varies by council)
- **6 decisions** the user must make
- Account: not required, but email is mandatory
- User needs to know their category: **yes**
- User needs to know their council: **no** (auto-detected from pin)

### Friction Points
- "Pothole" buried 2 levels deep in taxonomy
- Category list changes per council — no consistency
- Map pin validation rejects if not precisely on a road
- Duplicate detection adds a screen even if nothing matches

---

## Islington Council (islington.gov.uk)

### Flow: Report a Pothole
| Step | Screen | User Input |
|------|--------|-----------|
| 1 | Homepage | No "report" link visible — must search or navigate menu |
| 2 | Services > Roads | Find "Roads" section (not obvious) |
| 3 | "Report a problem with a road or pavement" | Read info page |
| 4 | Login / Register | **Account required** — email + password. New users must register first. |
| 5 | My Islington portal | Fill report form (behind login wall) |

- **7+ clicks** from homepage to submitted report
- **Account REQUIRED** — no anonymous option for potholes
- **Must know department** — user must navigate to "Roads" (not "Streets", not "Highways")
- No "report a problem" button on homepage

### Flow: Report Fly-Tipping
| Step | Screen | User Input |
|------|--------|-----------|
| 1 | Homepage | Navigate to Recycling and rubbish |
| 2 | Recycling and rubbish | Click "Report a problem" |
| 3 | Report a street cleaning problem | Choose this sub-option |
| 4 | Choose reporting method | My Islington account OR anonymous |
| 5 | Love Clean Streets form | Category dropdown: **146 selectable options** under 7 groups |
| 6 | Location | Address text field + Google Map with draggable pin |
| 7 | Details + submit | Description + photo (optional, max 4MB) |

- **7 clicks** minimum
- **146 category options** in the dropdown — user must find "Dumped or flytipped waste" in a list of 146
- Uses **external platform** (Love Clean Streets) — different from the pothole system
- **Different department** than potholes — "Recycling and rubbish" not "Roads"

---

## Camden Council (camden.gov.uk)

### Flow: Report a Pothole
| Step | Screen | User Input |
|------|--------|-----------|
| 1 | Homepage | No report link. Click "All services" |
| 2 | All services | Find and click "Environmental issues" (NOT "Roads and travel") |
| 3 | Environmental issues | Click "Report a street problem" |
| 4 | Info page | 14 issue types listed. Click "Report a problem" |
| 5 | **Redirects to FixMyStreet** | Different website, different UI |
| 6-9 | FixMyStreet flow | Postcode → map → category → details → submit |

- **8-9 clicks** across **two different websites**
- Must know it's under "Environmental issues" not "Roads and travel"
- No account required (FixMyStreet handles it)

### Flow: Report Fly-Tipping
| Step | Screen | User Input |
|------|--------|-----------|
| 1 | Homepage | All services |
| 2 | All services | Environmental issues |
| 3 | Environmental issues | Fly-tipping and street obstructions |
| 4 | Info page | Click "Report fly-tipping with Love Clean Streets" |
| 5 | **Redirects to Love Clean Streets** | Third website — different from FixMyStreet |
| 6 | **Account required** | Must create Love Clean Streets account |
| 7 | Report form | Category, location, description, photo |

- **8-10 clicks** minimum, including account creation
- Uses **Love Clean Streets** — different platform than potholes (which uses FixMyStreet)
- **Account REQUIRED** — no anonymous option
- A Camden resident reporting a pothole AND fly-tipping needs accounts on TWO different platforms

---

## Cross-Council Comparison

| Metric | FixMyStreet | Islington (pothole) | Islington (fly-tip) | Camden (pothole) | Camden (fly-tip) |
|--------|------------|-------------------|-------------------|-----------------|-----------------|
| Clicks to submit | 8 | 7+ | 7 | 8-9 | 8-10 |
| Account required | No | **YES** | No | No | **YES** |
| Category options | 67-83 | Behind login | **146** | ~14 | Behind login |
| External platforms | — | My Islington | Love Clean Streets | FixMyStreet | Love Clean Streets |
| Must know department | No | **YES (Roads)** | **YES (Recycling)** | **YES (Environmental)** | **YES (Environmental)** |
| "Report" on homepage | N/A | **NO** | **NO** | **NO** | **NO** |
| Map pin required | YES | Unknown | YES | YES | YES |

---

## The Killer Stats for the Demo

1. **No London council has a "report a problem" button on their homepage.**
2. **Reporting a pothole and fly-tipping on the same street requires 2 different platforms and up to 2 different accounts.**
3. **A user faces 67 to 146 category options** — and must already know the right taxonomy.
4. **8-10 clicks minimum** to report a single issue.
5. **The user must know which department handles their issue** — Roads? Recycling? Environmental? Streets? Highways?
6. **Councils redirect to 3 different external platforms** (FixMyStreet, Love Clean Streets, My Islington) with no consistency.
