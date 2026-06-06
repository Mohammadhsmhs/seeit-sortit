# London Civic Agent -- Verification Report

**Date:** 2 June 2026
**Test environment:** macOS Darwin 25.3.0, Python 3.14.5, pytest 9.0.3
**Provider tested:** MockProvider (fully offline)

---

## 1. What Works

### Main Demo (`python -m src.main --demo`)
- All 3 scenarios complete without errors.
- Categories are correctly identified:
  - Scenario 1: **Waste and Fly-Tipping / Fly-Tipping**
  - Scenario 2: **Roads and Highways / Pothole**
  - Scenario 3: **Street Lighting and Traffic / Streetlight Out**
- Severity scores land within the 1-10 range (all 3 scored 10/10 due to rich proximity data and hazard keywords).
- Submission text is well-structured with clear sections (CIVIC ISSUE REPORT, LOCATION, ROUTING, DESCRIPTION, SEVERITY ASSESSMENT).
- TfL detection works: Scenario 2 (A205 South Circular) correctly routes to Transport for London.

### Demo Runner (`python -m src.demo.run_demo --fast`)
- Completes without errors and produces colored terminal output.
- All 3 scenarios produce full results with category, severity, routing, and submission.
- Summary table renders correctly with all scenarios.
- Escalation path displays for Scenario 3.

### Test Suite (`pytest src/tests/ -v`)
- **55 tests, all passing** (expanded from original 5).
- Coverage includes: individual agents, full pipeline, severity range validation, routing, edge cases, mock mode offline verification, MockProvider unit tests, and performance.

### Dashboard (`src.dashboard.app`)
- `/api/stats` endpoint returns HTTP 200 with borough stats, category stats, and resolution distribution from scraper DB.
- `/api/boroughs` endpoint returns HTTP 200 with borough performance leaderboard (median resolution times, fastest/slowest categories).
- Data includes: Barnet, Bromley, Camden, Greenwich, Hackney, Islington, Southwark, Tower Hamlets, Westminster.

### Data Loading (`data/raw/load_data.py`)
- All 6 datasets verified successfully:
  - STATS19 Road Collisions: 20,834 London collisions from 100,927 total
  - STATS19 Road Casualties: 128,272 total records
  - Schools (GIAS): 5,881 London schools (3,194 open)
  - NHS Trust Sites: 6,432 London sites from 45,671 total
  - CQC Care Directory: 9,390 London providers from 56,778 total
  - Census LSOAs: 4,994 London LSOAs covering 33 boroughs (9,089,736 population)

### Mock Mode
- Runs **fully offline** -- verified by blocking `socket.connect` during pipeline execution. Zero network calls detected.

---

## 2. What Doesn't Work (Known Limitations)

### Borough Routing Accuracy (Nearest-Centroid Method)
The routing agent uses distance to each borough's centre point rather than polygon boundary checks. This causes misrouting in some cases:

- **Scenario 1** (Vallance Road, E1): Routes to **City of London Corporation** instead of the expected **Tower Hamlets**. Vallance Road at (51.521, -0.066) is 1.94 km from the City of London centroid but is geographically within Tower Hamlets. The Tower Hamlets centroid at (51.510, -0.027) is further away.
- **Scenario 3** (Lambeth Palace Road): Routes to **City of Westminster** instead of the expected **Lambeth**. The coordinates (51.498, -0.119) are 1.19 km from Westminster's centroid but the road straddles the Lambeth/Westminster boundary.

This is a known architectural limitation. The centroid-distance approach works reasonably for most of London but fails near borough boundaries, especially around the City of London (which is very small and geographically central).

### Severity Score Clustering at Maximum
All 3 demo scenarios score **10/10** severity. The combination of rich proximity data (real schools, hospitals, care homes, collision hotspots, population density) plus hazard keywords pushes scores to the cap. While the individual scoring components work correctly (and the cap correctly prevents scores >10), the result is that differentiation between scenarios is lost.

---

## 3. Warnings and Deprecations

- **No warnings or deprecations** observed in any test run or demo execution.
- Python 3.14.5 compatibility is clean.
- All imports resolve without issues.
- No deprecated API usage detected in Flask, Pydantic, or standard library calls.

---

## 4. Performance

| Metric | Time |
|--------|------|
| Single scenario (mock mode) | ~0.004s |
| All 3 demo scenarios (mock mode) | ~0.002s |
| Average per scenario | ~0.001s |
| Full test suite (55 tests) | ~35s |

The test suite time is dominated by ProximityIndex loading (reading CSV data from disk for each SeverityAgent instantiation). The pipeline logic itself is sub-millisecond in mock mode.

---

## 5. Recommendations

### High Priority

1. **Polygon-based borough routing**: Replace the nearest-centroid approach with GeoJSON polygon containment checks (e.g., using Shapely or a pre-computed spatial index). The boroughs.json file could be extended with boundary polygons from the ONS Open Geography Portal. This would fix the misrouting of Scenario 1 and 3.

2. **Severity score rebalancing**: With the real proximity data loaded, the additive scoring model saturates at 10/10 too easily. Consider:
   - Reducing proximity modifier values (e.g., +1 instead of +2 for nearby schools)
   - Using a multiplicative rather than additive approach
   - Introducing a diminishing-returns curve so early boosts matter more than late ones

### Medium Priority

3. **ProximityIndex caching**: The SeverityAgent loads all CSV data on every instantiation. Consider caching the parsed index at module level or using a singleton pattern. This would significantly speed up the test suite.

4. **Dashboard error handling**: The dashboard assumes the scraper DB exists and has the expected schema. If `fixmystreet.db` is missing or empty, the API endpoints will return 500 errors rather than empty results.

### Low Priority

5. **Address extraction improvements**: The regex-based address extractor captures partial addresses (e.g., "the pavement outside 42 Vallance Road" captures "the pavement outside 42 Vallance Road" rather than just "42 Vallance Road"). A more precise regex or NER-based approach could improve this.

6. **Non-London coordinate handling**: When coordinates are far outside London (e.g., Edinburgh at 55.95, -3.19), the system still routes to the nearest London borough without any warning. Consider adding a distance threshold that flags issues as "outside service area."
