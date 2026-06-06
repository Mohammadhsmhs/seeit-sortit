# RAG Data Shopping List

> Concrete inventory of every file the RAG corpus loader downloads. **Bookmark these URLs Friday evening** — Saturday morning is not the time to discover one has moved.
>
> Companion to `prompts/build-prompt-rag-corpus.md` (the build prompt). This doc is what the script downloads.
>
> Total disk after extraction: **~400 MB**. Total wall time: **10-15 min** on hackathon WiFi.

---

## 1. STATS19 — collision history

**What we cite:** *"7 STATS19 serious injuries within 500m, including 1 cyclist."*

| | |
|---|---|
| **Source** | TfL via London Datastore |
| **Canonical URL** | https://data.london.gov.uk/dataset/road-casualties-severe-injuries-borough |
| **File format** | CSV |
| **Size** | ~50 MB raw (filter to last 5 years → ~12 MB) |
| **Rows** | ~25,000 across London (filtered) |
| **Coordinate system** | British National Grid (Easting/Northing) — requires pyproj BNG→WGS84 transform |
| **Columns we keep** | Accident_Index, Date, Police_Force, Severity, Location_Easting_OSGR, Location_Northing_OSGR, Number_of_Vehicles, Number_of_Casualties, casualty_class |
| **Backup if URL broken** | https://www.data.gov.uk/dataset/road-accidents-safety-data |
| **Cache to** | `data/raw/stats19.csv` |
| **Target table** | `rag_collisions` |

### Saturday morning sanity check
```bash
curl -sI "<URL>" | head -3
# expect: 200 OK + content-length > 30MB
```

---

## 2. GIAS schools — schools & nurseries

**What we cite:** *"Osmani Primary School is 44m from this location."*

| | |
|---|---|
| **Source** | UK Department for Education — "Get Information about Schools" |
| **Canonical URL** | https://get-information-schools.service.gov.uk/Downloads |
| **Specific file** | `Establishment fields with links to current 'open' establishments` (CSV) |
| **Size** | ~25 MB raw → ~3 MB after London filter |
| **Rows** | ~2,400 London-postcode schools |
| **Coordinate system** | Easting/Northing — needs the same pyproj transform |
| **Columns we keep** | URN, EstablishmentName, EstablishmentStatus(=Open), Postcode, PhaseOfEducation, Easting, Northing |
| **Filter** | Postcode starts with any of: E, EC, N, NW, SE, SW, W, WC (London postcode prefixes) |
| **Backup if URL broken** | https://www.data.gov.uk/dataset/get-information-about-schools-csv |
| **Cache to** | `data/raw/gias_schools.csv` |
| **Target table** | `rag_schools` |

### Critical sanity check
```bash
# Must find Osmani Primary or the demo's flagship citation breaks
grep -i osmani data/raw/gias_schools.csv
# expect: a row containing "Osmani Primary School" with Tower Hamlets postcode
```

---

## 3. NHS organisation data — hospitals

**What we cite:** *"BARNSLEY STREET NEIGHBOURHOOD MENTAL HEALTH CENTRE is 160m away."*

| | |
|---|---|
| **Source** | NHS Digital Organisation Data Service |
| **Canonical URL** | https://digital.nhs.uk/services/organisation-data-service/file-downloads/data-files |
| **Specific files** | `epraccur.zip` (GP practices, ~5,000 rows London-filtered) + `etr.zip` (NHS trusts) + `ets.zip` (sites) |
| **Size** | ~5 MB combined |
| **Format** | CSV (no header — schema is documented separately on the same page) |
| **Coordinate system** | Postcode → lookup against ONSPD (postcode → lat/lon) |
| **Filter** | Postcode starts with London prefixes (same as GIAS) |
| **Backup** | https://www.data.gov.uk/dataset/nhs-postcode-directory |
| **Cache to** | `data/raw/nhs_*.csv` |
| **Target table** | `rag_hospitals` |

**Cuttable**: per `saturday-cut-list.md` item #1, hospitals are the first thing cut if we run out of time. Schools + collisions citations alone carry the demo.

