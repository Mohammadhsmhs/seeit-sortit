"""London Civic Agent — Borough Performance Dashboard."""

import base64
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, render_template, request

from src.data import processed_issues as store
from src.dashboard import scoring

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scraper", "fixmystreet.db")
FIXMYSTREET_REPORT_URL = "https://www.fixmystreet.com/report/{id}"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB photo cap
logger = logging.getLogger(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Helpers ───────────────────────────────────────────────────────────

def _parse_photos(photo_urls_json):
    """photo_urls is a JSON list stored as a string. Returns a list of URLs."""
    if not photo_urls_json:
        return []
    try:
        parsed = json.loads(photo_urls_json)
        if isinstance(parsed, list):
            return [u for u in parsed if isinstance(u, str) and u]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _days_open(created_at):
    """Days between created_at (ISO) and now. None if unparseable."""
    if not created_at:
        return None
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return round(delta.total_seconds() / 86400, 1)
    except (ValueError, AttributeError):
        return None


def _borough_slug(name):
    """Lowercase, hyphenated slug for a borough name."""
    if not name:
        return ""
    return name.strip().lower().replace(" ", "-").replace("'", "")


def _slug_to_borough(slug):
    """Look up the canonical borough name from a slug. Returns None if not found."""
    db = get_db()
    rows = db.execute("SELECT DISTINCT borough FROM reports").fetchall()
    db.close()
    for r in rows:
        if _borough_slug(r["borough"]) == slug.lower():
            return r["borough"]
    return None


def _serialise_report(row):
    """Turn a DB row into a JSON-friendly dict with computed fields.

    Always compute days_open for open tickets so the frontend can age-bucket
    them on the map.
    """
    d = dict(row)
    d["photos"] = _parse_photos(d.get("photo_urls"))
    d.pop("photo_urls", None)
    d["fixmystreet_url"] = FIXMYSTREET_REPORT_URL.format(id=d["id"])
    status = (d.get("status") or "").lower()
    if status == "open":
        d["days_open"] = _days_open(d.get("created_at"))
    else:
        d["days_open"] = None
    return d


def _row_to_report(row):
    """Lightweight version of _serialise_report for the main /api/reports list.

    Skips the photos list (expensive to parse for 6000+ rows) but always
    includes days_open + a fixmystreet URL so the map can age-bucket reports.
    """
    d = dict(row)
    d["fixmystreet_url"] = FIXMYSTREET_REPORT_URL.format(id=d["id"])
    status = (d.get("status") or "").lower()
    d["days_open"] = _days_open(d.get("created_at")) if status == "open" else None
    return d


# ── Category normalisation ───────────────────────────────────────────
#
# The canonical taxonomy lives in src/data/category_mapping.json. We load
# it once at import time and use it to roll up the ~350 raw FixMyStreet
# categories into a small set of parent buckets like "Roads and Highways"
# or "Waste and Fly-Tipping".

_CATEGORY_MAPPING_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "category_mapping.json"
)


