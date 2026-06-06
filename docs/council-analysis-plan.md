# Fair Council Performance Analysis — Plan

## The problem with naive ranking

Today our leaderboard sorts by median resolution days. That's unfair, because:

1. **Volume bias** — a council with 3,000 reports/year is in a different operational world than one with 500. We're comparing a Premier League club to a Sunday team.
2. **Category mix bias** — graffiti is fast to clean; fly-tipping needs a vehicle dispatch; planning issues take months by design. A borough with more "hard" categories looks worse through no fault of its own.
3. **Population/area bias** — outer-London Bromley covers 150 sq km; Kensington covers 12. Different reporting density, different operational challenges.
4. **Adoption bias** — FixMyStreet Pro boroughs (Camden, Hackney, Westminster, etc.) get more reports because the integration funnels them in. Boroughs that don't use FixMyStreet have artificially LOW report counts in our DB, which makes their resolution stats unreliable.
5. **Selection bias** — only *resolved* reports have resolution times. A borough that ignores reports forever looks great on "median resolution days" (because nothing resolves, so the sample is tiny).
6. **Temporal bias** — old reports (e.g., 11-year-old abandoned scooter that got fixed last week) distort averages.

If we publish a naive leaderboard, Camden and Islington — the two biggest, most-engaged boroughs — will look bad just because they're loaded. That's not just unfair, it's misleading.

---

## The fair framework: 5 dimensions, normalised

Each borough gets scored on 5 dimensions. Each dimension is normalised (0–100 z-score scaled) so they're directly comparable. The composite score is the weighted average.

### Dimension 1: Volume Burden (descriptive, not scored)
*"How loaded is this council?"*

- **Reports per 10,000 residents** (using ONS Census 2021 population per borough)
- **Reports per square kilometre** (using borough area)
- **Reports per month** (raw)

This is **context, not a score**. High volume isn't good or bad — it tells us how to weight everything else. A borough handling 10× the volume gets a partial credit grade against the same outcome.

### Dimension 2: Resolution Rate
*"Of reports filed, how many got fixed?"*

- `% resolved` = fixed reports / (fixed + open) over a 12-month window
- **Time-bounded**: only count reports filed >90 days ago (so we don't penalise recent reports that legitimately haven't had time to resolve)
- Cap at 95% — anything above is suspicious data quality

### Dimension 3: Speed (Median Resolution Days)
*"When they do fix it, how fast?"*

- Median resolution days (we use median, not mean, to ignore the 11-year-old outliers)
- **Per category**, then averaged with equal weight across categories the borough handles. This is the trick that removes category-mix bias.

### Dimension 4: Long-Tail Burden
*"How many reports are rotting?"*

- `% of reports open > 90 days`
- This catches the "ignored forever" pattern that Dimension 2 misses

### Dimension 5: Per-Category League Position
*"For each issue type, where does this council rank vs peers?"*

- For each category (potholes, fly-tipping, graffiti, etc.) where a borough has ≥10 resolved reports, compute its **percentile rank** among all London boroughs on median resolution days
- Average the percentile ranks across the borough's categories
- This is the **fairness corrective** — Camden being slow on fly-tipping is compared only to other boroughs' fly-tipping resolution, not to Bromley's graffiti speed.

### Composite Score
Weighted: 25% resolution rate + 30% per-category position + 25% speed + 20% long-tail burden.
Volume burden is shown alongside as context, not in the composite.

---

## What gets displayed

### Top-level leaderboard (replaces current)
Sortable columns:
| Rank | Borough | Volume / 10k | Composite Score | Resolution % | Median Days | Long Tail % | Adoption flag |
|------|---------|-------------|-----------------|--------------|-------------|-------------|---------------|

Add **adoption flag** ("FMS Pro" / "FMS Public" / "Direct only") so users can see which boroughs are well-represented in our data and which aren't.

### Per-borough page enhancements
Each borough page already exists. Add:

1. **Volume context card** at the top — "Camden handles 4,200 reports/year, 18.7 per 10k residents (3rd-highest in London). For its volume class, here's how it's doing:"
2. **Radar chart** — 5 dimensions vs London median, so you can see the shape of strengths/weaknesses at a glance
3. **Per-category league table** — for each category Camden handles, show its London percentile rank
4. **Volume-adjusted commentary**: "Camden's median pothole resolution is 24 days, vs the London median of 18 days. But Camden handles 3× the pothole volume of Islington."

### Cohort view (optional, big-impact)
Group boroughs into cohorts:
- **Inner High-Volume** (Camden, Islington, Westminster, Hackney, Southwark)
- **Inner Low-Volume** (City of London, K&C)
- **Outer Suburban** (Bromley, Bexley, Sutton)
- **Outer Urban** (Newham, Brent, Haringey)

Compare within cohort, not across. "Camden is 3rd in its cohort of 5" is a much fairer story than "Camden is 18th of 33."

---

## Data we need to add

| Data | Source | Notes |
|------|--------|-------|
| Borough population (2021) | ONS Census 2021 | Already in `data/raw/census/` per the migration notes |
| Borough area (sq km) | ONS / data.london.gov.uk | Static lookup, can hardcode |
| FixMyStreet Pro adoption | Manual list from research (Camden, Hackney, Westminster, Bromley, Bexley, Hounslow, Merton, Barnet) | Adoption flag column |
| SLA targets per category | London Councils published targets, or empirical p50 from data | For "% in SLA" metric |

---

## Implementation phases

### Phase 1 — Math (2-3 hours)
- Compute the 5 dimensions per borough
- Compute London-wide medians per category for the percentile rank
- Add `borough_metadata` table or JSON file (population, area, adoption)
- New API endpoint `/api/boroughs/scorecard` returning the full multi-dimensional data

### Phase 2 — Leaderboard redesign (1-2 hours)
- Update `/api/boroughs` to use the composite score
- Add sortable columns for each dimension
- Add adoption flag chip

### Phase 3 — Per-borough page (2-3 hours)
- Volume context card at top
- Radar chart (Chart.js radar, 5 axes)
- Per-category league table
- Inline commentary template

### Phase 4 — Cohort view (1-2 hours, can be cut)
- Define cohorts in a JSON file
- Add cohort filter to leaderboard
- Cohort league table

---

## Honest caveats to surface in the UI

We should publish these prominently — they make us credible, not less so:

- "Data is from FixMyStreet submissions only. Boroughs that don't use FixMyStreet as their primary intake will be under-represented."
- "Median resolution days only includes resolved reports. Ignored reports skew the data."
- "Categories are FixMyStreet's taxonomy and vary slightly between boroughs."
- "We compare like-for-like on category league position; the composite score is our best effort at fairness but no single number is the truth."

A small "Methodology" link from every score, opening a modal that shows exactly how that number was computed for that borough. This is the kind of detail that makes investors and judges trust the work.

---

## What this gives us for the pitch

Instead of "Hackney is rubbish at fixing things" (which is unfair and probably wrong), we can say:

> "Hackney handles 4,500 reports/year — 19.3 per 10,000 residents, third-highest in London. They resolve 73% within 90 days, slightly below the London median of 78%. But on a per-category basis, they rank in the top quartile for graffiti and dog fouling. Where they fall behind is fly-tipping and roadworks. The agent can now flag fly-tipping reports to Hackney as particularly slow-moving and escalate them earlier."

That's a story. That's also actionable for the council. Councils will engage with that. They won't engage with "you're #28 on a league table."
