"""
Download photos from scraped FixMyStreet reports.

Stores files under scraper/photos/{report_id}_{idx}.jpeg and updates the
reports table's `photo_paths` column with a JSON array of relative paths.

Respects FixMyStreet's 3-second crawl delay. Re-runs are safe — existing
files and DB rows with photo_paths already set are skipped.
"""

import json
import time
import logging
import argparse
from pathlib import Path

import requests

from db import get_db

CRAWL_DELAY = 3
PHOTO_DIR = Path(__file__).parent / "photos"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": "LondonCivicAgent-Scraper/0.1 (hackathon research project)",
})


def download_photos(borough=None, limit=None, skip_existing_rows=True):
    db = get_db()
    PHOTO_DIR.mkdir(exist_ok=True)

    query = (
        "SELECT id, borough, photo_urls, photo_paths "
        "FROM reports WHERE photo_urls IS NOT NULL"
    )
    params = []
    if borough:
        query += " AND borough = ?"
        params.append(borough)
    if skip_existing_rows:
        query += " AND (photo_paths IS NULL OR photo_paths = '')"
    if limit:
        query += f" LIMIT {int(limit)}"

    rows = db.execute(query, params).fetchall()
    log.info("Found %d reports with photos to fetch.", len(rows))

    downloaded = 0
    skipped_files = 0
    failed = 0

    for row in rows:
        report_id = row["id"]
        urls = json.loads(row["photo_urls"])
        local_paths = []

        for i, url in enumerate(urls):
            filename = f"{report_id}_{i}.jpeg"
            filepath = PHOTO_DIR / filename

            if filepath.exists() and filepath.stat().st_size > 0:
                skipped_files += 1
                local_paths.append(f"photos/{filename}")
                continue

            try:
                time.sleep(CRAWL_DELAY)
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
                filepath.write_bytes(resp.content)
                local_paths.append(f"photos/{filename}")
                downloaded += 1
                if downloaded % 10 == 0:
                    log.info(
                        "Progress: downloaded=%d skipped=%d failed=%d",
                        downloaded,
                        skipped_files,
                        failed,
                    )
            except Exception as e:
                failed += 1
                log.warning("Failed to download %s: %s", url, e)

        if local_paths:
            db.execute(
                "UPDATE reports SET photo_paths = ? WHERE id = ?",
                (json.dumps(local_paths), report_id),
            )
            db.commit()

    db.close()
    log.info(
        "Done. Downloaded=%d, file-skips=%d, failed=%d",
        downloaded,
        skipped_files,
        failed,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download photos from scraped reports")
    parser.add_argument("--borough", help="Filter by borough")
    parser.add_argument("--limit", type=int, help="Max reports to download photos from")
    parser.add_argument(
        "--redo",
        action="store_true",
        help="Re-check rows whose photo_paths is already set (useful after a partial run).",
    )
    args = parser.parse_args()

    download_photos(
        borough=args.borough,
        limit=args.limit,
        skip_existing_rows=not args.redo,
    )
