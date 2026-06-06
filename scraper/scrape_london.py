"""
Scrape FixMyStreet reports across ALL 33 London local authorities.

Scrapes both `fixed` and `open` reports. Uses FixMyStreet's borough listing
pages with a 3-second crawl delay per request (robots.txt compliant).

Run from the repo root:

    PYTHONPATH=scraper .venv/bin/python scraper/scrape_london.py
    PYTHONPATH=scraper .venv/bin/python scraper/scrape_london.py --remaining

By default this resumes — it scrapes only boroughs that don't already have
~150 reports in the DB, which makes it safe to re-run.
"""

import argparse
import logging
import sys

from scrape import scrape_borough
from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# All 33 London local authorities. Each entry is the FixMyStreet URL slug
# (which doubles as the value we store in `borough`).
# Note: "City of London" on FixMyStreet uses the full corporation name.
ALL_BOROUGHS = [
    "Barking and Dagenham",
    "Barnet",
    "Bexley",
    "Brent",
    "Bromley",
    "Camden",
    "City of London Corporation",
    "Croydon",
    "Ealing",
    "Enfield",
    "Greenwich",
    "Hackney",
    "Hammersmith and Fulham",
    "Haringey",
    "Harrow",
    "Havering",
    "Hillingdon",
    "Hounslow",
    "Islington",
    "Kensington and Chelsea",
    "Kingston upon Thames",
    "Lambeth",
    "Lewisham",
    "Merton",
    "Newham",
    "Redbridge",
    "Richmond upon Thames",
    "Southwark",
    "Sutton",
    "Tower Hamlets",
    "Waltham Forest",
    "Wandsworth",
    "Westminster",
]

# Boroughs already scraped (per the brief). We will skip these unless --all is used.
ALREADY_SCRAPED = {
    "Barnet",
    "Bromley",
    "Camden",
    "Greenwich",
    "Hackney",
    "Islington",
    "Lewisham",
    "Southwark",
    "Westminster",
}


def existing_counts():
    db = get_db()
    rows = db.execute(
        "SELECT borough, COUNT(*) AS n FROM reports GROUP BY borough"
    ).fetchall()
    db.close()
    return {r["borough"]: r["n"] for r in rows}


def main():
    parser = argparse.ArgumentParser(description="Scrape FixMyStreet across London")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-scrape ALL 33 boroughs (default: skip the 9 already scraped)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=2,
        help="Listing pages per (borough, status) pair. 2 pages = up to 200 reports.",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="How far back to look (months).",
    )
    parser.add_argument(
        "--min-existing",
        type=int,
        default=150,
        help="Resume mode: skip boroughs that already have at least this many rows.",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated borough list to override the default selection.",
    )
    args = parser.parse_args()

    if args.only:
        boroughs = [b.strip() for b in args.only.split(",") if b.strip()]
    elif args.all:
        boroughs = list(ALL_BOROUGHS)
    else:
        boroughs = [b for b in ALL_BOROUGHS if b not in ALREADY_SCRAPED]

    counts = existing_counts()

    log.info("=== London-wide scrape: %d boroughs queued ===", len(boroughs))
    for b in boroughs:
        log.info("  %s (existing rows: %d)", b, counts.get(b, 0))

    total_new = 0
    for borough in boroughs:
        existing = counts.get(borough, 0)
        if existing >= args.min_existing and not args.only and not args.all:
            log.info("=== SKIP %s (already has %d rows) ===", borough, existing)
            continue

        log.info("=== Starting %s ===", borough)
        for status in ("fixed", "open"):
            try:
                n = scrape_borough(
                    borough,
                    months_back=args.months,
                    max_pages=args.max_pages,
                    status=status,
                )
                total_new += n
                log.info("  %s/%s: %d new reports", borough, status, n)
            except Exception as e:
                log.error("  Failed on %s/%s: %s", borough, status, e)

    log.info("=== TOTAL NEW: %d reports across %d boroughs ===", total_new, len(boroughs))


if __name__ == "__main__":
    main()
