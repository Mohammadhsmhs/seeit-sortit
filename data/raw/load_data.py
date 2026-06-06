#!/usr/bin/env python3
"""
Load and verify all downloaded London Civic Agent RAG corpus datasets.
Prints summary statistics for each dataset to confirm data is usable.

Usage:
    python data/raw/load_data.py
"""

import csv
import json
import os
import sys
from pathlib import Path

# Resolve paths relative to this script
BASE_DIR = Path(__file__).parent
MANIFEST = BASE_DIR / "manifest.json"

# London postcode area prefixes (for filtering NHS data)
LONDON_POSTCODE_AREAS = {
    "E", "EC", "N", "NW", "SE", "SW", "W", "WC",
    "BR", "CR", "DA", "EN", "HA", "IG", "KT", "RM",
    "SM", "TN", "TW", "UB", "WD",
}


def is_london_postcode(postcode: str) -> bool:
    """Check if a postcode is in a London area."""
    if not postcode:
        return False
    pc = postcode.strip().upper().split()[0] if postcode.strip() else ""
    # Extract area prefix (letters before first digit)
    area = ""
    for ch in pc:
        if ch.isalpha():
            area += ch
        else:
            break
    return area in LONDON_POSTCODE_AREAS


def print_separator():
    print("=" * 72)


def load_stats19_collisions():
    """Load STATS19 collision data and filter to London."""
    filepath = BASE_DIR / "stats19" / "collisions_2024.csv"
    print_separator()
    print("STATS19 ROAD COLLISIONS 2024")
    print(f"  File: {filepath}")

    total = 0
    london_count = 0
    severities = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols[:10])}...")

        for row in reader:
            total += 1
            # Metropolitan Police = 1, City of London = 97
            pf = row.get("police_force", "")
            if pf in ("1", "97"):
                london_count += 1
                sev = row.get("collision_severity", "?")
                severities[sev] = severities.get(sev, 0) + 1

    print(f"  Total rows: {total:,}")
    print(f"  London collisions (Met Police + City): {london_count:,}")
    print(f"  London severity breakdown: {dict(sorted(severities.items()))}")
    return london_count


def load_stats19_casualties():
    """Load STATS19 casualty data."""
    filepath = BASE_DIR / "stats19" / "casualties_2024.csv"
    print_separator()
    print("STATS19 ROAD CASUALTIES 2024")
    print(f"  File: {filepath}")

    total = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols[:10])}...")
        for row in reader:
            total += 1

    print(f"  Total rows: {total:,}")
    print("  (Link to collisions via collision_index for London filtering)")
    return total


def load_schools():
    """Load London schools data from GIAS."""
    filepath = BASE_DIR / "schools" / "london_schools.csv"
    print_separator()
    print("SCHOOLS (GIAS) - LONDON")
    print(f"  File: {filepath}")

    total = 0
    open_schools = 0
    phases = {}
    types = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols[:8])}...")

        for row in reader:
            total += 1
            status = row.get("EstablishmentStatus (name)", "")
            if status == "Open":
                open_schools += 1
            phase = row.get("PhaseOfEducation (name)", "Unknown")
            phases[phase] = phases.get(phase, 0) + 1
            etype = row.get("TypeOfEstablishment (name)", "Unknown")
            types[etype] = types.get(etype, 0) + 1

    print(f"  Total rows: {total:,}")
    print(f"  Open schools: {open_schools:,}")
    print(f"  By phase: { {k: v for k, v in sorted(phases.items(), key=lambda x: -x[1])[:8]} }")
    print(f"  By type (top 5): { {k: v for k, v in sorted(types.items(), key=lambda x: -x[1])[:5]} }")
    return total


def load_hospitals():
    """Load NHS trust sites and filter to London."""
    filepath = BASE_DIR / "hospitals" / "nhs_trusts_sites.csv"
    print_separator()
    print("NHS TRUST SITES (HOSPITALS)")
    print(f"  File: {filepath}")

    total = 0
    london_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            total += 1
            if len(row) > 9:
                postcode = row[9]
                if is_london_postcode(postcode):
                    london_count += 1

    print(f"  Total rows: {total:,}")
    print(f"  London sites (by postcode): {london_count:,}")
    print("  Note: No header row. Key columns: [0]=ODS code, [1]=name, [4]=address, [9]=postcode")
    return london_count


def load_care_homes():
    """Load CQC care directory and filter to London."""
    filepath = BASE_DIR / "care_homes" / "cqc_directory.csv"
    print_separator()
    print("CQC CARE DIRECTORY")
    print(f"  File: {filepath}")

    total = 0
    london_count = 0
    service_types = {}

    with open(filepath, "r", encoding="utf-8") as f:
        # Skip first 4 metadata rows
        for _ in range(4):
            next(f)
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols[:8])}...")

        for row in reader:
            total += 1
            region = row.get("Region", "")
            if region == "London":
                london_count += 1
                stype = row.get("Service types", "Unknown")
                service_types[stype] = service_types.get(stype, 0) + 1

    print(f"  Total rows: {total:,}")
    print(f"  London providers: {london_count:,}")
    top_types = sorted(service_types.items(), key=lambda x: -x[1])[:5]
    print(f"  London service types (top 5): { {k: v for k, v in top_types} }")
    return london_count


