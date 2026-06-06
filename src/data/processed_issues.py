"""JSON-file-based store for agent-processed civic issues."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.models.base import CivicIssue

logger = logging.getLogger(__name__)

# Store lives at <project_root>/data/processed_issues.json
_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed_issues.json"


def _read_all() -> list[dict]:
    """Read the JSON array from disk (returns [] if file missing/corrupt)."""
    if not _STORE_PATH.exists():
        return []
    try:
        with open(_STORE_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read %s — returning empty list", _STORE_PATH)
        return []


def _write_all(items: list[dict]) -> None:
    """Overwrite the store with *items*."""
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STORE_PATH, "w") as f:
        json.dump(items, f, indent=2, default=str)


def save_issue(issue: CivicIssue) -> None:
    """Append a processed issue to the store (replaces if same id exists)."""
    items = _read_all()
    # Replace existing entry with same id, or append
    items = [it for it in items if it.get("id") != issue.id]
    items.append(issue.model_dump(mode="json"))
    _write_all(items)
    logger.info("Saved processed issue %s to store (%d total)", issue.id, len(items))


def get_all() -> list[dict]:
    """Return every stored issue as a list of dicts."""
    return _read_all()


def get_by_id(issue_id: str) -> Optional[dict]:
    """Return a single issue dict by id, or None."""
    for item in _read_all():
        if item.get("id") == issue_id:
            return item
    return None


def count() -> int:
    """Number of stored issues."""
    return len(_read_all())


def clear() -> None:
    """Remove all stored issues (useful for testing)."""
    _write_all([])
