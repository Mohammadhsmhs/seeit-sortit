"""
Deep analysis of FixMyStreet data for the London Civic Agent project.
Generates docs/fixmystreet-analysis.md with comprehensive findings.

Usage:
    python scraper/deep_analysis.py
"""

import sqlite3
import re
from collections import Counter
from pathlib import Path
from statistics import median as stat_median

DB_PATH = Path(__file__).parent / "fixmystreet.db"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "fixmystreet-analysis.md"

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "this", "that", "are", "was",
    "be", "has", "have", "had", "not", "no", "been", "which", "as", "its",
    "they", "their", "there", "also", "very", "can", "will", "do", "does",
    "did", "would", "could", "should", "may", "might", "i", "we", "you",
    "he", "she", "my", "our", "your", "all", "if", "so", "up", "out",
    "about", "into", "over", "after", "than", "them", "then", "just",
    "some", "other", "what", "when", "where", "who", "how", "each",
    "were", "being", "these", "those", "through", "during", "before",
    "between", "both", "same", "any", "here", "such", "only", "own",
    "more", "get", "one", "two", "new", "now", "way", "like", "well",
    "back", "still", "see", "make", "much", "need", "going", "got",
    "around", "since", "off", "down", "long", "been", "because", "too",
}


def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def section_volume(db):
    """Section 2: Volume Analysis"""
    lines = []
    lines.append("## 2. Volume Analysis\n")

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    lines.append(f"**Total reports in database:** {total}\n")

    # By borough
    lines.append("### Reports by Borough\n")
    lines.append("| Borough | Count | % of Total |")
    lines.append("|---------|------:|----------:|")
    rows = db.execute(
        "SELECT borough, COUNT(*) as n FROM reports GROUP BY borough ORDER BY n DESC"
    ).fetchall()
    for r in rows:
        pct = r["n"] / total * 100
        lines.append(f"| {r['borough']} | {r['n']} | {pct:.1f}% |")
    lines.append("")

    # By category top 20
    lines.append("### Top 20 Categories\n")
    lines.append("| Rank | Category | Count | % of Total |")
    lines.append("|-----:|----------|------:|----------:|")
    rows = db.execute(
        """SELECT category, COUNT(*) as n
           FROM reports WHERE category IS NOT NULL AND category != ''
           GROUP BY category ORDER BY n DESC LIMIT 20"""
    ).fetchall()
    for i, r in enumerate(rows, 1):
        pct = r["n"] / total * 100
        lines.append(f"| {i} | {r['category']} | {r['n']} | {pct:.1f}% |")

    # Category count for "other"
    all_cats = db.execute(
        "SELECT COUNT(DISTINCT category) FROM reports WHERE category IS NOT NULL AND category != ''"
    ).fetchone()[0]
    lines.append(f"\n*{all_cats} distinct categories total across all boroughs.*\n")

    # By quarter/year if dates available
    lines.append("### Reports by Year Created\n")
    rows = db.execute(
        """SELECT SUBSTR(created_at, 1, 4) as year, COUNT(*) as n
           FROM reports WHERE created_at IS NOT NULL AND created_at != ''
           GROUP BY year ORDER BY year"""
    ).fetchall()
    if rows:
        lines.append("| Year | Count |")
        lines.append("|------|------:|")
        for r in rows:
            lines.append(f"| {r['year']} | {r['n']} |")
    lines.append("")

    lines.append("### Reports by Quarter (top periods)\n")
    rows = db.execute(
        """SELECT SUBSTR(created_at, 1, 4) as year,
                  CASE
                    WHEN CAST(SUBSTR(created_at, 6, 2) AS INTEGER) <= 3 THEN 'Q1'
                    WHEN CAST(SUBSTR(created_at, 6, 2) AS INTEGER) <= 6 THEN 'Q2'
                    WHEN CAST(SUBSTR(created_at, 6, 2) AS INTEGER) <= 9 THEN 'Q3'
                    ELSE 'Q4'
                  END as quarter,
                  COUNT(*) as n
           FROM reports WHERE created_at IS NOT NULL AND created_at != ''
           GROUP BY year, quarter ORDER BY n DESC LIMIT 12"""
    ).fetchall()
    if rows:
        lines.append("| Period | Count |")
        lines.append("|--------|------:|")
        for r in rows:
            lines.append(f"| {r['year']} {r['quarter']} | {r['n']} |")
    lines.append("")

    return "\n".join(lines)


