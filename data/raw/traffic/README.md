# DfT AADF Traffic Flow Data — London

## Source

- **Dataset**: Annual Average Daily Flow (AADF) — Count Point level, all directions
- **Provider**: UK Department for Transport (DfT)
- **Source page**: https://roadtraffic.dft.gov.uk/downloads
- **Direct CSV URL**: https://storage.googleapis.com/dft-statistics/road-traffic/downloads/aadf/region_id/dft_aadf_region_id_6.csv
  (`region_id=6` is the London region)
- **Downloaded**: 2026-06-02
- **License**: Open Government Licence v3.0 (https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

## Files

- `london_aadf_2025.csv` — London traffic count points for **2025** (the most recent year available).
  Filtered from the full London time-series (2000–2025, 56,321 rows) down to 2,050 rows for 2025.

## Columns

| Column | Description |
|---|---|
| `count_point_id` | Stable DfT identifier for the count point |
| `year` | Survey year (2025 throughout this file) |
| `region_id`, `region_name` | DfT region (`6` / `London`) |
| `local_authority_id`, `local_authority_name` | London borough (33 boroughs covered) |
| `road_name` | Road identifier (e.g. `M1`, `A205`, `A406`, `C` for minor classified) |
| `road_type` | `Major` or `Minor` |
| `start_junction_road_name`, `end_junction_road_name` | Bounding junctions for the link |
| `easting`, `northing` | British National Grid coordinates |
| `latitude`, `longitude` | WGS84 (already converted in source) |
| `link_length_km`, `link_length_miles` | Length of the road link |
| `estimation_method`, `estimation_method_detailed` | `Counted` (manual) or `Estimated` |
| `pedal_cycles` | AADF pedal cycles |
| `two_wheeled_motor_vehicles` | AADF motorcycles |
| `cars_and_taxis` | AADF cars + taxis |
| `buses_and_coaches` | AADF buses + coaches |
| `lgvs` | AADF light goods vehicles |
| `hgvs_2_rigid_axle`, `hgvs_3_rigid_axle`, `hgvs_4_or_more_rigid_axle`, `hgvs_3_or_4_articulated_axle`, `hgvs_5_articulated_axle`, `hgvs_6_articulated_axle` | AADF HGVs by axle config |
| `all_hgvs` | Sum of all HGV categories |
| `all_motor_vehicles` | **Total AADF — the headline number used for severity scoring** |

## Filter notes

- `region_name == "London"` already filtered at source (region_id=6).
- Covers all 33 London authorities: City of London, Westminster, Camden, Islington,
  Hackney, Tower Hamlets, Greenwich, Lewisham, Southwark, Lambeth, Wandsworth,
  Hammersmith & Fulham, Kensington & Chelsea, Newham, Waltham Forest, Redbridge,
  Havering, Bexley, Bromley, Croydon, Sutton, Merton, Kingston upon Thames,
  Richmond upon Thames, Hounslow, Hillingdon, Ealing, Brent, Harrow, Barnet,
  Enfield, Haringey, Barking and Dagenham.
- Mix of Major (motorway / A-road) and Minor (B-road / classified) count points.

## Provenance / regenerate

```bash
# Download full London time-series (2000-2025) — ~12 MB
curl -sL -o london_aadf_all_years.csv \
  "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/aadf/region_id/dft_aadf_region_id_6.csv"

# Filter to 2025
python -c "
import csv
with open('london_aadf_all_years.csv') as fin, open('london_aadf_2025.csv', 'w', newline='') as fout:
    r = csv.DictReader(fin)
    w = csv.DictWriter(fout, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        if row['year'] == '2025':
            w.writerow(row)
"
```