def _load_category_mapping():
    try:
        with open(_CATEGORY_MAPPING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("mapping", {})
        # Build a case-insensitive lookup
        return {k.strip().lower(): v.strip() for k, v in raw.items() if k and v}
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not load category_mapping.json; using identity mapping")
        return {}


_CATEGORY_MAPPING = _load_category_mapping()


def _normalize_category(name):
    if not name:
        return name
    key = name.strip().lower()
    return _CATEGORY_MAPPING.get(key, name.strip())


def _category_slug(name):
    """URL-safe slug for a normalised category name."""
    if not name:
        return ""
    s = name.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_/":
            out.append("-")
        # drop everything else (& punctuation, etc.)
    slug = "".join(out)
    # collapse runs of dashes
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _slug_to_category(slug):
    """Reverse lookup: given a slug, return the canonical normalised name.

    Inspects every distinct DB category, normalises it, and matches slugs.
    """
    if not slug:
        return None
    db = get_db()
    rows = db.execute("SELECT DISTINCT category FROM reports").fetchall()
    db.close()
    seen = set()
    for r in rows:
        norm = _normalize_category(r["category"])
        if norm in seen:
            continue
        seen.add(norm)
        if _category_slug(norm) == slug.lower():
            return norm
    return None


def _aggregate_categories(rows):
    """Merge rows sharing the same normalised category. Each row must have
    'category', 'total', and optionally 'avg_days'.

    Accepts both sqlite3.Row and plain dicts.
    """
    merged = {}
    for r in rows:
        # sqlite3.Row has no .get() — normalise to dict first
        rd = dict(r) if not isinstance(r, dict) else r
        key = _normalize_category(rd["category"])
        if key not in merged:
            merged[key] = {"category": key, "total": 0, "_sum_days": 0.0, "_n_days": 0}
        merged[key]["total"] += rd["total"]
        if rd.get("avg_days") is not None:
            merged[key]["_sum_days"] += rd["avg_days"] * rd["total"]
            merged[key]["_n_days"] += rd["total"]
    result = []
    for v in merged.values():
        v["avg_days"] = round(v["_sum_days"] / v["_n_days"], 1) if v["_n_days"] else None
        del v["_sum_days"], v["_n_days"]
        result.append(v)
    result.sort(key=lambda x: x["total"], reverse=True)
    return result


def _compute_median(values):
    """Plain median for a sorted list. None if empty."""
    if not values:
        return None
    vals = sorted(values)
    mid = len(vals) // 2
    if len(vals) % 2:
        return round(vals[mid], 1)
    return round((vals[mid - 1] + vals[mid]) / 2, 1)


def _get_orchestrator():
    """Lazily build an Orchestrator with the configured LLM provider."""
    from src.config import MODEL_PROVIDER
    from src.agents.orchestrator import Orchestrator

    if MODEL_PROVIDER == "nim":
        from src.models.nim import NIMProvider
        llm = NIMProvider()
    elif MODEL_PROVIDER == "openai":
        from src.models.openai import OpenAIProvider
        llm = OpenAIProvider()
    else:
        from src.models.mock import MockProvider
        llm = MockProvider()

    return Orchestrator(llm)


# ── Pages ─────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/dashboard")
def index():
    return render_template("index.html")


@app.route("/dashboard/borough/<short_name>")
def borough_page(short_name: str):
    borough = _slug_to_borough(short_name)
    if borough is None:
        abort(404)
    return render_template("borough.html", borough=borough, slug=_borough_slug(borough))


@app.route("/dashboard/categories")
def categories_page():
    """Top-level category leaderboard — same data as /api/categories/stats."""
    return render_template("categories.html")


@app.route("/dashboard/category/<slug>")
def category_page(slug: str):
    category = _slug_to_category(slug)
    if category is None:
        abort(404)
    return render_template("category.html", category=category, slug=_category_slug(category))


@app.route("/intake")
def intake_page():
    return render_template("intake.html")


@app.route("/processed")
def processed_page():
    return render_template("processed.html")


# ── Consumer app pages ────────────────────────────────────────────────

@app.route("/app")
def app_landing():
    return render_template("app.html")


@app.route("/app/camera")
def app_camera():
    return render_template("camera.html")


@app.route("/app/mic")
def app_mic():
    return render_template("mic.html")


@app.route("/app/home")
def app_home():
    return render_template("home.html")


# ── API endpoints ─────────────────────────────────────────────────────

@app.route("/api/processed")
def api_processed():
    """Return all agent-processed issues as JSON."""
    return jsonify(store.get_all())


@app.route("/api/processed/<issue_id>")
def api_processed_detail(issue_id: str):
    """Return a single processed issue with full details."""
    item = store.get_by_id(issue_id)
    if item is None:
        return jsonify({"error": "Issue not found"}), 404
    return jsonify(item)

@app.route("/api/reports")
def api_reports():
    """All reports (lightweight) — used by the all-London map.

    Each row includes a computed days_open so the frontend can age-bucket
    open tickets into the six-colour scheme.
    """
    db = get_db()
    rows = db.execute(
        """SELECT id, title, category, description, latitude, longitude,
                  address, borough, status, created_at, resolved_at,
                  resolution_days
           FROM reports ORDER BY created_at DESC"""
    ).fetchall()
    db.close()
    return jsonify([_row_to_report(r) for r in rows])


@app.route("/api/stats")
def api_stats():
    db = get_db()

    total = db.execute("SELECT COUNT(*) AS n FROM reports").fetchone()["n"]

    # Borough stats
    borough_rows = db.execute(
        """SELECT borough,
                  COUNT(*) AS total,
                  ROUND(AVG(resolution_days), 1) AS avg_days,
                  ROUND(MEDIAN_PLACEHOLDER, 1) AS med_days
           FROM reports GROUP BY borough ORDER BY total DESC"""
        .replace(
            "ROUND(MEDIAN_PLACEHOLDER, 1) AS med_days",
            # SQLite has no MEDIAN, so we compute it in Python below
            "0 AS med_days"
        )
    ).fetchall()
    borough_stats = [dict(r) for r in borough_rows]

    # Compute medians per borough in Python
    for bs in borough_stats:
        med_row = db.execute(
            """SELECT resolution_days FROM reports
               WHERE borough = ? AND resolution_days IS NOT NULL
               ORDER BY resolution_days""",
            (bs["borough"],),
        ).fetchall()
        vals = [r["resolution_days"] for r in med_row]
        if vals:
            mid = len(vals) // 2
            bs["med_days"] = round(vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2, 1)
        else:
            bs["med_days"] = None

    # Category stats (top 15, normalised)
    cat_rows = db.execute(
        """SELECT category, COUNT(*) AS total,
                  ROUND(AVG(resolution_days), 1) AS avg_days
           FROM reports GROUP BY category ORDER BY total DESC"""
    ).fetchall()
    category_stats = _aggregate_categories(cat_rows)[:15]

    # Resolution time distribution
    brackets = db.execute(
        """SELECT
             SUM(CASE WHEN resolution_days < 1 THEN 1 ELSE 0 END) AS same_day,
             SUM(CASE WHEN resolution_days >= 1 AND resolution_days < 3 THEN 1 ELSE 0 END) AS one_three,
             SUM(CASE WHEN resolution_days >= 3 AND resolution_days < 7 THEN 1 ELSE 0 END) AS one_week,
             SUM(CASE WHEN resolution_days >= 7 AND resolution_days < 30 THEN 1 ELSE 0 END) AS one_month,
             SUM(CASE WHEN resolution_days >= 30 AND resolution_days < 90 THEN 1 ELSE 0 END) AS three_months,
             SUM(CASE WHEN resolution_days >= 90 AND resolution_days < 180 THEN 1 ELSE 0 END) AS six_months,
             SUM(CASE WHEN resolution_days >= 180 THEN 1 ELSE 0 END) AS over_six
           FROM reports WHERE resolution_days IS NOT NULL"""
    ).fetchone()

    resolution_dist = {
        "Same day": brackets["same_day"] or 0,
        "1-3 days": brackets["one_three"] or 0,
        "3-7 days": brackets["one_week"] or 0,
        "1-4 weeks": brackets["one_month"] or 0,
        "1-3 months": brackets["three_months"] or 0,
        "3-6 months": brackets["six_months"] or 0,
        "6+ months": brackets["over_six"] or 0,
    }

    db.close()
    return jsonify({
        "total_reports": total,
        "borough_stats": borough_stats,
        "category_stats": category_stats,
        "resolution_distribution": resolution_dist,
    })


@app.route("/api/boroughs/scorecard")
def api_boroughs_scorecard():
    """Fair multi-dimensional council scorecard (BETA).

    Returns each borough's raw metrics, normalised scores, and composite,
    plus the London-wide medians for the radar baseline.

    See scoring.py for the methodology.
    """
    db = get_db()
    scored = scoring.score_all_boroughs(db)
    medians = scoring.london_medians(scored)
    db.close()
    return jsonify({
        "beta": True,
        "methodology_url": "/docs/council-analysis-plan.md",
        "weights": scoring.WEIGHTS,
        "boroughs": scored,
        "london_medians": medians,
    })


@app.route("/api/borough/<short_name>/categories")
def api_borough_category_league(short_name: str):
    """Per-category league position for one borough.

    For each category the borough handles (with ≥10 resolved reports),
    show its rank vs other London boroughs handling the same category.
    """
    borough = _slug_to_borough(short_name)
    if borough is None:
        return jsonify({"error": "Borough not found"}), 404
    db = get_db()
    results = scoring.per_category_league(db, borough)
    db.close()
    return jsonify({"borough": borough, "categories": results})


@app.route("/api/boroughs")
def api_boroughs():
    """Borough performance leaderboard with fastest/slowest categories."""
    db = get_db()

    boroughs = db.execute(
        """SELECT borough, COUNT(*) AS total,
                  ROUND(AVG(resolution_days), 1) AS avg_days
           FROM reports GROUP BY borough"""
    ).fetchall()
    result = []

    for b in boroughs:
        name = b["borough"]

        # Median
        med_rows = db.execute(
            """SELECT resolution_days FROM reports
               WHERE borough = ? AND resolution_days IS NOT NULL
               ORDER BY resolution_days""",
            (name,),
        ).fetchall()
        vals = [r["resolution_days"] for r in med_rows]
        if vals:
            mid = len(vals) // 2
            median = round(vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2, 1)
        else:
            median = None

        # Fastest category (lowest avg resolution, min 2 reports)
        fastest = db.execute(
            """SELECT category, ROUND(AVG(resolution_days), 1) AS avg_d, COUNT(*) AS n
               FROM reports WHERE borough = ? AND resolution_days IS NOT NULL
               GROUP BY category HAVING n >= 2
               ORDER BY avg_d ASC LIMIT 1""",
            (name,),
        ).fetchone()

        # Slowest category
        slowest = db.execute(
            """SELECT category, ROUND(AVG(resolution_days), 1) AS avg_d, COUNT(*) AS n
               FROM reports WHERE borough = ? AND resolution_days IS NOT NULL
               GROUP BY category HAVING n >= 2
               ORDER BY avg_d DESC LIMIT 1""",
            (name,),
        ).fetchone()

        result.append({
            "borough": name,
            "total": b["total"],
            "avg_days": b["avg_days"],
            "median_days": median,
            "fastest_category": fastest["category"] if fastest else "N/A",
            "fastest_avg": fastest["avg_d"] if fastest else None,
            "slowest_category": slowest["category"] if slowest else "N/A",
            "slowest_avg": slowest["avg_d"] if slowest else None,
        })

    # Sort by median resolution (ascending = best first)
    result.sort(key=lambda x: x["median_days"] if x["median_days"] is not None else 9999)
    db.close()
    return jsonify(result)


# ── Category analytics ───────────────────────────────────────────────


def _aggregate_category_stats(rows):
    """Roll up raw DB category rows into normalised parent categories.

    Each input row must have: category, status, resolution_days, days_open,
    borough. Returns a list of per-normalised-category stat dicts.
    """
    bucket = {}  # name → working bucket
    for r in rows:
        norm = _normalize_category(r["category"])
        if not norm:
            continue
        b = bucket.get(norm)
        if b is None:
            b = bucket[norm] = {
                "category": norm,
                "slug": _category_slug(norm),
                "total": 0,
                "resolved": 0,
                "open": 0,
                "_res_days": [],         # resolution times for resolved
                "_open_days": [],        # current days_open for open
                "_by_borough": {},       # borough → {n, resolved, _res_days}
            }
        b["total"] += 1
        status = (r["status"] or "").lower()
        if status == "fixed":
            b["resolved"] += 1
            if r["resolution_days"] is not None:
                b["_res_days"].append(r["resolution_days"])
        elif status == "open":
            b["open"] += 1
            if r["days_open"] is not None:
                b["_open_days"].append(r["days_open"])
        borough = r["borough"] or "Unknown"
        bb = b["_by_borough"].setdefault(
            borough, {"borough": borough, "n": 0, "resolved": 0, "_res_days": []}
        )
        bb["n"] += 1
        if status == "fixed":
            bb["resolved"] += 1
            if r["resolution_days"] is not None:
                bb["_res_days"].append(r["resolution_days"])
    # Finalise: medians/averages, best/worst borough
    results = []
    for b in bucket.values():
        b["median_resolution_days"] = _compute_median(b["_res_days"])
        b["avg_resolution_days"] = (
            round(sum(b["_res_days"]) / len(b["_res_days"]), 1) if b["_res_days"] else None
        )
        b["avg_days_open"] = (
            round(sum(b["_open_days"]) / len(b["_open_days"]), 1) if b["_open_days"] else None
        )
        b["pct_resolved"] = round((b["resolved"] / b["total"]) * 100, 1) if b["total"] else 0
        # Borough rollups — only consider boroughs with >= 5 reports of this
        # category so we don't crown a borough on the back of 1 lucky resolve.
        eligible = []
        for bb in b["_by_borough"].values():
            if bb["n"] >= 5 and bb["_res_days"]:
                bb["median_days"] = _compute_median(bb["_res_days"])
                eligible.append(bb)
        if eligible:
            eligible.sort(key=lambda x: x["median_days"])
            best = eligible[0]
            worst = eligible[-1]
            b["best_borough"] = {"borough": best["borough"], "median_days": best["median_days"], "n": best["n"]}
            b["worst_borough"] = {"borough": worst["borough"], "median_days": worst["median_days"], "n": worst["n"]}
        else:
            b["best_borough"] = None
            b["worst_borough"] = None
        # Strip internals
        for k in ("_res_days", "_open_days", "_by_borough"):
            b.pop(k, None)
        results.append(b)
    results.sort(key=lambda x: x["total"], reverse=True)
    return results


@app.route("/api/categories/stats")
def api_categories_stats():
    """Per-category aggregations: counts, resolution times, best/worst borough.

    Used by the main dashboard's "Performance by Issue Type" panel. Returns
    the top 20 normalised categories by total report count.
    """
    db = get_db()
    rows = db.execute(
        """SELECT category, status, resolution_days, created_at, borough
           FROM reports"""
    ).fetchall()
    db.close()
    # Add days_open in-Python for open rows
    enriched = []
    for r in rows:
        d = dict(r)
        if (d.get("status") or "").lower() == "open":
            d["days_open"] = _days_open(d.get("created_at"))
        else:
            d["days_open"] = None
        enriched.append(d)
    stats = _aggregate_category_stats(enriched)[:20]
    return jsonify(stats)


@app.route("/api/category/<slug>/stats")
def api_category_stats(slug: str):
    """Per-category detail: KPIs, borough leaderboard, resolution distribution."""
    category = _slug_to_category(slug)
    if category is None:
        return jsonify({"error": "Category not found"}), 404
    db = get_db()
    rows = db.execute(
        """SELECT category, status, resolution_days, created_at, borough
           FROM reports"""
    ).fetchall()
    # Filter to this normalised category only
    matching = []
    for r in rows:
        if _normalize_category(r["category"]) != category:
            continue
        d = dict(r)
        if (d.get("status") or "").lower() == "open":
            d["days_open"] = _days_open(d.get("created_at"))
        else:
            d["days_open"] = None
        matching.append(d)
    db.close()

    total = len(matching)
    resolved = [r for r in matching if (r["status"] or "").lower() == "fixed"]
    open_ = [r for r in matching if (r["status"] or "").lower() == "open"]
    res_days = [r["resolution_days"] for r in resolved if r["resolution_days"] is not None]
    open_days = [r["days_open"] for r in open_ if r["days_open"] is not None]

    # Resolution distribution
    dist = {
        "Same day": 0, "1-3 days": 0, "3-7 days": 0,
        "1-4 weeks": 0, "1-3 months": 0, "3-6 months": 0, "6+ months": 0,
    }
    for d in res_days:
        if d < 1:    dist["Same day"] += 1
        elif d < 3:  dist["1-3 days"] += 1
        elif d < 7:  dist["3-7 days"] += 1
        elif d < 30: dist["1-4 weeks"] += 1
        elif d < 90: dist["1-3 months"] += 1
        elif d < 180:dist["3-6 months"] += 1
        else:        dist["6+ months"] += 1

    # Borough leaderboard for THIS category
    by_borough = {}
    for r in matching:
        b = r["borough"] or "Unknown"
        bb = by_borough.setdefault(b, {"borough": b, "total": 0, "resolved": 0, "_res_days": [], "open": 0})
        bb["total"] += 1
        s = (r["status"] or "").lower()
        if s == "fixed":
            bb["resolved"] += 1
            if r["resolution_days"] is not None:
                bb["_res_days"].append(r["resolution_days"])
        elif s == "open":
            bb["open"] += 1
    leaderboard = []
    for bb in by_borough.values():
        bb["median_days"] = _compute_median(bb["_res_days"])
        bb["avg_days"] = round(sum(bb["_res_days"]) / len(bb["_res_days"]), 1) if bb["_res_days"] else None
        bb["pct_resolved"] = round((bb["resolved"] / bb["total"]) * 100, 1) if bb["total"] else 0
        del bb["_res_days"]
        bb["slug"] = _borough_slug(bb["borough"])
        leaderboard.append(bb)
    # Sort by median asc (fastest first); boroughs without enough resolved
    # data are pushed to the end.
    leaderboard.sort(key=lambda x: (x["median_days"] is None, x["median_days"] or 9999))

    return jsonify({
        "category": category,
        "slug": slug,
        "total_reports": total,
        "resolved_count": len(resolved),
        "open_count": len(open_),
        "pct_resolved": round((len(resolved) / total) * 100, 1) if total else 0,
        "median_days": _compute_median(res_days),
        "avg_days": round(sum(res_days) / len(res_days), 1) if res_days else None,
        "avg_days_open": round(sum(open_days) / len(open_days), 1) if open_days else None,
        "resolution_distribution": dist,
        "borough_leaderboard": leaderboard,
    })


@app.route("/api/category/<slug>/reports")
def api_category_reports(slug: str):
    """All reports in a single normalised category, age-bucketed-ready."""
    category = _slug_to_category(slug)
    if category is None:
        return jsonify({"error": "Category not found"}), 404
    db = get_db()
    rows = db.execute(
        """SELECT id, title, category, description, latitude, longitude,
                  address, borough, council, status, created_at, resolved_at,
                  resolution_days, photo_urls
           FROM reports ORDER BY created_at DESC"""
    ).fetchall()
    db.close()
    out = []
    for r in rows:
        if _normalize_category(r["category"]) != category:
            continue
        out.append(_serialise_report(r))
    return jsonify(out)


@app.route("/api/reports/<int:report_id>")
def api_report_detail(report_id: int):
    """Return a single full report as JSON (used by the map click handler).
    Includes the full updates/comments timeline."""
    db = get_db()
    row = db.execute(
        """SELECT id, title, category, description, latitude, longitude,
                  address, borough, council, status, created_at, updated_at,
                  resolved_at, resolution_days, photo_urls
           FROM reports WHERE id = ?""",
        (report_id,),
    ).fetchone()
    if row is None:
        db.close()
        return jsonify({"error": "Report not found"}), 404

    update_rows = db.execute(
        """SELECT text, timestamp FROM updates
           WHERE report_id = ? ORDER BY timestamp ASC""",
        (report_id,),
    ).fetchall()
    db.close()

    data = _serialise_report(row)
    data["updates"] = [dict(u) for u in update_rows]
    return jsonify(data)


@app.route("/api/borough/<short_name>/reports")
def api_borough_reports(short_name: str):
    """Return all reports for a single borough."""
    borough = _slug_to_borough(short_name)
    if borough is None:
        return jsonify({"error": "Borough not found"}), 404
    db = get_db()
    rows = db.execute(
        """SELECT id, title, category, description, latitude, longitude,
                  address, borough, council, status, created_at, resolved_at,
                  resolution_days, photo_urls
           FROM reports WHERE borough = ? ORDER BY created_at DESC""",
        (borough,),
    ).fetchall()
    db.close()
    return jsonify([_serialise_report(r) for r in rows])


@app.route("/api/borough/<short_name>/stats")
def api_borough_stats(short_name: str):
    """Per-borough stats: KPIs, category mix, resolution distribution,
    slowest open reports, fastest resolved reports."""
    borough = _slug_to_borough(short_name)
    if borough is None:
        return jsonify({"error": "Borough not found"}), 404

    db = get_db()

    total = db.execute(
        "SELECT COUNT(*) AS n FROM reports WHERE borough = ?", (borough,)
    ).fetchone()["n"]

    resolved_count = db.execute(
        "SELECT COUNT(*) AS n FROM reports WHERE borough = ? AND status = 'fixed'",
        (borough,),
    ).fetchone()["n"]

    open_count = db.execute(
        "SELECT COUNT(*) AS n FROM reports WHERE borough = ? AND status = 'open'",
        (borough,),
    ).fetchone()["n"]

    pct_resolved = round((resolved_count / total) * 100, 1) if total else 0

    res_rows = db.execute(
        """SELECT resolution_days FROM reports
           WHERE borough = ? AND resolution_days IS NOT NULL
           ORDER BY resolution_days""",
        (borough,),
    ).fetchall()
    res_values = [r["resolution_days"] for r in res_rows]
    median_days = _compute_median(res_values)
    avg_days = round(sum(res_values) / len(res_values), 1) if res_values else None

    # Category breakdown (normalised)
    cat_rows = db.execute(
        """SELECT category, COUNT(*) AS total,
                  ROUND(AVG(resolution_days), 1) AS avg_days
           FROM reports WHERE borough = ?
           GROUP BY category ORDER BY total DESC""",
        (borough,),
    ).fetchall()
    category_stats = _aggregate_categories(cat_rows)[:12]

    # Resolution distribution
    brackets = db.execute(
        """SELECT
             SUM(CASE WHEN resolution_days < 1 THEN 1 ELSE 0 END) AS same_day,
             SUM(CASE WHEN resolution_days >= 1 AND resolution_days < 3 THEN 1 ELSE 0 END) AS one_three,
             SUM(CASE WHEN resolution_days >= 3 AND resolution_days < 7 THEN 1 ELSE 0 END) AS one_week,
             SUM(CASE WHEN resolution_days >= 7 AND resolution_days < 30 THEN 1 ELSE 0 END) AS one_month,
             SUM(CASE WHEN resolution_days >= 30 AND resolution_days < 90 THEN 1 ELSE 0 END) AS three_months,
             SUM(CASE WHEN resolution_days >= 90 AND resolution_days < 180 THEN 1 ELSE 0 END) AS six_months,
             SUM(CASE WHEN resolution_days >= 180 THEN 1 ELSE 0 END) AS over_six
           FROM reports WHERE borough = ? AND resolution_days IS NOT NULL""",
        (borough,),
    ).fetchone()
    resolution_dist = {
        "Same day": brackets["same_day"] or 0,
        "1-3 days": brackets["one_three"] or 0,
        "3-7 days": brackets["one_week"] or 0,
        "1-4 weeks": brackets["one_month"] or 0,
        "1-3 months": brackets["three_months"] or 0,
        "3-6 months": brackets["six_months"] or 0,
        "6+ months": brackets["over_six"] or 0,
    }

    # Slowest unresolved (longest-open) — these need attention.
    # Skip rows with no usable created_at, otherwise empty-string timestamps
    # sort to the top of an ASC ordering and the list comes back full of
    # rows where days_open can't be computed.
    slowest_open_rows = db.execute(
        """SELECT id, title, category, address, created_at
           FROM reports
           WHERE borough = ? AND status = 'open'
             AND created_at IS NOT NULL AND created_at != ''
           ORDER BY created_at ASC LIMIT 10""",
        (borough,),
    ).fetchall()
    slowest_open = []
    for r in slowest_open_rows:
        d = dict(r)
        d["days_open"] = _days_open(d["created_at"])
        d["fixmystreet_url"] = FIXMYSTREET_REPORT_URL.format(id=d["id"])
        slowest_open.append(d)
    # Belt and braces: drop any still-Nones (unparseable dates) and re-sort
    # by days_open DESC so the purple-highlight rows pin to the top of the
    # "These need attention" list in the UI.
    slowest_open = [d for d in slowest_open if d["days_open"] is not None]
    slowest_open.sort(key=lambda d: d["days_open"], reverse=True)

    # Fastest resolutions — wins
    fastest_rows = db.execute(
        """SELECT id, title, category, address, created_at, resolved_at, resolution_days
           FROM reports
           WHERE borough = ? AND resolution_days IS NOT NULL AND resolution_days >= 0
           ORDER BY resolution_days ASC LIMIT 10""",
        (borough,),
    ).fetchall()
    fastest = []
    for r in fastest_rows:
        d = dict(r)
        d["fixmystreet_url"] = FIXMYSTREET_REPORT_URL.format(id=d["id"])
        fastest.append(d)

    # Get the council too — useful in the header
    council_row = db.execute(
        """SELECT council, COUNT(*) AS n FROM reports
           WHERE borough = ? AND council IS NOT NULL AND council != ''
           GROUP BY council ORDER BY n DESC LIMIT 1""",
        (borough,),
    ).fetchone()
    council = council_row["council"] if council_row else None

    db.close()
    return jsonify({
        "borough": borough,
        "council": council,
        "total_reports": total,
        "resolved_count": resolved_count,
        "open_count": open_count,
        "pct_resolved": pct_resolved,
        "median_days": median_days,
        "avg_days": avg_days,
        "category_stats": category_stats,
        "resolution_distribution": resolution_dist,
        "slowest_open": slowest_open,
        "fastest_resolved": fastest,
    })


@app.route("/api/process", methods=["POST"])
def api_process():
    """Run the Orchestrator pipeline on a user-submitted description."""
    data = request.get_json(silent=True)
    if not data or not data.get("description", "").strip():
        return jsonify({"error": "Missing 'description' field"}), 400

    description = data["description"].strip()
    lat = data.get("lat")
    lon = data.get("lon")

    try:
        orch = _get_orchestrator()
        issue = orch.process(
            description,
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
        )
        return jsonify(issue.model_dump(mode="json"))
    except Exception:
        logger.exception("Pipeline error")
        return jsonify({"error": "Pipeline processing failed"}), 500


@app.route("/api/intake-photo", methods=["POST"])
def api_intake_photo():
    """Accept a photo (+ optional text) and run the pipeline."""
    photo = request.files.get("photo")
    if photo is None or photo.filename == "":
        return jsonify({"error": "No photo uploaded"}), 400

    text = (request.form.get("text") or "").strip()
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    # Encode the photo as a data URL so it can be saved with the issue.
    raw = photo.read()
    mime = photo.mimetype or "image/jpeg"
    data_url = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"

    # If the user didn't describe the issue, fall back to a neutral placeholder
    # so the pipeline has something to classify on.
    description = text or "Issue reported via photo upload — see attached image."
    photo_description = text or None

    try:
        orch = _get_orchestrator()
        issue = orch.process(
            description,
            photo_description=photo_description,
            photos=[data_url],
            latitude=float(lat) if lat else None,
            longitude=float(lon) if lon else None,
        )
        return jsonify(issue.model_dump(mode="json"))
    except Exception:
        logger.exception("Photo pipeline error")
        return jsonify({"error": "Pipeline processing failed"}), 500


@app.route("/api/intake-voice", methods=["POST"])
def api_intake_voice():
    """Accept a transcript (+ optional metadata) and run the pipeline."""
    data = request.get_json(silent=True) or {}
    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        return jsonify({"error": "Empty transcript"}), 400

    lat = data.get("lat")
    lon = data.get("lon")

    try:
        orch = _get_orchestrator()
        issue = orch.process(
            transcript,
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
        )
        return jsonify(issue.model_dump(mode="json"))
    except Exception:
        logger.exception("Voice pipeline error")
        return jsonify({"error": "Pipeline processing failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