def section_resolution(db):
    """Section 3: Resolution Performance"""
    lines = []
    lines.append("## 3. Resolution Performance\n")

    total_with_res = db.execute(
        "SELECT COUNT(*) FROM reports WHERE resolution_days IS NOT NULL"
    ).fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    lines.append(
        f"**Reports with resolution time data:** {total_with_res} of {total} "
        f"({total_with_res / total * 100:.1f}%)\n"
    )

    # Overall stats
    stats = db.execute(
        """SELECT AVG(resolution_days) as avg_d,
                  MIN(resolution_days) as min_d,
                  MAX(resolution_days) as max_d
           FROM reports WHERE resolution_days IS NOT NULL"""
    ).fetchone()
    all_days = [
        r[0]
        for r in db.execute(
            "SELECT resolution_days FROM reports WHERE resolution_days IS NOT NULL ORDER BY resolution_days"
        ).fetchall()
    ]
    med = stat_median(all_days) if all_days else 0

    lines.append("### Overall Resolution Stats\n")
    lines.append(f"- **Average:** {stats['avg_d']:.1f} days")
    lines.append(f"- **Median:** {med:.1f} days")
    lines.append(f"- **Fastest:** {stats['min_d']:.2f} days ({stats['min_d'] * 24:.1f} hours)")
    lines.append(f"- **Slowest:** {stats['max_d']:.0f} days ({stats['max_d'] / 365:.1f} years)")
    lines.append("")

    # By borough
    lines.append("### Resolution Time by Borough\n")
    lines.append("| Borough | Avg (days) | Median (days) | Min (days) | Max (days) | Reports w/ data |")
    lines.append("|---------|----------:|-------------:|----------:|----------:|---------------:|")
    boroughs = db.execute("SELECT DISTINCT borough FROM reports ORDER BY borough").fetchall()
    borough_stats = []
    for b in boroughs:
        bname = b["borough"]
        brows = [
            r[0]
            for r in db.execute(
                "SELECT resolution_days FROM reports WHERE borough = ? AND resolution_days IS NOT NULL ORDER BY resolution_days",
                (bname,),
            ).fetchall()
        ]
        if brows:
            bavg = sum(brows) / len(brows)
            bmed = stat_median(brows)
            bmin = min(brows)
            bmax = max(brows)
            borough_stats.append((bname, bavg, bmed, bmin, bmax, len(brows)))
            lines.append(
                f"| {bname} | {bavg:.1f} | {bmed:.1f} | {bmin:.2f} | {bmax:.0f} | {len(brows)} |"
            )

    lines.append("")

    # Borough ranking
    lines.append("### Borough Performance Ranking (fastest median resolution)\n")
    ranked = sorted(borough_stats, key=lambda x: x[2])
    for i, (bname, bavg, bmed, bmin, bmax, cnt) in enumerate(ranked, 1):
        lines.append(f"{i}. **{bname}** -- median {bmed:.1f} days (avg {bavg:.1f} days)")
    lines.append("")

    # By category
    lines.append("### Resolution Time by Category (top 15 by volume)\n")
    lines.append("| Category | Avg (days) | Median (days) | Count |")
    lines.append("|----------|----------:|-------------:|------:|")
    cats = db.execute(
        """SELECT category, COUNT(*) as n
           FROM reports
           WHERE resolution_days IS NOT NULL AND category IS NOT NULL AND category != ''
           GROUP BY category ORDER BY n DESC LIMIT 15"""
    ).fetchall()
    cat_stats = []
    for c in cats:
        cname = c["category"]
        crows = [
            r[0]
            for r in db.execute(
                "SELECT resolution_days FROM reports WHERE category = ? AND resolution_days IS NOT NULL ORDER BY resolution_days",
                (cname,),
            ).fetchall()
        ]
        if crows:
            cavg = sum(crows) / len(crows)
            cmed = stat_median(crows)
            cat_stats.append((cname, cavg, cmed, len(crows)))
            lines.append(f"| {cname} | {cavg:.1f} | {cmed:.1f} | {len(crows)} |")
    lines.append("")

    # Fastest vs slowest categories
    if cat_stats:
        lines.append("### Fastest vs Slowest Categories (by median, min 3 reports)\n")
        filtered = [c for c in cat_stats if c[3] >= 3]
        fastest = sorted(filtered, key=lambda x: x[2])[:5]
        slowest = sorted(filtered, key=lambda x: x[2], reverse=True)[:5]

        lines.append("**Fastest to resolve:**\n")
        for cname, cavg, cmed, cnt in fastest:
            lines.append(f"- {cname}: median {cmed:.1f} days ({cnt} reports)")

        lines.append("\n**Slowest to resolve:**\n")
        for cname, cavg, cmed, cnt in slowest:
            lines.append(f"- {cname}: median {cmed:.1f} days ({cnt} reports)")
        lines.append("")

    # Distribution brackets
    lines.append("### Resolution Time Distribution\n")
    brackets = [
        ("Same day (< 1 day)", 0, 1),
        ("1-3 days", 1, 3),
        ("3-7 days (< 1 week)", 3, 7),
        ("1-2 weeks", 7, 14),
        ("2-4 weeks", 14, 28),
        ("1-3 months", 28, 90),
        ("3-6 months", 90, 180),
        ("6-12 months", 180, 365),
        ("1+ year", 365, 999999),
    ]
    lines.append("| Bracket | Count | % |")
    lines.append("|---------|------:|--:|")
    for label, lo, hi in brackets:
        n = db.execute(
            "SELECT COUNT(*) FROM reports WHERE resolution_days IS NOT NULL AND resolution_days >= ? AND resolution_days < ?",
            (lo, hi),
        ).fetchone()[0]
        pct = n / total_with_res * 100 if total_with_res else 0
        lines.append(f"| {label} | {n} | {pct:.1f}% |")
    lines.append("")

    return "\n".join(lines)


