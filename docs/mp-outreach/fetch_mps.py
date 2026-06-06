"""
Fetch all current London MPs from the UK Parliament Members API,
enrich with email + Twitter from /Contact, and save to london_mps.json.

No auth required. Respect the API — small delays between calls.

Usage:
    python3 fetch_mps.py
"""

import json
import time
import logging
from pathlib import Path

import requests

API = "https://members-api.parliament.uk/api"
OUT = Path(__file__).parent / "london_mps.json"

# Post-2024 London constituency names. The API doesn't tag constituencies as
# "London" — we filter against this list.
# Source: Wikipedia "Parliamentary constituencies in London", verified 2026.
LONDON_CONSTITUENCIES = {
    "Barking", "Battersea", "Beckenham and Penge", "Bermondsey and Old Southwark",
    "Bethnal Green and Stepney", "Bexleyheath and Crayford", "Brent East",
    "Brent West", "Brentford and Isleworth", "Bromley and Biggin Hill",
    "Carshalton and Wallington", "Chelsea and Fulham", "Chingford and Woodford Green",
    "Chipping Barnet", "Cities of London and Westminster", "Clapham and Brixton Hill",
    "Croydon East", "Croydon South", "Croydon West", "Dagenham and Rainham",
    "Dulwich and West Norwood", "Ealing Central and Acton", "Ealing North",
    "Ealing Southall", "East Ham", "Edmonton and Winchmore Hill", "Eltham and Chislehurst",
    "Enfield North", "Erith and Thamesmead", "Feltham and Heston",
    "Finchley and Golders Green", "Greenwich and Woolwich", "Hackney North and Stoke Newington",
    "Hackney South and Shoreditch", "Hammersmith and Chiswick", "Hampstead and Highgate",
    "Harrow East", "Harrow West", "Hayes and Harlington", "Hendon",
    "Holborn and St Pancras", "Hornchurch and Upminster", "Hornsey and Friern Barnet",
    "Ilford North", "Ilford South", "Islington North", "Islington South and Finsbury",
    "Kensington and Bayswater", "Kingston and Surbiton", "Leyton and Wanstead",
    "Lewisham East", "Lewisham North", "Lewisham West and East Dulwich",
    "Mitcham and Morden", "Old Bexley and Sidcup", "Orpington",
    "Peckham", "Putney", "Queen's Park and Maida Vale", "Richmond Park",
    "Romford", "Ruislip, Northwood and Pinner", "Southgate and Wood Green",
    "Stratford and Bow", "Streatham and Croydon North", "Sutton and Cheam",
    "Tooting", "Tottenham", "Twickenham", "Uxbridge and South Ruislip",
    "Vauxhall and Camberwell Green", "Walthamstow", "West Ham and Beckton",
    "Wimbledon",
}


def fetch_all_members():
    """Page through every current Commons MP."""
    members = []
    skip = 0
    take = 20
    while True:
        r = requests.get(
            f"{API}/Members/Search",
            params={
                "House": 1,  # 1 = Commons
                "IsCurrentMember": "true",
                "skip": skip,
                "take": take,
            },
            timeout=30,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            break
        members.extend(items)
        if len(items) < take:
            break
        skip += take
        time.sleep(0.1)
    return members


def fetch_contact(member_id):
    """Get email, Twitter, etc. for one MP."""
    try:
        r = requests.get(f"{API}/Members/{member_id}/Contact", timeout=15)
        r.raise_for_status()
        return r.json().get("value", [])
    except requests.RequestException:
        return []


def is_london(member):
    item = member.get("value", member)
    constituency = (item.get("latestHouseMembership") or {}).get("membershipFrom", "")
    return constituency in LONDON_CONSTITUENCIES


def normalise(member, contacts):
    item = member.get("value", member)
    membership = item.get("latestHouseMembership") or {}
    party = (item.get("latestParty") or {}).get("name", "")
    constituency = membership.get("membershipFrom", "")

    # The /Contact endpoint stores the real email under any contact's `email`
    # field (typically the "Parliamentary office" entry). Trust that first; only
    # fall back to a constructed default if nothing usable came back.
    email = None
    twitter = None
    for c in contacts:
        if c.get("email") and not email:
            email = c["email"]
        ctype = (c.get("type") or "").lower()
        if "twitter" in ctype and c.get("line1"):
            twitter = c["line1"]

    if not email:
        # Strip titles before slugging — "Dr Rosena Allin-Khan" -> "rosena.allin-khan"
        TITLES = {"mr", "mrs", "ms", "miss", "dr", "sir", "dame", "lord", "lady", "rt", "hon"}
        parts = [p for p in item["nameDisplayAs"].lower().split() if p.rstrip(".") not in TITLES]
        name_slug = ".".join(parts).replace("'", "")
        email = f"{name_slug}.mp@parliament.uk"

    return {
        "id": item["id"],
        "name": item["nameDisplayAs"],
        "party": party,
        "constituency": constituency,
        "email": email,
        "twitter": twitter,
        "profile_url": f"https://members.parliament.uk/member/{item['id']}",
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger(__name__)

    log.info("Fetching all current Commons MPs from Parliament API…")
    all_members = fetch_all_members()
    log.info("Got %d MPs total", len(all_members))

    london = [m for m in all_members if is_london(m)]
    log.info("Of those, %d are London MPs", len(london))

    enriched = []
    for i, m in enumerate(london, 1):
        item = m.get("value", m)
        contacts = fetch_contact(item["id"])
        enriched.append(normalise(m, contacts))
        if i % 10 == 0:
            log.info("Enriched %d/%d", i, len(london))
        time.sleep(0.1)

    OUT.write_text(json.dumps(enriched, indent=2, ensure_ascii=False))
    log.info("Saved %d London MPs to %s", len(enriched), OUT)


if __name__ == "__main__":
    main()