def load_traffic():
    """Load DfT AADF traffic count data for London."""
    filepath = BASE_DIR / "traffic" / "london_aadf_2025.csv"
    print_separator()
    print("DfT AADF TRAFFIC COUNTS - LONDON 2025")
    print(f"  File: {filepath}")

    if not filepath.exists():
        print("  MISSING")
        return 0

    total = 0
    boroughs = {}
    max_aadf = 0
    max_road = ""
    sum_aadf = 0
    busy = 0  # > 10,000 AADF
    very_busy = 0  # > 20,000 AADF

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols[:8])}...")

        for row in reader:
            total += 1
            borough = row.get("local_authority_name", "Unknown")
            boroughs[borough] = boroughs.get(borough, 0) + 1
            try:
                aadf = int(row.get("all_motor_vehicles", "0"))
            except ValueError:
                aadf = 0
            sum_aadf += aadf
            if aadf > 10000:
                busy += 1
            if aadf > 20000:
                very_busy += 1
            if aadf > max_aadf:
                max_aadf = aadf
                max_road = f"{row.get('road_name', '?')} ({borough})"

    avg_aadf = sum_aadf / total if total else 0
    print(f"  Total count points: {total:,}")
    print(f"  London boroughs covered: {len(boroughs)}")
    print(f"  Average AADF: {avg_aadf:,.0f} vehicles/day")
    print(f"  Busy roads (>10k AADF): {busy:,}")
    print(f"  Very busy roads (>20k AADF): {very_busy:,}")
    print(f"  Busiest count point: {max_road} ({max_aadf:,} vehicles/day)")
    return total


def load_census():
    """Load Census 2021 LSOA population density for London."""
    filepath = BASE_DIR / "census" / "london_lsoa_population_density.csv"
    print_separator()
    print("CENSUS 2021 LSOA POPULATION DENSITY - LONDON")
    print(f"  File: {filepath}")

    total = 0
    boroughs = {}
    total_pop = 0
    max_density = 0
    max_density_lsoa = ""

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        print(f"  Columns ({len(cols)}): {', '.join(cols)}")

        for row in reader:
            total += 1
            borough = row.get("LAD 2023 Name", "Unknown")
            boroughs[borough] = boroughs.get(borough, 0) + 1
            try:
                pop = float(row.get("Mid-2024: Population", 0))
                density = float(row.get("Mid-2024: People per Sq Km", 0))
                total_pop += pop
                if density > max_density:
                    max_density = density
                    max_density_lsoa = row.get("LSOA 2021 Name", "?")
            except (ValueError, TypeError):
                pass

    print(f"  Total London LSOAs: {total:,}")
    print(f"  London boroughs covered: {len(boroughs)}")
    print(f"  Total London population (mid-2024): {total_pop:,.0f}")
    print(f"  Densest LSOA: {max_density_lsoa} ({max_density:,.0f} people/sq km)")
    print(f"  Boroughs: {', '.join(sorted(boroughs.keys()))}")
    return total


def main():
    print("\n" + "=" * 72)
    print("  LONDON CIVIC AGENT RAG CORPUS - DATA VERIFICATION")
    print("=" * 72 + "\n")

    # Load manifest
    if MANIFEST.exists():
        with open(MANIFEST) as f:
            manifest = json.load(f)
        print(f"Manifest: {len(manifest['datasets'])} primary datasets, "
              f"{len(manifest.get('supplementary_files', []))} supplementary files")
        print(f"Download date: {manifest['download_date']}\n")

    # Load each dataset
    results = {}
    results["stats19_collisions_london"] = load_stats19_collisions()
    results["stats19_casualties_total"] = load_stats19_casualties()
    results["schools_london"] = load_schools()
    results["hospitals_london"] = load_hospitals()
    results["care_homes_london"] = load_care_homes()
    results["census_lsoas_london"] = load_census()
    results["traffic_count_points_london"] = load_traffic()

    # Summary
    print_separator()
    print("\nSUMMARY OF LONDON-RELEVANT DATA:")
    print(f"  Road collisions (London 2024):   {results['stats19_collisions_london']:>8,}")
    print(f"  Road casualties (all GB 2024):   {results['stats19_casualties_total']:>8,}")
    print(f"  Schools (London):                {results['schools_london']:>8,}")
    print(f"  NHS sites (London):              {results['hospitals_london']:>8,}")
    print(f"  CQC providers (London):          {results['care_homes_london']:>8,}")
    print(f"  Census LSOAs (London):           {results['census_lsoas_london']:>8,}")
    print(f"  Traffic count points (London):   {results['traffic_count_points_london']:>8,}")
    print()

    # Check for issues
    issues = []
    if results["stats19_collisions_london"] == 0:
        issues.append("No London collisions found - check police_force filter")
    if results["schools_london"] < 1000:
        issues.append("Fewer than 1000 London schools - check GOR filter")
    if results["hospitals_london"] == 0:
        issues.append("No London hospitals found - check postcode filter")
    if results["care_homes_london"] == 0:
        issues.append("No London care homes found - check Region filter")
    if results["census_lsoas_london"] < 4000:
        issues.append("Fewer than 4000 London LSOAs - check LAD filter")
    if results["traffic_count_points_london"] < 1500:
        issues.append("Fewer than 1500 London traffic count points - check region filter")

    if issues:
        print("ISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("All datasets verified successfully. Data is ready for RAG corpus.")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
