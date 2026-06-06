"""Build the RAG chunk index from all raw datasets.

Usage:
    .venv/bin/python -m src.rag.build_index
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from src.config import RAW_DATA_DIR, PROJECT_ROOT
from src.rag.corpus import CorpusManager

INDEX_PATH = PROJECT_ROOT / "data" / "rag_index.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    print()
    print("=" * 60)
    print("  RAG INDEX BUILDER -- London Civic Agent")
    print("=" * 60)
    print()
    print(f"  Data directory: {RAW_DATA_DIR}")
    print(f"  Index output:   {INDEX_PATH}")
    print()

    if not RAW_DATA_DIR.is_dir():
        print(f"ERROR: Data directory not found: {RAW_DATA_DIR}")
        return 1

    corpus = CorpusManager()

    t0 = time.monotonic()
    total = corpus.build_index()
    elapsed = time.monotonic() - t0

    stats = corpus.get_stats()

    print("-" * 60)
    print(f"  Total chunks:     {total:>8,}")
    print()
    print("  Chunks by dataset:")
    for ds, count in sorted(stats["chunks_by_dataset"].items()):
        print(f"    {ds:<20s} {count:>8,}")
    print()
    print(f"  Geo-located chunks: {stats['geo_chunks']:>6,}")

    bbox = stats.get("bounding_box")
    if bbox:
        print(f"  Bounding box:       lat [{bbox['lat_min']:.4f}, {bbox['lat_max']:.4f}]")
        print(f"                      lon [{bbox['lon_min']:.4f}, {bbox['lon_max']:.4f}]")

    print()
    print(f"  Build time:         {elapsed:.1f}s")
    print("-" * 60)

    # Save to disk
    print()
    print(f"  Saving index to {INDEX_PATH} ...")
    corpus.save(INDEX_PATH)
    size_mb = INDEX_PATH.stat().st_size / (1024 * 1024)
    print(f"  Saved ({size_mb:.1f} MB)")

    print()
    print("  Done. Load with: CorpusManager().load('data/rag_index.json')")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