def section_geographic(db):
    """Section 4: Geographic Analysis"""
    lines = []
    lines.append("## 4. Geographic Analysis\n")

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    with_coords = db.execute(
        "SELECT COUNT(*) FROM reports WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchone()[0]
    lines.append(
        f"**Reports with valid coordinates:** {with_coords} of {total} ({with_coords / total * 100:.1f}%)\n"
    )

    # Bounding box per borough
    lines.append("### Geographic Bounding Box by Borough\n")
    lines.append("| Borough | Min Lat | Max Lat | Min Lon | Max Lon | Lat Spread | Lon Spread |")
    lines.append("|---------|--------:|--------:|--------:|--------:|----------:|----------:|")
    boroughs = db.execute(
        """SELECT borough,
                  MIN(latitude) as min_lat, MAX(latitude) as max_lat,
                  MIN(longitude) as min_lon, MAX(longitude) as max_lon,
                  COUNT(*) as n
           FROM reports
           WHERE latitude IS NOT NULL AND longitude IS NOT NULL
           GROUP BY borough ORDER BY borough"""
    ).fetchall()
    for b in boroughs:
        lat_spread = b["max_lat"] - b["min_lat"]
        lon_spread = b["max_lon"] - b["min_lon"]
        lines.append(
            f"| {b['borough']} | {b['min_lat']:.4f} | {b['max_lat']:.4f} | "
            f"{b['min_lon']:.4f} | {b['max_lon']:.4f} | {lat_spread:.4f} | {lon_spread:.4f} |"
        )
    lines.append("")

    # Clustering -- look at address street frequency
    lines.append("### Most Reported Streets/Locations\n")
    # Extract street names from addresses
    rows = db.execute(
        "SELECT address, borough FROM reports WHERE address IS NOT NULL AND address != ''"
    ).fetchall()
    street_counter = Counter()
    for r in rows:
        addr = r["address"]
        # Take the first part of address (street name)
        parts = addr.split(",")
        if parts:
            street = parts[0].strip()
            # Remove house numbers
            street_clean = re.sub(r"^\d+[-\d]*\s*", "", street).strip()
            if street_clean and len(street_clean) > 3:
                street_counter[(street_clean, r["borough"])] += 1

    lines.append("| Street/Location | Borough | Reports |")
    lines.append("|-----------------|---------|--------:|")
    for (street, borough), count in street_counter.most_common(15):
        lines.append(f"| {street} | {borough} | {count} |")
    lines.append("")

    return "\n".join(lines)


def section_content(db):
    """Section 5: Content Analysis"""
    lines = []
    lines.append("## 5. Content Analysis\n")

    # Description lengths
    descs = db.execute(
        "SELECT description FROM reports WHERE description IS NOT NULL AND description != ''"
    ).fetchall()
    real_descs = [d["description"] for d in descs if d["description"].strip() not in (".", "")]
    lengths = [len(d) for d in real_descs]

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    lines.append("### Description Quality\n")
    lines.append(f"- **Reports with meaningful descriptions:** {len(real_descs)} of {total} ({len(real_descs)/total*100:.1f}%)")
    if lengths:
        lines.append(f"- **Average description length:** {sum(lengths)/len(lengths):.0f} characters")
        lines.append(f"- **Median description length:** {stat_median(lengths):.0f} characters")
        lines.append(f"- **Shortest:** {min(lengths)} characters")
        lines.append(f"- **Longest:** {max(lengths)} characters")

    # Reports with just "." as description
    dot_descs = db.execute(
        "SELECT COUNT(*) FROM reports WHERE description = '.'"
    ).fetchone()[0]
    empty_descs = db.execute(
        "SELECT COUNT(*) FROM reports WHERE description IS NULL OR description = ''"
    ).fetchone()[0]
    lines.append(f"- **Reports with placeholder description ('.'):** {dot_descs}")
    lines.append(f"- **Reports with empty/null description:** {empty_descs}")
    lines.append("")

    # Most common words
    word_counter = Counter()
    for desc in real_descs:
        words = re.findall(r"[a-z]+", desc.lower())
        for w in words:
            if w not in STOPWORDS and len(w) > 2:
                word_counter[w] += 1

    lines.append("### Most Common Words in Descriptions (excluding stopwords)\n")
    lines.append("| Rank | Word | Occurrences |")
    lines.append("|-----:|------|----------:|")
    for i, (word, count) in enumerate(word_counter.most_common(30), 1):
        lines.append(f"| {i} | {word} | {count} |")
    lines.append("")

    # Photos
    lines.append("### Photo Attachment Rate\n")
    with_photos = db.execute(
        "SELECT COUNT(*) FROM reports WHERE photo_urls IS NOT NULL AND photo_urls != '[]' AND photo_urls != ''"
    ).fetchone()[0]
    without_photos = total - with_photos
    lines.append(f"- **Reports with photos:** {with_photos} ({with_photos/total*100:.1f}%)")
    lines.append(f"- **Reports without photos:** {without_photos} ({without_photos/total*100:.1f}%)")

    # Photos by borough
    lines.append("")
    lines.append("| Borough | With Photos | Without | Photo Rate |")
    lines.append("|---------|----------:|--------:|----------:|")
    boroughs = db.execute(
        """SELECT borough,
                  SUM(CASE WHEN photo_urls IS NOT NULL AND photo_urls != '[]' AND photo_urls != '' THEN 1 ELSE 0 END) as with_p,
                  SUM(CASE WHEN photo_urls IS NULL OR photo_urls = '[]' OR photo_urls = '' THEN 1 ELSE 0 END) as without_p,
                  COUNT(*) as n
           FROM reports GROUP BY borough ORDER BY borough"""
    ).fetchall()
    for b in boroughs:
        rate = b["with_p"] / b["n"] * 100 if b["n"] else 0
        lines.append(f"| {b['borough']} | {b['with_p']} | {b['without_p']} | {rate:.0f}% |")
    lines.append("")

    # Urgency signals
    lines.append("### Urgency Signals in Descriptions\n")
    urgency_patterns = [
        ("dangerous/danger", r"\bdanger(?:ous)?\b"),
        ("hazard/hazardous", r"\bhazard(?:ous)?\b"),
        ("urgent/urgently", r"\burgent(?:ly)?\b"),
        ("immediately/immediate", r"\bimmediate(?:ly)?\b"),
        ("accident/injury", r"\b(?:accident|injur(?:y|ies|ed))\b"),
        ("children/kids/school", r"\b(?:children|kids|school|child)\b"),
        ("elderly/disabled", r"\b(?:elderly|disabled|wheelchair|blind)\b"),
        ("falling/fallen/collapse", r"\b(?:fall(?:ing|en)?|collaps(?:e|ed|ing))\b"),
        ("flood/flooding", r"\bflood(?:ing|ed)?\b"),
        ("broken glass", r"\bbroken\s+glass\b"),
        ("blocked/blocking", r"\bblock(?:ed|ing)\b"),
        ("trip/tripping", r"\btrip(?:ping)?\b"),
        ("smashed/smash", r"\bsmash(?:ed|ing)?\b"),
    ]
    lines.append("| Signal Pattern | Occurrences | Example Report Title |")
    lines.append("|----------------|----------:|----------------------|")
    all_reports = db.execute(
        "SELECT title, description FROM reports WHERE description IS NOT NULL"
    ).fetchall()
    for label, pattern in urgency_patterns:
        count = 0
        example = ""
        for r in all_reports:
            text = f"{r['title'] or ''} {r['description'] or ''}".lower()
            if re.search(pattern, text):
                count += 1
                if not example:
                    example = (r["title"] or "")[:60]
        lines.append(f"| {label} | {count} | {example} |")
    lines.append("")

    return "\n".join(lines)


def section_product_insights(db):
    """Section 6: Insights for the Product"""
    lines = []
    lines.append("## 6. Insights for the Product\n")

    # Intake classifier priorities
    lines.append("### Category Prioritization for Intake Classifier\n")
    lines.append(
        "Categories ranked by volume -- these should be the primary targets for "
        "the intake classifier. Covering the top 10 captures the vast majority of reports.\n"
    )
    rows = db.execute(
        """SELECT category, COUNT(*) as n,
                  ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM reports), 1) as pct
           FROM reports WHERE category IS NOT NULL AND category != ''
           GROUP BY category ORDER BY n DESC"""
    ).fetchall()
    cumulative = 0
    lines.append("| Priority | Category | Count | % | Cumulative % |")
    lines.append("|:--------:|----------|------:|--:|:------------:|")
    for i, r in enumerate(rows, 1):
        cumulative += r["pct"]
        lines.append(f"| {i} | {r['category']} | {r['n']} | {r['pct']}% | {cumulative:.1f}% |")
        if i >= 15:
            break
    lines.append("")

    # Severity signals
    lines.append("### Severity Signals from Historical Data\n")
    lines.append("Based on analysis of resolution times and content, these signals can help estimate severity:\n")

    # Compare resolution times for reports with urgency words vs without
    urgent_days = db.execute(
        """SELECT AVG(resolution_days) as avg_d FROM reports
           WHERE resolution_days IS NOT NULL
           AND (LOWER(description) LIKE '%danger%'
                OR LOWER(description) LIKE '%hazard%'
                OR LOWER(description) LIKE '%urgent%'
                OR LOWER(description) LIKE '%immediate%'
                OR LOWER(description) LIKE '%accident%'
                OR LOWER(description) LIKE '%injur%')"""
    ).fetchone()
    normal_days = db.execute(
        """SELECT AVG(resolution_days) FROM reports
           WHERE resolution_days IS NOT NULL
           AND NOT (LOWER(description) LIKE '%danger%'
                    OR LOWER(description) LIKE '%hazard%'
                    OR LOWER(description) LIKE '%urgent%'
                    OR LOWER(description) LIKE '%immediate%'
                    OR LOWER(description) LIKE '%accident%'
                    OR LOWER(description) LIKE '%injur%')"""
    ).fetchone()

    lines.append("**Resolution speed by urgency language:**\n")
    if urgent_days[0] is not None:
        lines.append(f"- Reports with urgency keywords: avg {urgent_days[0]:.1f} days")
    if normal_days[0] is not None:
        lines.append(f"- Reports without urgency keywords: avg {normal_days[0]:.1f} days")
    lines.append("")

    lines.append("**Extractable severity indicators:**\n")
    lines.append("1. **Category-based severity** -- Potholes and road defects historically resolve faster (infrastructure priority)")
    lines.append("2. **Urgency keywords** -- 'dangerous', 'hazard', 'children', 'elderly', 'accident'")
    lines.append("3. **Photo presence** -- Reports with photos may get prioritized (evidence)")
    lines.append("4. **Location density** -- Multiple reports at same location signal systemic issue")
    lines.append("5. **Description quality** -- Longer, more detailed descriptions may correlate with faster action")
    lines.append("")

    # What makes a good report
    lines.append("### What Makes a 'Good' Report (correlates with faster resolution)\n")

    # Photo vs no photo resolution
    photo_res = db.execute(
        """SELECT AVG(resolution_days) FROM reports
           WHERE resolution_days IS NOT NULL
           AND photo_urls IS NOT NULL AND photo_urls != '[]' AND photo_urls != ''"""
    ).fetchone()[0]
    no_photo_res = db.execute(
        """SELECT AVG(resolution_days) FROM reports
           WHERE resolution_days IS NOT NULL
           AND (photo_urls IS NULL OR photo_urls = '[]' OR photo_urls = '')"""
    ).fetchone()[0]

    lines.append("**Photo impact on resolution:**\n")
    if photo_res is not None:
        lines.append(f"- With photos: avg {photo_res:.1f} days")
    if no_photo_res is not None:
        lines.append(f"- Without photos: avg {no_photo_res:.1f} days")
    lines.append("")

    # Description length vs resolution
    lines.append("**Description length vs resolution time:**\n")
    brackets = [
        ("Placeholder only (.)", "description = '.'"),
        ("Short (1-50 chars)", "LENGTH(description) BETWEEN 1 AND 50 AND description != '.'"),
        ("Medium (51-200 chars)", "LENGTH(description) BETWEEN 51 AND 200"),
        ("Long (200+ chars)", "LENGTH(description) > 200"),
    ]
    for label, where in brackets:
        res = db.execute(
            f"SELECT AVG(resolution_days), COUNT(*) FROM reports WHERE resolution_days IS NOT NULL AND {where}"
        ).fetchone()
        if res[0] is not None:
            lines.append(f"- {label}: avg {res[0]:.1f} days (n={res[1]})")
    lines.append("")

    lines.append("**Key attributes of well-resolved reports:**\n")
    lines.append("1. Clear, specific category selection")
    lines.append("2. Photo evidence attached")
    lines.append("3. Precise location (street address + postcode)")
    lines.append("4. Description with specific details (what, where, size/severity)")
    lines.append("5. Urgency context when applicable (safety risk, accessibility impact)")
    lines.append("")

    # Borough leaderboard
    lines.append("### Borough Leaderboard (Dashboard Data)\n")
    lines.append("| Rank | Borough | Reports | Median Resolution | Avg Resolution | Photo Rate |")
    lines.append("|-----:|---------|--------:|-----------------:|---------------:|----------:|")
    borough_data = db.execute(
        """SELECT borough, COUNT(*) as n,
                  SUM(CASE WHEN photo_urls IS NOT NULL AND photo_urls != '[]' AND photo_urls != '' THEN 1 ELSE 0 END) as photos,
                  SUM(CASE WHEN resolution_days IS NOT NULL THEN 1 ELSE 0 END) as with_res
           FROM reports GROUP BY borough ORDER BY borough"""
    ).fetchall()
    leaderboard = []
    for b in borough_data:
        brows = [
            r[0]
            for r in db.execute(
                "SELECT resolution_days FROM reports WHERE borough = ? AND resolution_days IS NOT NULL ORDER BY resolution_days",
                (b["borough"],),
            ).fetchall()
        ]
        bmed = stat_median(brows) if brows else 0
        bavg = sum(brows) / len(brows) if brows else 0
        photo_rate = b["photos"] / b["n"] * 100 if b["n"] else 0
        leaderboard.append((b["borough"], b["n"], bmed, bavg, photo_rate))

    leaderboard.sort(key=lambda x: x[2])
    for i, (borough, n, med, avg, pr) in enumerate(leaderboard, 1):
        lines.append(f"| {i} | {borough} | {n} | {med:.1f} days | {avg:.1f} days | {pr:.0f}% |")
    lines.append("")

    # Demo scenarios
    lines.append("### Recommended Demo Scenarios\n")
    lines.append(
        "Based on the data, these scenarios would make compelling demos "
        "because they represent real, common issues with good data quality:\n"
    )

    # Find well-described reports with photos and fast resolution
    good_demos = db.execute(
        """SELECT title, category, borough, resolution_days, description
           FROM reports
           WHERE resolution_days IS NOT NULL
           AND photo_urls IS NOT NULL AND photo_urls != '[]'
           AND description IS NOT NULL AND LENGTH(description) > 20 AND description != '.'
           ORDER BY resolution_days ASC
           LIMIT 5"""
    ).fetchall()
    lines.append("**Fast-resolution success stories (good for 'report -> fixed' demo flow):**\n")
    for r in good_demos:
        desc_preview = (r["description"] or "")[:80]
        lines.append(f"- **{r['title']}** ({r['category']}, {r['borough']}): resolved in {r['resolution_days']:.1f} days")
        lines.append(f"  > {desc_preview}...")
    lines.append("")

    # Most common categories for demo
    top_cats = db.execute(
        "SELECT category, COUNT(*) as n FROM reports WHERE category != '' GROUP BY category ORDER BY n DESC LIMIT 5"
    ).fetchall()
    lines.append("**Highest-volume categories (most relatable to users):**\n")
    for i, c in enumerate(top_cats, 1):
        lines.append(f"{i}. **{c['category']}** ({c['n']} reports) -- everyone encounters these")
    lines.append("")

    lines.append("**Recommended demo flow:**\n")
    lines.append("1. User reports a pothole or street lighting issue (most common)")
    lines.append("2. Show photo upload working with real examples from the dataset")
    lines.append("3. AI categorizes and routes to the correct borough council")
    lines.append("4. Display borough leaderboard with real resolution stats")
    lines.append("5. Show estimated resolution time based on historical data for that category/borough")
    lines.append("")

    return "\n".join(lines)


def build_executive_summary(db):
    """Section 1: Executive Summary"""
    lines = []
    lines.append("## 1. Executive Summary\n")

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    boroughs = db.execute("SELECT COUNT(DISTINCT borough) FROM reports").fetchone()[0]
    cats = db.execute(
        "SELECT COUNT(DISTINCT category) FROM reports WHERE category IS NOT NULL AND category != ''"
    ).fetchone()[0]

    # Top category
    top_cat = db.execute(
        "SELECT category, COUNT(*) as n FROM reports WHERE category != '' GROUP BY category ORDER BY n DESC LIMIT 1"
    ).fetchone()

    # Median resolution
    all_days = [
        r[0]
        for r in db.execute(
            "SELECT resolution_days FROM reports WHERE resolution_days IS NOT NULL ORDER BY resolution_days"
        ).fetchall()
    ]
    med = stat_median(all_days) if all_days else 0

    # Photo rate
    with_photos = db.execute(
        "SELECT COUNT(*) FROM reports WHERE photo_urls IS NOT NULL AND photo_urls != '[]' AND photo_urls != ''"
    ).fetchone()[0]

    # Fastest borough
    borough_medians = []
    for b in db.execute("SELECT DISTINCT borough FROM reports").fetchall():
        brows = [
            r[0]
            for r in db.execute(
                "SELECT resolution_days FROM reports WHERE borough = ? AND resolution_days IS NOT NULL ORDER BY resolution_days",
                (b["borough"],),
            ).fetchall()
        ]
        if brows:
            borough_medians.append((b["borough"], stat_median(brows)))
    borough_medians.sort(key=lambda x: x[1])
    fastest = borough_medians[0] if borough_medians else ("N/A", 0)
    slowest = borough_medians[-1] if borough_medians else ("N/A", 0)

    with_res = db.execute("SELECT COUNT(*) FROM reports WHERE resolution_days IS NOT NULL").fetchone()[0]

    borough_names = [b[0] for b in db.execute("SELECT DISTINCT borough FROM reports ORDER BY borough").fetchall()]
    borough_list = ", ".join(borough_names)
    lines.append(f"- **{total} fixed/resolved reports** scraped across **{boroughs} London boroughs** ({borough_list}) spanning **{cats} distinct issue categories**.")
    lines.append(f"- The most reported category is **{top_cat['category']}** ({top_cat['n']} reports, {top_cat['n']/total*100:.0f}% of total). The top 10 categories cover the vast majority of all reports.")
    lines.append(f"- Median resolution time is **{med:.0f} days** across {with_res} reports with resolution data. Resolution varies dramatically -- from under 1 hour to over 10 years, reflecting both quick fixes and long-lingering issues.")
    lines.append(f"- **{fastest[0]}** is the fastest-responding borough (median {fastest[1]:.0f} days), while **{slowest[0]}** is the slowest (median {slowest[1]:.0f} days).")
    lines.append(f"- **{with_photos/total*100:.0f}%** of reports include photos. Photo-attached reports and longer descriptions offer a foundation for training the AI intake classifier and severity estimator.")
    lines.append("")

    return "\n".join(lines)


def section_updates(db):
    """Bonus: Updates/comments analysis."""
    lines = []
    lines.append("## Appendix: Update/Comment Activity\n")

    total_updates = db.execute("SELECT COUNT(*) FROM updates").fetchone()[0]
    reports_with_updates = db.execute(
        "SELECT COUNT(DISTINCT report_id) FROM updates"
    ).fetchone()[0]
    total_reports = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]

    lines.append(f"- **Total update entries:** {total_updates}")
    lines.append(f"- **Reports with updates:** {reports_with_updates} of {total_reports} ({reports_with_updates/total_reports*100:.1f}%)")
    if total_updates and reports_with_updates:
        lines.append(f"- **Average updates per report (with updates):** {total_updates/reports_with_updates:.1f}")
    lines.append("")

    # Reports with most updates
    lines.append("### Reports with Most Updates\n")
    lines.append("| Report ID | Title | Updates | Borough |")
    lines.append("|-----------|-------|--------:|---------|")
    rows = db.execute(
        """SELECT u.report_id, r.title, COUNT(*) as n, r.borough
           FROM updates u JOIN reports r ON u.report_id = r.id
           GROUP BY u.report_id ORDER BY n DESC LIMIT 10"""
    ).fetchall()
    for r in rows:
        title = (r["title"] or "")[:50]
        lines.append(f"| {r['report_id']} | {title} | {r['n']} | {r['borough']} |")
    lines.append("")

    return "\n".join(lines)


def generate_report():
    db = connect()

    total = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    n_boroughs = db.execute("SELECT COUNT(DISTINCT borough) FROM reports").fetchone()[0]
    header = f"""# FixMyStreet Data Analysis
## London Civic Agent Project

*Analysis of {total} scraped reports across {n_boroughs} London boroughs*
*Generated from scraper/fixmystreet.db*

---

"""

    sections = [
        header,
        build_executive_summary(db),
        section_volume(db),
        section_resolution(db),
        section_geographic(db),
        section_content(db),
        section_product_insights(db),
        section_updates(db),
    ]

    report = "\n".join(sections)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report)
    print(f"Report written to {OUTPUT_PATH}")
    print(f"Report length: {len(report)} characters, {report.count(chr(10))} lines")

    db.close()


if __name__ == "__main__":
    generate_report()
