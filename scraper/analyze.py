"""
Analyze scraped FixMyStreet data: category distribution, resolution rates, timing.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fixmystreet.db"


def analyze():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    fixed = db.execute("SELECT COUNT(*) FROM reports WHERE status = 'fixed'").fetchone()[0]
    open_ = db.execute("SELECT COUNT(*) FROM reports WHERE status = 'open'").fetchone()[0]

    print(f"{'='*60}")
    print(f"FIXMYSTREET DATA ANALYSIS")
    print(f"{'='*60}")
    print(f"Total reports: {total}")
    print(f"  Fixed: {fixed} ({fixed/total*100:.1f}%)" if total else "")
    print(f"  Open:  {open_} ({open_/total*100:.1f}%)" if total else "")
    print()

    # Borough distribution
    print(f"{'='*60}")
    print("REPORTS BY BOROUGH")
    print(f"{'='*60}")
    rows = db.execute(
        """SELECT borough, COUNT(*) as n,
           SUM(CASE WHEN status='fixed' THEN 1 ELSE 0 END) as fixed,
           AVG(CASE WHEN resolution_days IS NOT NULL THEN resolution_days END) as avg_days,
           MIN(CASE WHEN resolution_days IS NOT NULL THEN resolution_days END) as min_days,
           MAX(CASE WHEN resolution_days IS NOT NULL THEN resolution_days END) as max_days
           FROM reports GROUP BY borough ORDER BY n DESC"""
    ).fetchall()
    print(f"{'Borough':<20} {'Total':>6} {'Fixed':>6} {'Fix%':>6} {'Avg Days':>10} {'Min':>6} {'Max':>8}")
    print(f"{'-'*20} {'-'*6} {'-'*6} {'-'*6} {'-'*10} {'-'*6} {'-'*8}")
    for r in rows:
        fix_pct = f"{r['fixed']/r['n']*100:.0f}%" if r['n'] else "n/a"
        avg = f"{r['avg_days']:.1f}" if r['avg_days'] else "n/a"
        mn = f"{r['min_days']:.1f}" if r['min_days'] is not None else "n/a"
        mx = f"{r['max_days']:.0f}" if r['max_days'] is not None else "n/a"
        print(f"{r['borough']:<20} {r['n']:>6} {r['fixed']:>6} {fix_pct:>6} {avg:>10} {mn:>6} {mx:>8}")
    print()

    # Category distribution
    print(f"{'='*60}")
    print("CATEGORY DISTRIBUTION")
    print(f"{'='*60}")
    rows = db.execute(
        """SELECT category, COUNT(*) as n,
           ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM reports),1) as pct,
           AVG(CASE WHEN resolution_days IS NOT NULL THEN resolution_days END) as avg_days
           FROM reports WHERE category != ''
           GROUP BY category ORDER BY n DESC LIMIT 25"""
    ).fetchall()
    print(f"{'Category':<35} {'Count':>6} {'%':>6} {'Avg Fix Days':>13}")
    print(f"{'-'*35} {'-'*6} {'-'*6} {'-'*13}")
    for r in rows:
        avg = f"{r['avg_days']:.1f}" if r['avg_days'] else "n/a"
        print(f"{r['category']:<35} {r['n']:>6} {r['pct']:>5}% {avg:>13}")
    print()

    # Resolution time distribution
    print(f"{'='*60}")
    print("RESOLUTION TIME DISTRIBUTION (fixed reports only)")
    print(f"{'='*60}")
    with_time = db.execute(
        "SELECT COUNT(*) FROM reports WHERE resolution_days IS NOT NULL"
    ).fetchone()[0]
    if with_time:
        brackets = [
            ("Same day (< 1 day)", 0, 1),
            ("1-3 days", 1, 3),
            ("3-7 days", 3, 7),
            ("1-2 weeks", 7, 14),
            ("2-4 weeks", 14, 28),
            ("1-3 months", 28, 90),
            ("3-6 months", 90, 180),
            ("6+ months", 180, 99999),
        ]
        print(f"Reports with resolution time data: {with_time}")
        print()
        print(f"{'Bracket':<25} {'Count':>6} {'%':>6}")
        print(f"{'-'*25} {'-'*6} {'-'*6}")
        for label, lo, hi in brackets:
            n = db.execute(
                "SELECT COUNT(*) FROM reports WHERE resolution_days >= ? AND resolution_days < ?",
                (lo, hi),
            ).fetchone()[0]
            pct = f"{n/with_time*100:.1f}" if with_time else "0"
            print(f"{label:<25} {n:>6} {pct:>5}%")

        median = db.execute(
            """SELECT resolution_days FROM reports
               WHERE resolution_days IS NOT NULL
               ORDER BY resolution_days
               LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM reports WHERE resolution_days IS NOT NULL)"""
        ).fetchone()
        avg = db.execute(
            "SELECT AVG(resolution_days) FROM reports WHERE resolution_days IS NOT NULL"
        ).fetchone()[0]
        print()
        print(f"Median resolution time: {median[0]:.1f} days" if median else "")
        print(f"Average resolution time: {avg:.1f} days" if avg else "")
    else:
        print("No resolution time data available.")

    print()
    db.close()


if __name__ == "__main__":
    analyze()
