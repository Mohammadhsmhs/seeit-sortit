"""
Fair council scoring (BETA).

Five dimensions per borough:
  1. Volume Burden       — reports / 10k residents. CONTEXT, not scored.
  2. Resolution Rate     — % of reports >90 days old that are resolved.
  3. Speed               — median resolution days, averaged across categories
                           with equal weight (removes category-mix bias).
  4. Long-Tail Burden    — % of open reports older than 90 days.
  5. Per-Category Rank   — average percentile rank vs other boroughs, computed
                           per category. The fairness corrective.

The composite score is a weighted average of dimensions 2-5.
Dimension 1 (volume) is shown as context, not in the composite.

All dimensions are normalised to a 0-100 scale where 100 is best.

Read the methodology in docs/council-analysis-plan.md before changing weights.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Composite weights — sum to 1.0
WEIGHTS = {
    "resolution_rate": 0.25,
    "category_rank": 0.30,
    "speed": 0.25,
    "long_tail": 0.20,
}

# Reports must be older than this to count toward resolution rate
# (so we don't penalise councils for recent reports that legitimately
# haven't had time to be resolved yet).
RESOLUTION_WINDOW_DAYS = 90

# A category needs at least this many resolved reports in a borough
# before we'll use its median for the per-category league position.
MIN_RESOLVED_PER_CATEGORY = 10

METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "borough_metadata.json"
)


# ── Metadata ──────────────────────────────────────────────────────────

def load_metadata():
    """Return dict[borough_name] -> metadata dict.

    Falls back to empty dict if the file is missing — the dashboard still
    works, you just lose population/area/adoption context.
    """
    try:
        with open(METADATA_PATH, "r") as f:
            data = json.load(f)
        return data.get("boroughs", {})
    except FileNotFoundError:
        logger.warning("borough_metadata.json not found at %s", METADATA_PATH)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Bad JSON in borough_metadata.json: %s", e)
        return {}


# ── Helpers ───────────────────────────────────────────────────────────

def _median(values):
    if not values:
        return None
    return round(statistics.median(values), 1)


def _days_since(iso_string, now):
    if not iso_string:
        return None
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).total_seconds() / 86400
    except ValueError:
        return None


def _normalise(value, lo, hi, invert=False):
    """Scale `value` into 0-100 across the [lo, hi] range.

    invert=True means "lower is better" — used for speed and long-tail.
    Clamps to [0, 100] so outliers don't break the scale.
    """
    if value is None or lo is None or hi is None or hi == lo:
        return None
    pct = (value - lo) / (hi - lo) * 100
    if invert:
        pct = 100 - pct
    return max(0.0, min(100.0, round(pct, 1)))


# ── Per-borough raw metrics ──────────────────────────────────────────

def compute_borough_metrics(db, borough, now):
    """Compute raw (not yet normalised) metrics for one borough.

    Returns a dict with the raw numbers — normalisation happens in
    `score_all_boroughs` once we know the London-wide ranges.
    """
    rows = db.execute(
        """SELECT status, created_at, resolution_days, category
           FROM reports WHERE borough = ?""",
        (borough,),
    ).fetchall()

    total = len(rows)
    if total == 0:
        return None

    # Resolution Rate — only count reports old enough to have a chance
    eligible_for_resolution = []
    for r in rows:
        days_old = _days_since(r["created_at"], now)
        if days_old is not None and days_old >= RESOLUTION_WINDOW_DAYS:
            eligible_for_resolution.append(r)

    resolved_in_window = sum(
        1 for r in eligible_for_resolution if r["status"] == "fixed"
    )
    resolution_rate = (
        resolved_in_window / len(eligible_for_resolution) * 100
        if eligible_for_resolution
        else None
    )

    # Speed — median days per category, then mean across categories
    days_per_category = defaultdict(list)
    for r in rows:
        if r["resolution_days"] is not None and r["category"]:
            days_per_category[r["category"]].append(r["resolution_days"])

    category_medians = {
        cat: _median(vals)
        for cat, vals in days_per_category.items()
        if len(vals) >= MIN_RESOLVED_PER_CATEGORY
    }

    if category_medians:
        speed_avg = round(
            sum(category_medians.values()) / len(category_medians), 1
        )
    else:
        speed_avg = None

    # Long-Tail Burden — % of OPEN reports older than 90 days
    open_rows = [r for r in rows if r["status"] == "open"]
    if open_rows:
        old_open = 0
        for r in open_rows:
            days_old = _days_since(r["created_at"], now)
            if days_old is not None and days_old >= 90:
                old_open += 1
        long_tail_pct = round(old_open / len(open_rows) * 100, 1)
    else:
        long_tail_pct = None

    # Volume
    return {
        "borough": borough,
        "total_reports": total,
        "resolved_count": sum(1 for r in rows if r["status"] == "fixed"),
        "open_count": sum(1 for r in rows if r["status"] == "open"),
        "resolution_rate_raw": resolution_rate,
        "speed_raw_days": speed_avg,
        "long_tail_raw_pct": long_tail_pct,
        "category_medians": category_medians,
    }


# ── London-wide aggregation + normalisation ──────────────────────────

def _category_percentile_ranks(boroughs):
    """For each (borough, category), compute percentile rank vs all
    boroughs handling that category, then average per borough.

    Lower median resolution days = better rank = higher percentile (100 = fastest).
    """
    # Gather all category medians keyed by category
    per_category = defaultdict(list)
    for b in boroughs:
        for cat, med in b["category_medians"].items():
            per_category[cat].append((b["borough"], med))

    # For each category, rank boroughs by median ascending
    borough_to_ranks = defaultdict(list)
    for cat, entries in per_category.items():
        if len(entries) < 2:
            continue  # need at least 2 boroughs to rank within a category
        sorted_entries = sorted(entries, key=lambda x: x[1])
        n = len(sorted_entries)
        for i, (borough, _med) in enumerate(sorted_entries):
            # Highest percentile for fastest (i=0); lowest for slowest (i=n-1)
            percentile = (n - 1 - i) / (n - 1) * 100 if n > 1 else 100.0
            borough_to_ranks[borough].append(percentile)

    return {
        b: round(sum(ranks) / len(ranks), 1) if ranks else None
        for b, ranks in borough_to_ranks.items()
    }


def score_all_boroughs(db):
    """Return a list of scored borough dicts, ranked best-first by composite.

    Public API for the dashboard. Includes everything you need to render
    the leaderboard, radar chart, and per-borough page.
    """
    now = datetime.now(timezone.utc)
    metadata = load_metadata()

    # Raw metrics per borough
    boroughs_rows = db.execute(
        "SELECT DISTINCT borough FROM reports WHERE borough IS NOT NULL"
    ).fetchall()

    raw = []
    for row in boroughs_rows:
        m = compute_borough_metrics(db, row["borough"], now)
        if m is not None:
            raw.append(m)

    if not raw:
        return []

    # Per-category league position (depends on all boroughs' category medians)
    category_ranks = _category_percentile_ranks(raw)

    # Volume per 10k residents (descriptive, not in composite)
    for b in raw:
        meta = metadata.get(b["borough"], {})
        pop = meta.get("population")
        b["population"] = pop
        b["area_km2"] = meta.get("area_km2")
        b["adoption"] = meta.get("adoption", "unknown")
        b["cohort"] = meta.get("cohort", "unknown")
        b["reports_per_10k"] = (
            round(b["total_reports"] / pop * 10000, 1) if pop else None
        )
        b["category_rank_raw"] = category_ranks.get(b["borough"])

    # Normalise each dimension across London for the composite score
    def _collect(field):
        return [b[field] for b in raw if b.get(field) is not None]

    res_vals = _collect("resolution_rate_raw")
    speed_vals = _collect("speed_raw_days")
    tail_vals = _collect("long_tail_raw_pct")
    rank_vals = _collect("category_rank_raw")

    res_lo, res_hi = (min(res_vals), max(res_vals)) if res_vals else (None, None)
    speed_lo, speed_hi = (min(speed_vals), max(speed_vals)) if speed_vals else (None, None)
    tail_lo, tail_hi = (min(tail_vals), max(tail_vals)) if tail_vals else (None, None)
    rank_lo, rank_hi = (min(rank_vals), max(rank_vals)) if rank_vals else (None, None)

    for b in raw:
        b["resolution_rate_score"] = _normalise(b["resolution_rate_raw"], res_lo, res_hi)
        b["speed_score"] = _normalise(b["speed_raw_days"], speed_lo, speed_hi, invert=True)
        b["long_tail_score"] = _normalise(b["long_tail_raw_pct"], tail_lo, tail_hi, invert=True)
        b["category_rank_score"] = _normalise(b["category_rank_raw"], rank_lo, rank_hi)

        # Composite — weighted average of available dimensions
        components = {
            "resolution_rate": b["resolution_rate_score"],
            "speed": b["speed_score"],
            "long_tail": b["long_tail_score"],
            "category_rank": b["category_rank_score"],
        }
        used = {k: v for k, v in components.items() if v is not None}
        if used:
            weight_sum = sum(WEIGHTS[k] for k in used)
            weighted = sum(WEIGHTS[k] * v for k, v in used.items())
            b["composite_score"] = round(weighted / weight_sum, 1)
        else:
            b["composite_score"] = None

    # Sort by composite descending (best first); boroughs without score at the end
    raw.sort(key=lambda b: (b["composite_score"] is None, -(b["composite_score"] or 0)))
    for i, b in enumerate(raw, 1):
        b["rank"] = i

    return raw


def london_medians(scored):
    """Compute London-wide medians for use in the radar chart baseline."""
    def med(field):
        vals = [b[field] for b in scored if b.get(field) is not None]
        return round(statistics.median(vals), 1) if vals else None

    return {
        "resolution_rate_score": med("resolution_rate_score"),
        "speed_score": med("speed_score"),
        "long_tail_score": med("long_tail_score"),
        "category_rank_score": med("category_rank_score"),
        "composite_score": med("composite_score"),
        "reports_per_10k": med("reports_per_10k"),
    }


def per_category_league(db, borough):
    """For a single borough, return its rank in each category it handles.

    Used by the per-borough page to show category-level league position.
    """
    rows = db.execute(
        """SELECT category, COUNT(*) AS n,
                  AVG(resolution_days) AS avg_days
           FROM reports
           WHERE borough = ? AND resolution_days IS NOT NULL
           GROUP BY category
           HAVING COUNT(*) >= ?""",
        (borough, MIN_RESOLVED_PER_CATEGORY),
    ).fetchall()

    results = []
    for r in rows:
        cat = r["category"]
        # Compute medians across all boroughs for this category
        other_rows = db.execute(
            """SELECT borough, resolution_days FROM reports
               WHERE category = ? AND resolution_days IS NOT NULL""",
            (cat,),
        ).fetchall()
        by_borough = defaultdict(list)
        for o in other_rows:
            by_borough[o["borough"]].append(o["resolution_days"])
        medians = {b: statistics.median(v) for b, v in by_borough.items() if len(v) >= MIN_RESOLVED_PER_CATEGORY}
        if borough not in medians or len(medians) < 2:
            continue
        sorted_boroughs = sorted(medians.items(), key=lambda x: x[1])
        rank = next(i for i, (b, _) in enumerate(sorted_boroughs, 1) if b == borough)
        n = len(sorted_boroughs)
        results.append({
            "category": cat,
            "borough_median_days": round(medians[borough], 1),
            "rank": rank,
            "total": n,
            "percentile": round((n - rank) / (n - 1) * 100, 0) if n > 1 else 100,
            "borough_report_count": r["n"],
        })
    results.sort(key=lambda x: x["percentile"], reverse=True)
    return results
