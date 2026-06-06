"""Evaluation framework — test the pipeline against real FixMyStreet data.

Usage:
    .venv/bin/python -m src.eval.evaluate
"""

from __future__ import annotations

import json
import logging
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path so src.* imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SCRAPER_DB, CATEGORY_MAPPING_JSON
from src.models.mock import MockProvider
from src.models.base import CivicIssue, IssueCategory
from src.agents.intake import IntakeAgent
from src.agents.severity import SeverityAgent
from src.agents.routing import RoutingAgent

logger = logging.getLogger(__name__)

# Number of reports to sample
SAMPLE_SIZE = 50
SEED = 42


# ---------------------------------------------------------------------------
# Category mapping helpers
# ---------------------------------------------------------------------------

def _load_category_mapping() -> dict[str, str]:
    """Load raw FixMyStreet category -> parent category mapping."""
    if CATEGORY_MAPPING_JSON.exists():
        with open(CATEGORY_MAPPING_JSON) as f:
            data = json.load(f)
        return data.get("mapping", {})
    return {}


def _normalize_to_parent(raw_category: str, mapping: dict[str, str]) -> str:
    """Map a raw FixMyStreet category to a parent category.

    Tries exact match, then case-insensitive match.  If the raw category
    is already a valid parent category name, returns it directly.
    """
    # Already a parent category?
    valid_parents = {c.value for c in IssueCategory}
    if raw_category in valid_parents:
        return raw_category

    # Exact match in mapping
    if raw_category in mapping:
        return mapping[raw_category]

    # Case-insensitive match
    lower_map = {k.lower(): v for k, v in mapping.items()}
    if raw_category.lower() in lower_map:
        return lower_map[raw_category.lower()]

    return "Uncategorised"


# ---------------------------------------------------------------------------
# Borough normalization
# ---------------------------------------------------------------------------

# The DB stores short borough names (e.g. "Islington") while the routing
# agent may return the full council name.  We normalize both sides to
# short names for comparison.
_COUNCIL_TO_SHORT: dict[str, str] = {
    "city of london corporation": "City of London",
    "transport for london (tfl)": "TfL",
}


def _normalize_borough(name: str) -> str:
    """Normalize a borough/council name to a short comparable form."""
    if not name:
        return ""
    low = name.lower().strip()

    # Check explicit overrides
    if low in _COUNCIL_TO_SHORT:
        return _COUNCIL_TO_SHORT[low]

    # Strip common prefixes
    for prefix in ("london borough of ", "royal borough of ", "city of "):
        if low.startswith(prefix):
            return name[len(prefix):].strip()

    return name.strip()


# ---------------------------------------------------------------------------
# Load reports from scraper DB
# ---------------------------------------------------------------------------

def load_sample_reports(n: int = SAMPLE_SIZE, seed: int = SEED) -> list[dict]:
    """Load n random reports from the scraper DB.

    Returns dicts with keys: id, title, category, description, latitude,
    longitude, address, borough.
    """
    if not SCRAPER_DB.exists():
        print(f"ERROR: Scraper DB not found at {SCRAPER_DB}")
        sys.exit(1)

    db = sqlite3.connect(str(SCRAPER_DB))
    db.row_factory = sqlite3.Row

    # Exclude reports with empty description or category
    rows = db.execute(
        "SELECT id, title, category, description, latitude, longitude, "
        "address, borough FROM reports "
        "WHERE description IS NOT NULL AND description != '' "
        "AND category IS NOT NULL AND category != '' "
        "ORDER BY id"
    ).fetchall()
    db.close()

    if len(rows) < n:
        print(f"WARNING: Only {len(rows)} valid reports found (requested {n})")
        n = len(rows)

    rng = random.Random(seed)
    sample = rng.sample(rows, n)
    return [dict(r) for r in sample]


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

def evaluate_classification(
    reports: list[dict],
    intake: IntakeAgent,
    mapping: dict[str, str],
) -> dict:
    """Run classification on each report and compare to actual category.

    Returns a results dict with per-report predictions and aggregate metrics.
    """
    results = []
    correct = 0
    actual_counts: Counter = Counter()
    predicted_counts: Counter = Counter()
    # confusion[actual][predicted] = count
    confusion: dict[str, Counter] = defaultdict(Counter)

    for report in reports:
        actual_parent = _normalize_to_parent(report["category"], mapping)
        actual_counts[actual_parent] += 1

        issue = intake.process(
            report["description"],
            latitude=report.get("latitude"),
            longitude=report.get("longitude"),
        )
        predicted = issue.category
        predicted_counts[predicted] += 1

        match = predicted == actual_parent
        if match:
            correct += 1

        confusion[actual_parent][predicted] += 1

        results.append({
            "id": report["id"],
            "raw_category": report["category"],
            "actual_parent": actual_parent,
            "predicted": predicted,
            "match": match,
        })

    accuracy = correct / len(reports) if reports else 0.0

    # Per-category precision: of everything predicted as X, how many were actually X?
    precision: dict[str, float] = {}
    for cat in predicted_counts:
        tp = confusion[cat][cat]
        total_predicted = predicted_counts[cat]
        precision[cat] = tp / total_predicted if total_predicted > 0 else 0.0

    return {
        "results": results,
        "accuracy": accuracy,
        "correct": correct,
        "total": len(reports),
        "precision": precision,
        "confusion": confusion,
        "actual_counts": actual_counts,
        "predicted_counts": predicted_counts,
    }


