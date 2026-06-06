# Data Sources

The London Civic Agent uses six open public datasets to score, contextualise,
and route civic issue reports. All data is downloaded from official UK / London
sources and stored under `data/raw/`. Each dataset is geolocated to London
either at source (region filter) or via postcode-sector geocoding built from
the GIAS schools register.

Provenance metadata for every file is tracked in `data/raw/manifest.json`.

---

## 1. STATS19 Road Collisions (2024)

- **File:** `data/raw/stats19/collisions_2024.csv`, `data/raw/stats19/casualties_2024.csv`
- **Source:** UK Department for Transport — Road Safety Open Data
- **URL:** https://www.gov.uk/government/statistical-data-sets/road-safety-open-data
- **License:** Open Government Licence v3.0
- **Used for:** Collision hotspot detection (severity +1 if 3+ collisions within
  500m over the last 3 years).
- **London filter:** `police_force == 1` (Metropolitan Police) or `97` (City of London).

## 2. Get Information About Schools (GIAS)

- **File:** `data/raw/schools/london_schools.csv`
- **Source:** UK Department for Education
- **URL:** https://get-information-schools.service.gov.uk/Downloads
- **License:** Open Government Licence v3.0
- **Used for:** Schools-within-200m proximity boost (+2); also builds the
  postcode-sector geocoder used to place hospitals and care homes.
- **London filter:** GOR (Region) name contains `London`.

## 3. NHS Trust Sites (Hospitals)

- **File:** `data/raw/hospitals/nhs_trusts_sites.csv`
- **Source:** NHS Digital — Organisation Data Service
- **URL:** https://digital.nhs.uk/services/organisation-data-service/data-search-and-export/csv-downloads/other-nhs-organisations
- **License:** Open Government Licence v3.0
- **Used for:** Hospitals-within-300m proximity boost (+2).
- **London filter:** Postcode prefix matches London areas (E, EC, N, NW, SE,
  SW, W, WC).

## 4. CQC Care Directory

- **File:** `data/raw/care_homes/cqc_directory.csv`
- **Source:** Care Quality Commission
- **URL:** https://www.cqc.org.uk/about-us/transparency/using-cqc-data
- **License:** Open Government Licence v3.0
- **Used for:** Care-homes-within-200m proximity boost (+1).
- **London filter:** `Region == "London"`.

## 5. Census 2021 LSOA Population Density

- **File:** `data/raw/census/london_lsoa_population_density.csv`
- **Source:** Office for National Statistics
- **URL:** https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareapopulationdensity
- **License:** Open Government Licence v3.0
- **Used for:** High-density area boost (+1 if local LSOA exceeds 15,000
  people/sq km).
- **London filter:** LAD codes starting with `E09` (the 33 London boroughs).

## 6. DfT AADF Road Traffic Statistics — London 2025

- **File:** `data/raw/traffic/london_aadf_2025.csv`
- **Source:** UK Department for Transport — Road Traffic Statistics
- **Source page:** https://roadtraffic.dft.gov.uk/downloads
- **Direct URL:** `https://storage.googleapis.com/dft-statistics/road-traffic/downloads/aadf/region_id/dft_aadf_region_id_6.csv`
- **License:** Open Government Licence v3.0
- **Used for:** Traffic-flow context boost — busy road (>10,000 AADF) +1,
  very busy (>20,000 AADF) +1 more. Looked up at the nearest count point
  within 400m of the issue. Added to the severity justification as e.g.
  "On a busy road carrying ~18,400 vehicles/day (A205, DfT AADF)".
- **London filter:** `region_id == 6` (already filtered at source).
- **Coverage:** 2,050 count points across all 33 London boroughs, 2025.
- See `data/raw/traffic/README.md` for the full column documentation.

---

## Attribution

These datasets are made available under the Open Government Licence v3.0.
When using outputs from this project that derive from them, attribution should
include: "Contains public sector information licensed under the Open Government
Licence v3.0" and the underlying source (DfT, ONS, NHS Digital, CQC, DfE).
