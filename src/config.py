"""Central configuration — reads from environment variables with sensible defaults."""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DATA_DIR = Path(__file__).resolve().parent / "data"    # src/data/ — JSON config files
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"               # data/raw/ — RAG corpus datasets
SCRAPER_DIR = PROJECT_ROOT / "scraper"
SCRAPER_DB = SCRAPER_DIR / "fixmystreet.db"
BOROUGHS_JSON = SRC_DATA_DIR / "boroughs.json"
CATEGORIES_JSON = SRC_DATA_DIR / "categories.json"
SEVERITY_FACTORS_JSON = SRC_DATA_DIR / "severity_factors.json"
CATEGORY_MAPPING_JSON = SRC_DATA_DIR / "category_mapping.json"

# Keep DATA_DIR as alias for backwards compatibility (points to src/data/)
DATA_DIR = SRC_DATA_DIR

# ---------------------------------------------------------------------------
# Model provider: "mock" | "openai" | "nim"
# ---------------------------------------------------------------------------
MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "mock")

# OpenAI-compatible endpoint (vLLM / TensorRT-LLM / local)
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "meta/llama-3.1-8b-instruct")

# NVIDIA NIM
NIM_BASE_URL: str = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY: str = os.getenv("NIM_API_KEY", "")
NIM_MODEL: str = os.getenv("NIM_MODEL", "meta/llama-3.1-8b-instruct")
NIM_EMBED_MODEL: str = os.getenv("NIM_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5")

# ---------------------------------------------------------------------------
# Integration stubs
# ---------------------------------------------------------------------------
FIXMYSTREET_API_URL: str = os.getenv(
    "FIXMYSTREET_API_URL", "https://www.fixmystreet.com/import"
)
FIXMYSTREET_API_KEY: str = os.getenv("FIXMYSTREET_API_KEY", "")

ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
ELEVENLABS_AGENT_ID: str = os.getenv("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_PHONE_NUMBER_ID: str = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")

TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")

TFL_BASE_URL: str = "https://api.tfl.gov.uk"
TFL_APP_KEY: str = os.getenv("TFL_APP_KEY", "")  # optional, raises rate limit

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_SEVERITY = 5
MAX_SEVERITY = 10
EMBED_DIM = 384  # dimension for mock embeddings
