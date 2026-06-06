"""
FixMyStreet scraper for London borough reports.

Respects robots.txt: 3-second crawl delay between requests.
Only scrapes publicly allowed pages (/reports/, /report/{id}).
"""

import re
import json
import time
import logging
import argparse
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from db import get_db, upsert_report, insert_updates

BASE_URL = "https://www.fixmystreet.com"
CRAWL_DELAY = 3
REPORTS_PER_PAGE = 100

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


def fetch(url):
    time.sleep(CRAWL_DELAY)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp


def scrape_listing_page(borough, page, status=None):
    params = f"?p={page}"
    if status:
        params += f"&status={status}"
    url = f"{BASE_URL}/reports/{borough}{params}"
    log.info("Listing page %d: %s", page, url)
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "lxml")

    items = soup.select("li[data-report-id]")
    reports = []
    for item in items:
        report_id = int(item["data-report-id"])
        last_update = item.get("data-lastupdate", "")

        title_el = item.select_one("h3.item-list__heading a, h3 a")
        title = title_el.get_text(strip=True) if title_el else ""

        addr_el = item.select_one("span.visuallyhidden")
        address = addr_el.get_text(strip=True) if addr_el else ""

        reports.append({
            "id": report_id,
            "title": title,
            "address": address,
            "updated_at": last_update,
        })

    nav_links = soup.select(".pagination a, .nav-previous-next a, a[rel='next']")
    has_next = any(
        a.get("rel") == ["next"] or "next" in a.get_text(strip=True).lower()
        for a in nav_links
    )

    return reports, has_next


def scrape_report_detail(report_id):
    url = f"{BASE_URL}/report/{report_id}"
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "lxml")

    title_el = soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    category = ""
    cat_match = re.search(r"in the (.+?) category", soup.get_text())
    if cat_match:
        category = cat_match.group(1).strip()

    desc_el = soup.select_one(".moderate-display p, .moderate-display")
    description = ""
    if desc_el:
        paragraphs = desc_el.find_all("p") if desc_el.name != "p" else [desc_el]
        description = "\n".join(p.get_text(strip=True) for p in paragraphs)
    if not description and desc_el:
        description = desc_el.get_text(strip=True)

    lat, lng = None, None
    map_el = soup.select_one("[data-latitude]")
    if map_el:
        lat = float(map_el["data-latitude"])
        lng = float(map_el["data-longitude"])

    council = ""
    council_match = re.search(r"Sent to (.+?Council)", soup.get_text())
    if council_match:
        council = council_match.group(1).strip()

    created_at = ""
    time_el = soup.select_one("time[datetime]")
    if time_el:
        created_at = time_el.get("datetime", "")
    if not created_at:
        date_match = re.search(
            r"at (\d{2}:\d{2}),\s+\w+\s+(\d{1,2}\s+\w+\s+\d{4})",
            soup.get_text(),
        )
        if date_match:
            try:
                raw = f"{date_match.group(2)} {date_match.group(1)}"
                dt = datetime.strptime(raw, "%d %B %Y %H:%M")
                created_at = dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass

    photos = []
    for img in soup.select("img[src*='/photo/']"):
        src = img.get("src", "")
        if src:
            full = re.sub(r"\.\d+\.fp\.jpeg", ".jpeg", src)
            if not full.startswith("http"):
                full = BASE_URL + full
            photos.append(full)

    updates = []
    for update_el in soup.select(".item-list__item--updates"):
        raw_text = update_el.get_text(" ", strip=True)
        ts = ""
        ts_match = re.search(
            r"at (\d{2}:\d{2}),\s+\w+\s+(\d{1,2}\s+\w+\s+\d{4})",
            raw_text,
        )
        if ts_match:
            try:
                raw_ts = f"{ts_match.group(2)} {ts_match.group(1)}"
                dt_u = datetime.strptime(raw_ts, "%d %B %Y %H:%M")
                ts = dt_u.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass
        updates.append({
            "text": raw_text,
            "timestamp": ts,
        })

    resolved_at = None
    resolution_days = None
    for u in updates:
        if "fixed" in u["text"].lower() and u["timestamp"]:
            resolved_at = u["timestamp"]
            break
    if resolved_at and created_at:
        try:
            ct = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            rt = datetime.fromisoformat(resolved_at.replace("Z", "+00:00"))
            if ct.tzinfo is None:
                ct = ct.replace(tzinfo=timezone.utc)
            if rt.tzinfo is None:
                rt = rt.replace(tzinfo=timezone.utc)
            resolution_days = (rt - ct).total_seconds() / 86400
        except ValueError:
            pass

    return {
        "title": title,
        "category": category,
        "description": description,
        "latitude": lat,
        "longitude": lng,
        "council": council,
        "created_at": created_at,
        "photo_urls": json.dumps(photos) if photos else None,
        "updates": updates,
        "resolved_at": resolved_at,
        "resolution_days": resolution_days,
    }


