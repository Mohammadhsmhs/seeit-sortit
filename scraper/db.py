import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fixmystreet.db"

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    title TEXT,
    category TEXT,
    description TEXT,
    latitude REAL,
    longitude REAL,
    address TEXT,
    borough TEXT,
    council TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT,
    photo_urls TEXT,
    photo_paths TEXT,
    resolved_at TEXT,
    resolution_days REAL,
    source TEXT DEFAULT 'fixmystreet',
    source_url TEXT,
    report_count INTEGER DEFAULT 1,
    scraped_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    text TEXT,
    timestamp TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id)
);
"""

INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_reports_borough ON reports(borough);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_coords ON reports(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_reports_source ON reports(source);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
"""


def _migrate(db):
    """Add new columns to an existing DB if they don't already exist."""
    cols = {row["name"] for row in db.execute("PRAGMA table_info(reports)").fetchall()}
    if "source" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN source TEXT DEFAULT 'fixmystreet'")
        db.execute("UPDATE reports SET source = 'fixmystreet' WHERE source IS NULL")
    if "source_url" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN source_url TEXT")
        db.execute(
            "UPDATE reports SET source_url = 'https://www.fixmystreet.com/report/' || id "
            "WHERE source_url IS NULL"
        )
    if "report_count" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN report_count INTEGER DEFAULT 1")
    if "photo_paths" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN photo_paths TEXT")
    db.commit()


def get_db(path=None):
    db = sqlite3.connect(path or DB_PATH)
    db.row_factory = sqlite3.Row
    # Create tables first, then migrate (add columns), THEN create indexes
    # so that indexes referring to new columns don't fail on legacy DBs.
    db.executescript(TABLE_SCHEMA)
    _migrate(db)
    db.executescript(INDEX_SCHEMA)
    return db


def upsert_report(db, report):
    report = dict(report)
    report.setdefault("source", "fixmystreet")
    report.setdefault("source_url", f"https://www.fixmystreet.com/report/{report['id']}")
    report.setdefault("report_count", 1)
    db.execute(
        """INSERT INTO reports (id, title, category, description, latitude, longitude,
           address, borough, council, status, created_at, updated_at, photo_urls,
           resolved_at, resolution_days, source, source_url, report_count)
           VALUES (:id, :title, :category, :description, :latitude, :longitude,
           :address, :borough, :council, :status, :created_at, :updated_at, :photo_urls,
           :resolved_at, :resolution_days, :source, :source_url, :report_count)
           ON CONFLICT(id) DO UPDATE SET
             title=excluded.title, category=excluded.category,
             description=excluded.description, status=excluded.status,
             updated_at=excluded.updated_at, photo_urls=excluded.photo_urls,
             resolved_at=excluded.resolved_at, resolution_days=excluded.resolution_days,
             source=excluded.source, source_url=excluded.source_url,
             scraped_at=datetime('now')""",
        report,
    )


def insert_updates(db, report_id, updates):
    db.execute("DELETE FROM updates WHERE report_id = ?", (report_id,))
    for u in updates:
        db.execute(
            "INSERT INTO updates (report_id, text, timestamp) VALUES (?, ?, ?)",
            (report_id, u["text"], u["timestamp"]),
        )
