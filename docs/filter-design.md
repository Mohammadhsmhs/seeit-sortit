# Filter Design

## The problem

Today the filter bar only has Borough + Category. The marker colour bakes in the status interpretation (green = resolved fast, red = open or slow). If you want to see only **resolved** reports, or only **open ones older than 90 days**, you can't.

Worse — the filters silently affect the leaderboard, KPIs, charts, and map. There's no visible "showing X of Y" feedback.

## Design goals

1. **Multi-dimensional filtering**: borough, category, status, age, resolution speed
2. **Visible state**: always show what's filtered + how many results
3. **One-click clear** per filter and global reset
4. **Compose with the colour legend, don't replace it** — colours stay as visual cues, filters control which rows are shown
5. **Affects all panels together** — map, leaderboard, charts, list — single source of truth
6. **Sleek, not clunky** — dropdowns + chips, not a wall of toggles

## Approach: Toolbar + Chip Row

```
┌───────────────────────────────────────────────────────────────────┐
│  Borough ▾  Category ▾  Status ▾  Age ▾  Speed ▾   [Reset]       │
├───────────────────────────────────────────────────────────────────┤
│  [Camden ×] [Status: Open ×] [Age: 30–90 days ×]    234 of 6,107  │
└───────────────────────────────────────────────────────────────────┘
```

**Top row**: the dropdowns (controls)
**Second row** (only visible when filters are active): active-filter chips + result count

Click a chip → removes that filter. Click "Reset" → clears all.

## Filter dimensions

| Filter | Type | Options |
|--------|------|---------|
| **Borough** | single-select | All Boroughs / [list] |
| **Category** | single-select | All Categories / [list] |
| **Status** | single-select | All / Open / Resolved |
| **Age** | single-select | All / < 7 days / 7–30 days / 30–90 days / > 90 days |
| **Resolution Speed** | single-select | All / Fast (< 7d) / Medium (7–30d) / Slow (> 30d) — only applies to resolved reports |

Future (Phase 2 — out of scope for this round):
- Date range picker
- Multi-select on category
- Has photos toggle
- Hide own submissions

## What gets filtered

Every panel reads from `filtered()`. Affected:
- **Map** markers (clusters + heat)
- **Leaderboard** — recalculated against filtered set… actually no. The leaderboard ranks **boroughs**, so a borough filter would only ever show one row. Decision: **leaderboard is NOT filtered by borough**, but IS filtered by category/status/age/speed. Show a hint when applied.
- **KPIs** — count, median, fastest borough, etc.
- **Category bar chart** — counts in filtered set
- **Resolution distribution** — only resolved reports, filtered
- **Individual Reports** scrollable list

## Visual: chip styling

Existing `.chip` class works. Active filter chips get the dismissal × on the right:

```html
<span class="filter-chip">
  <span class="filter-chip-label">Status:</span>
  <span class="filter-chip-value">Open</span>
  <button class="filter-chip-x">×</button>
</span>
```

## Implementation steps

1. Add `<select>` elements for Status, Age, Speed to the filter bar
2. Add a chip row below — empty by default, populated as filters change
3. Update `filtered()` in JS to apply all five dimensions
4. Update `render()` to display the active-filter chip strip + counter
5. Wire chip × buttons to clear their respective filter
6. Make sure URL doesn't break — keep state in JS only (no query params for now, but easy to add later)

No backend changes — all filtering is client-side because we already load all reports. (The scorecard endpoint isn't filtered, by design — the leaderboard rankings reflect the global picture, not the filtered subset.)

## Estimated effort
~1 hour. Single-file change (`index.html`) + small CSS additions.
