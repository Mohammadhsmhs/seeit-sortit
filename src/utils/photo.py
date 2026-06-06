"""Photo handling utilities — extract GPS, metadata, and generate LLM prompts.

All functions degrade gracefully when Pillow is not installed, returning None
and logging a message.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS

    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
    logger.info("Pillow not installed — photo utilities will return None")


# ---------------------------------------------------------------------------
# GPS extraction
# ---------------------------------------------------------------------------

def _dms_to_decimal(dms_tuple: tuple, ref: str) -> float:
    """Convert EXIF DMS (degrees, minutes, seconds) to decimal degrees."""
    degrees, minutes, seconds = dms_tuple
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def extract_gps(filepath: str | Path) -> Optional[dict[str, float]]:
    """Extract GPS coordinates from EXIF data.

    Returns {"latitude": float, "longitude": float} or None if unavailable.
    Supports JPEG and common image formats via Pillow.
    """
    if not _PILLOW_AVAILABLE:
        logger.warning("extract_gps: Pillow not installed, returning None")
        return None

    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning("extract_gps: file not found: %s", filepath)
        return None

    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if not exif_data:
            return None

        gps_info = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "GPSInfo":
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag_name] = gps_value
                break

        if not gps_info:
            return None

        lat_dms = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon_dms = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if not (lat_dms and lat_ref and lon_dms and lon_ref):
            return None

        return {
            "latitude": _dms_to_decimal(lat_dms, lat_ref),
            "longitude": _dms_to_decimal(lon_dms, lon_ref),
        }
    except Exception:
        logger.warning("extract_gps: failed to read EXIF from %s", filepath, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_metadata(filepath: str | Path) -> Optional[dict[str, str]]:
    """Extract timestamp, camera model, and orientation from EXIF data.

    Returns a dict with keys: timestamp, camera_model, orientation.
    Missing fields are set to empty strings.  Returns None if Pillow
    is unavailable or the file has no EXIF data.
    """
    if not _PILLOW_AVAILABLE:
        logger.warning("extract_metadata: Pillow not installed, returning None")
        return None

    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning("extract_metadata: file not found: %s", filepath)
        return None

    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if not exif_data:
            return None

        decoded: dict[str, str] = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            decoded[tag_name] = value

        orientation_val = decoded.get("Orientation", "")
        orientation_map = {
            1: "Normal",
            3: "Rotated 180",
            6: "Rotated 90 CW",
            8: "Rotated 90 CCW",
        }

        return {
            "timestamp": str(decoded.get("DateTimeOriginal", decoded.get("DateTime", ""))),
            "camera_model": str(decoded.get("Model", "")),
            "orientation": orientation_map.get(orientation_val, str(orientation_val)),
        }
    except Exception:
        logger.warning("extract_metadata: failed to read EXIF from %s", filepath, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Vision LLM prompt generation
# ---------------------------------------------------------------------------

def describe_for_llm(filepath: str | Path) -> str:
    """Generate a text prompt for a vision LLM to describe a civic issue photo.

    This returns the prompt text that would be sent alongside the image to
    Qwen2.5-VL-7B or a similar vision model.  The prompt does NOT include
    the image itself — the caller is responsible for attaching the image
    to the multimodal request.
    """
    filepath = Path(filepath)

    # Try to include GPS context if available
    gps_context = ""
    gps = extract_gps(filepath)
    if gps:
        gps_context = (
            f" The photo was taken at GPS coordinates "
            f"({gps['latitude']:.5f}, {gps['longitude']:.5f})."
        )

    return (
        "You are an expert at identifying civic and infrastructure issues "
        "in urban environments. Analyze this photo and describe:\n"
        "1. What type of civic issue is shown (e.g. pothole, fly-tipping, "
        "broken streetlight, graffiti, damaged pavement, etc.)\n"
        "2. The severity of the issue (minor, moderate, serious, dangerous)\n"
        "3. Any safety hazards visible\n"
        "4. The approximate size or extent of the problem\n"
        "5. Any identifiable location features (street signs, buildings, landmarks)\n"
        "\n"
        "Be specific and factual. Focus on what is visible in the image."
        f"{gps_context}\n"
        "\n"
        "Respond in 2-3 concise sentences suitable for a civic issue report."
    )