def scrape_borough(borough, months_back=3, max_pages=None, status=None):
    db = get_db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)
    page = 1
    total_scraped = 0
    total_skipped = 0
    hit_cutoff = False

    status_label = f" [status={status}]" if status else ""
    log.info("Scraping %s%s (last %d months, cutoff %s)", borough, status_label, months_back, cutoff.date())

    while True:
        listings, has_next = scrape_listing_page(borough, page, status=status)

        if not listings:
            log.info("No reports on page %d, stopping.", page)
            break

        for item in listings:
            updated = item.get("updated_at", "")
            if updated:
                try:
                    dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt < cutoff:
                        hit_cutoff = True
                        total_skipped += 1
                        continue
                except ValueError:
                    pass

            existing = db.execute(
                "SELECT id FROM reports WHERE id = ?", (item["id"],)
            ).fetchone()
            if existing:
                total_skipped += 1
                continue

            try:
                detail = scrape_report_detail(item["id"])
            except Exception as e:
                log.warning("Failed to scrape report %d: %s", item["id"], e)
                continue

            report = {
                "id": item["id"],
                "title": detail["title"] or item["title"],
                "category": detail["category"],
                "description": detail["description"],
                "latitude": detail["latitude"],
                "longitude": detail["longitude"],
                "address": item["address"],
                "borough": borough,
                "council": detail["council"],
                "status": status or "open",
                "created_at": detail["created_at"],
                "updated_at": item["updated_at"],
                "photo_urls": detail["photo_urls"],
                "resolved_at": detail.get("resolved_at"),
                "resolution_days": detail.get("resolution_days"),
                "source": "fixmystreet",
                "source_url": f"{BASE_URL}/report/{item['id']}",
                "report_count": 1,
            }

            upsert_report(db, report)
            if detail["updates"]:
                insert_updates(db, item["id"], detail["updates"])
            db.commit()

            total_scraped += 1
            if total_scraped % 10 == 0:
                log.info("Progress: %d scraped, %d skipped", total_scraped, total_skipped)

        def _past_cutoff(updated):
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                return False
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt < cutoff

        dated = [i for i in listings if i.get("updated_at")]
        if hit_cutoff and dated and all(_past_cutoff(i["updated_at"]) for i in dated):
            log.info("All reports on page %d are past cutoff, stopping.", page)
            break

        if not has_next:
            log.info("No more pages.")
            break

        if max_pages and page >= max_pages:
            log.info("Reached max pages (%d).", max_pages)
            break

        page += 1

    db.close()
    log.info("Done. Scraped %d new reports, skipped %d.", total_scraped, total_skipped)
    return total_scraped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape FixMyStreet reports")
    parser.add_argument("borough", help="Borough name (e.g. Islington)")
    parser.add_argument("--months", type=int, default=3, help="Months of history to scrape")
    parser.add_argument("--max-pages", type=int, default=None, help="Max listing pages to scrape")
    parser.add_argument("--status", choices=["open", "fixed", "closed"], help="Filter by report status")
    args = parser.parse_args()

    scrape_borough(args.borough, months_back=args.months, max_pages=args.max_pages, status=args.status)