def evaluate_severity(
    reports: list[dict],
    intake: IntakeAgent,
    severity_agent: SeverityAgent,
) -> dict:
    """Run severity scoring and check range + distribution."""
    scores = []
    out_of_range = 0

    for report in reports:
        issue = intake.process(
            report["description"],
            latitude=report.get("latitude"),
            longitude=report.get("longitude"),
        )
        issue = severity_agent.process(issue)
        score = issue.severity_score

        if score < 1 or score > 10:
            out_of_range += 1

        scores.append(score)

    distribution = Counter(scores)

    return {
        "scores": scores,
        "min": min(scores) if scores else 0,
        "max": max(scores) if scores else 0,
        "mean": sum(scores) / len(scores) if scores else 0,
        "out_of_range": out_of_range,
        "distribution": dict(sorted(distribution.items())),
    }


def evaluate_routing(
    reports: list[dict],
    intake: IntakeAgent,
    routing_agent: RoutingAgent,
) -> dict:
    """Run routing and compare predicted borough to actual."""
    correct = 0
    total_with_borough = 0
    mismatches = []

    for report in reports:
        actual_borough = report.get("borough", "")
        if not actual_borough:
            continue
        total_with_borough += 1

        issue = intake.process(
            report["description"],
            latitude=report.get("latitude"),
            longitude=report.get("longitude"),
        )
        issue.address = report.get("address", "")
        issue = routing_agent.process(issue)

        actual_norm = _normalize_borough(actual_borough)
        predicted_norm = _normalize_borough(issue.borough)

        if actual_norm.lower() == predicted_norm.lower():
            correct += 1
        else:
            mismatches.append({
                "id": report["id"],
                "actual": actual_borough,
                "predicted": issue.borough,
                "lat": report.get("latitude"),
                "lon": report.get("longitude"),
            })

    accuracy = correct / total_with_borough if total_with_borough > 0 else 0.0

    return {
        "correct": correct,
        "total": total_with_borough,
        "accuracy": accuracy,
        "mismatches": mismatches,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _severity_histogram(distribution: dict[int, int]) -> str:
    """Render a simple ASCII histogram for the severity distribution."""
    lines = []
    max_count = max(distribution.values()) if distribution else 1
    for score in range(1, 11):
        count = distribution.get(score, 0)
        bar_len = int((count / max_count) * 30) if max_count > 0 else 0
        bar = "#" * bar_len
        lines.append(f"  {score:>2} | {bar} ({count})")
    return "\n".join(lines)


def _confusion_matrix_md(
    confusion: dict[str, Counter],
    top_n: int = 10,
) -> str:
    """Render a confusion matrix for the top N categories as a markdown table."""
    # Find the top N categories by total actual count
    totals = Counter()
    for actual, preds in confusion.items():
        totals[actual] += sum(preds.values())
    top_cats = [cat for cat, _ in totals.most_common(top_n)]

    if not top_cats:
        return "No data for confusion matrix."

    # Abbreviate long names for the table header
    def abbrev(name: str) -> str:
        words = name.split()
        if len(words) <= 2:
            return name
        return " ".join(w[:4] for w in words[:3])

    header_labels = [abbrev(c) for c in top_cats]

    lines = []
    header = "| Actual \\ Predicted | " + " | ".join(header_labels) + " |"
    sep = "|" + "---|" * (len(top_cats) + 1)
    lines.append(header)
    lines.append(sep)

    for actual in top_cats:
        row_label = abbrev(actual)
        cells = []
        for predicted in top_cats:
            count = confusion.get(actual, Counter()).get(predicted, 0)
            cells.append(f"**{count}**" if actual == predicted else str(count))
        lines.append(f"| {row_label} | " + " | ".join(cells) + " |")

    return "\n".join(lines)


def generate_report(
    classification: dict,
    severity: dict,
    routing: dict,
    mode: str,
    n_reports: int,
) -> str:
    """Generate the full evaluation report as markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Evaluation Report",
        "",
        f"- **Date:** {now}",
        f"- **Reports tested:** {n_reports}",
        f"- **Mode:** {mode}",
        "",
        "---",
        "",
        "## Classification Accuracy",
        "",
        f"**Overall accuracy:** {classification['accuracy']:.1%} "
        f"({classification['correct']}/{classification['total']})",
        "",
        "### Per-Category Precision",
        "",
        "| Category | Precision | Predicted Count |",
        "|---|---|---|",
    ]

    for cat in sorted(classification["precision"], key=lambda c: -classification["precision"][c]):
        p = classification["precision"][cat]
        pc = classification["predicted_counts"][cat]
        lines.append(f"| {cat} | {p:.1%} | {pc} |")

    lines += [
        "",
        "### Confusion Matrix (Top 10 Categories)",
        "",
        _confusion_matrix_md(classification["confusion"]),
        "",
        "### Top Misclassifications",
        "",
    ]

    # Find the most common misclassification pairs
    mis_pairs: Counter = Counter()
    for r in classification["results"]:
        if not r["match"]:
            mis_pairs[(r["actual_parent"], r["predicted"])] += 1

    if mis_pairs:
        lines.append("| Actual | Predicted | Count |")
        lines.append("|---|---|---|")
        for (actual, predicted), count in mis_pairs.most_common(10):
            lines.append(f"| {actual} | {predicted} | {count} |")
    else:
        lines.append("No misclassifications.")

    lines += [
        "",
        "---",
        "",
        "## Routing Accuracy",
        "",
        f"**Borough match accuracy:** {routing['accuracy']:.1%} "
        f"({routing['correct']}/{routing['total']})",
        "",
    ]

    if routing["mismatches"]:
        lines.append("### Sample Mismatches")
        lines.append("")
        lines.append("| Report ID | Actual Borough | Predicted Borough |")
        lines.append("|---|---|---|")
        for m in routing["mismatches"][:10]:
            lines.append(f"| {m['id']} | {m['actual']} | {m['predicted']} |")
    else:
        lines.append("All borough routings matched.")

    lines += [
        "",
        "---",
        "",
        "## Severity Distribution",
        "",
        f"- **Range:** {severity['min']} - {severity['max']}",
        f"- **Mean:** {severity['mean']:.1f}",
        f"- **Out of range (not 1-10):** {severity['out_of_range']}",
        "",
        "```",
        _severity_histogram(severity["distribution"]),
        "```",
        "",
        "---",
        "",
        "## Interpretation",
        "",
        "The mock provider uses keyword matching rather than LLM reasoning. "
        "Classification accuracy reflects how well keyword banks align with "
        "FixMyStreet's own category labels. With Llama 3.3 70B via NVIDIA NIM, "
        "we expect significantly higher accuracy due to semantic understanding.",
        "",
        "Routing accuracy depends on whether the report has GPS coordinates "
        "and/or a recognisable postcode in the address field. The mock provider "
        "does not affect routing since it is entirely rule-based.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    print("=" * 60)
    print("  London Civic Agent — Evaluation Framework")
    print("=" * 60)
    print()

    # Load data
    mapping = _load_category_mapping()
    reports = load_sample_reports(SAMPLE_SIZE)
    print(f"Loaded {len(reports)} sample reports from {SCRAPER_DB.name}")
    print()

    # Initialize agents in mock mode
    llm = MockProvider()
    intake = IntakeAgent(llm)
    severity_agent = SeverityAgent(llm)
    routing_agent = RoutingAgent(llm)
    mode = "mock (keyword matching)"

    # Run evaluations
    print("Running classification evaluation...")
    cls_results = evaluate_classification(reports, intake, mapping)
    print(f"  Classification accuracy: {cls_results['accuracy']:.1%}")

    print("Running severity evaluation...")
    sev_results = evaluate_severity(reports, intake, severity_agent)
    print(f"  Severity range: {sev_results['min']}-{sev_results['max']}, "
          f"mean: {sev_results['mean']:.1f}")

    print("Running routing evaluation...")
    route_results = evaluate_routing(reports, intake, routing_agent)
    print(f"  Routing accuracy: {route_results['accuracy']:.1%}")

    print()

    # Generate and write report
    report_md = generate_report(
        cls_results, sev_results, route_results, mode, len(reports)
    )

    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    report_path = docs_dir / "evaluation-report.md"
    report_path.write_text(report_md)
    print(f"Report written to {report_path}")

    # Print summary
    print()
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"  Classification accuracy:  {cls_results['accuracy']:.1%}  "
          f"({cls_results['correct']}/{cls_results['total']})")
    print(f"  Routing accuracy:         {route_results['accuracy']:.1%}  "
          f"({route_results['correct']}/{route_results['total']})")
    print(f"  Severity mean:            {sev_results['mean']:.1f}  "
          f"(range {sev_results['min']}-{sev_results['max']})")
    print(f"  Severity out of range:    {sev_results['out_of_range']}")
    print("-" * 60)


if __name__ == "__main__":
    main()