### Saturday morning sanity check
```bash
unzip -l data/raw/epraccur.zip
# expect: contains "epraccur.csv"
```

---

## 4. ONS Census 2021 — LSOA population density

**What we cite:** *"Population density of 17,095 people / sq km."*

| | |
|---|---|
| **Source** | ONS — London Datastore mirror |
| **Canonical URL** | https://data.london.gov.uk/dataset/lsoa-atlas |
| **Specific file** | LSOA Atlas 2021 (xlsx — ~50 MB) OR direct NOMIS query |
| **Size** | ~50 MB xlsx → ~2 MB CSV |
| **Rows** | ~4,800 London LSOAs |
| **Coordinate system** | LSOA codes (E01xxxxx) — we use the centroid lat/lon, looked up from the ONS Output Area lookup |
| **Columns we keep** | LSOA21CD, LSOA21NM, Population, Area_km2, Density_ppl_per_km2 |
| **Backup** | NOMIS bulk: https://www.nomisweb.co.uk/sources/census_2021_bulk |
| **Cache to** | `data/raw/lsoa_density.csv` |
| **Target table** | `rag_lsoa` |

### Sanity check
```bash
# Tower Hamlets is the densest — should show a density >15000 per km2 for an LSOA in there
sqlite3 scraper/fixmystreet.db "SELECT name, density FROM rag_lsoa
  WHERE name LIKE '%Tower Hamlets%' ORDER BY density DESC LIMIT 3;"
```

---

## 5. Borough boundaries (for the routing agent — not severity)

**Used by:** routing agent (point-in-polygon)

| | |
|---|---|
| **Source** | data.london.gov.uk / OS Open data |
| **URL** | https://skgrange.github.io/www/data/london_boroughs.json |
| **Format** | GeoJSON |
| **Size** | ~5 MB |
| **Cache to** | `data/london_boroughs.geojson` |

Pre-download this Friday evening — it's small and not strictly RAG but the routing agent crashes without it.

---

## Order to download Saturday morning (in `build_rag_corpus.py`)

Smallest first so we get fast wins:

1. **Borough boundaries** (~5 MB, 5 sec)
2. **LSOA density** (~50 MB xlsx, 60 sec)
3. **GIAS schools** (~25 MB, 30 sec)
4. **NHS** (~5 MB combined, 20 sec)
5. **STATS19** (~50 MB, 60 sec — biggest, leave for last)

Total: ~3-5 minutes of downloads if WiFi is decent.

---

## What we DON'T download

Don't get tempted Saturday afternoon:

- ❌ **DfT traffic volume (AADF)** — interesting but irrelevant for our 4-citation severity rubric
- ❌ **High Streets footfall** — restricted to partnership members
- ❌ **Care homes (CQC)** — adds 3rd reference category, doesn't move the demo
- ❌ **OpenStreetMap full extract** — gigabytes, total time-sink

If we have spare time at 18:00 Saturday, **don't add data**. Polish what's there.

---

## Disk + bandwidth budget

| Stage | Disk | Bandwidth |
|-------|------|-----------|
| Raw downloads | ~250 MB | One-time |
| Parsed CSVs | ~30 MB | n/a |
| SQLite tables | ~50 MB added to `fixmystreet.db` | n/a |
| **Total disk** | **~330 MB extra** | **~250 MB download** |

If the venue WiFi can't sustain ~250 MB downloads — switch to phone hotspot for this hour. ~5 minutes on a 4G connection.

---

## Pre-fetch tonight (Friday)

Tonight, while waiting for pizza, run these in a shell on your laptop:

```bash
mkdir -p data/raw
cd data/raw
curl -sLO "https://skgrange.github.io/www/data/london_boroughs.json"
# Browse to https://get-information-schools.service.gov.uk/Downloads
# and click through to GIAS download — saves a few clicks Saturday
```

Boroughs GeoJSON is small enough we can hit it now. The other 4 datasets are best left until Saturday morning so we run the actual loader fresh.
