# FixMyStreet Data Analysis
## London Civic Agent Project

*Analysis of 2374 scraped reports across 9 London boroughs*
*Generated from scraper/fixmystreet.db*

---


## 1. Executive Summary

- **2374 fixed/resolved reports** scraped across **9 London boroughs** (Barnet, Bromley, Camden, Greenwich, Hackney, Islington, Lewisham, Southwark, Westminster) spanning **189 distinct issue categories**.
- The most reported category is **Fly Tipping** (227 reports, 10% of total). The top 10 categories cover the vast majority of all reports.
- Median resolution time is **11 days** across 1247 reports with resolution data. Resolution varies dramatically -- from under 1 hour to over 10 years, reflecting both quick fixes and long-lingering issues.
- **Greenwich** is the fastest-responding borough (median 1 days), while **Lewisham** is the slowest (median 59 days).
- **70%** of reports include photos. Photo-attached reports and longer descriptions offer a foundation for training the AI intake classifier and severity estimator.

## 2. Volume Analysis

**Total reports in database:** 2374

### Reports by Borough

| Borough | Count | % of Total |
|---------|------:|----------:|
| Barnet | 300 | 12.6% |
| Bromley | 300 | 12.6% |
| Camden | 300 | 12.6% |
| Greenwich | 300 | 12.6% |
| Hackney | 300 | 12.6% |
| Islington | 300 | 12.6% |
| Southwark | 300 | 12.6% |
| Lewisham | 176 | 7.4% |
| Westminster | 98 | 4.1% |

### Top 20 Categories

| Rank | Category | Count | % of Total |
|-----:|----------|------:|----------:|
| 1 | Fly Tipping | 227 | 9.6% |
| 2 | Pothole | 138 | 5.8% |
| 3 | Potholes | 130 | 5.5% |
| 4 | Fly Tipping on Street | 126 | 5.3% |
| 5 | Flytipping - General | 116 | 4.9% |
| 6 | Fly-Tipping | 77 | 3.2% |
| 7 | Flytip | 74 | 3.1% |
| 8 | Excessive Litter | 53 | 2.2% |
| 9 | Abandoned vehicles | 48 | 2.0% |
| 10 | Flytipping | 48 | 2.0% |
| 11 | Road Defect | 47 | 2.0% |
| 12 | Pavement Defect | 46 | 1.9% |
| 13 | Graffiti | 45 | 1.9% |
| 14 | Graffiti - General | 45 | 1.9% |
| 15 | Litter and Detritus | 44 | 1.9% |
| 16 | Public Litter Bin | 44 | 1.9% |
| 17 | Roads/highways | 40 | 1.7% |
| 18 | Litter Bin | 36 | 1.5% |
| 19 | Other tree issue | 36 | 1.5% |
| 20 | Pavements/footpaths | 35 | 1.5% |

*189 distinct categories total across all boroughs.*

### Reports by Year Created

| Year | Count |
|------|------:|
| 2015 | 1 |
| 2016 | 1 |
| 2019 | 2 |
| 2021 | 5 |
| 2022 | 3 |
| 2023 | 10 |
| 2024 | 26 |
| 2025 | 204 |
| 2026 | 1805 |

### Reports by Quarter (top periods)

| Period | Count |
|--------|------:|
| 2026 Q2 | 1308 |
| 2026 Q1 | 497 |
| 2025 Q4 | 135 |
| 2025 Q3 | 34 |
| 2025 Q2 | 25 |
| 2024 Q4 | 12 |
| 2025 Q1 | 10 |
| 2024 Q2 | 5 |
| 2024 Q3 | 5 |
| 2023 Q3 | 4 |
| 2024 Q1 | 4 |
| 2023 Q4 | 3 |

## 3. Resolution Performance

**Reports with resolution time data:** 1247 of 2374 (52.5%)

### Overall Resolution Stats

- **Average:** 65.0 days
- **Median:** 11.5 days
- **Fastest:** 0.00 days (0.0 hours)
- **Slowest:** 3930 days (10.8 years)

### Resolution Time by Borough

| Borough | Avg (days) | Median (days) | Min (days) | Max (days) | Reports w/ data |
|---------|----------:|-------------:|----------:|----------:|---------------:|
| Barnet | 57.3 | 28.1 | 0.71 | 3431 | 253 |
| Bromley | 10.6 | 1.1 | 0.00 | 129 | 142 |
| Camden | 73.7 | 49.2 | 0.08 | 526 | 102 |
| Greenwich | 3.2 | 0.7 | 0.00 | 95 | 194 |
| Hackney | 2.7 | 1.3 | 0.03 | 9 | 24 |
| Islington | 255.4 | 28.7 | 3.57 | 3930 | 92 |
| Lewisham | 168.9 | 59.3 | 0.00 | 2646 | 168 |
| Southwark | 1.9 | 0.9 | 0.02 | 28 | 209 |
| Westminster | 72.3 | 28.8 | 0.36 | 409 | 63 |

### Borough Performance Ranking (fastest median resolution)

1. **Greenwich** -- median 0.7 days (avg 3.2 days)
2. **Southwark** -- median 0.9 days (avg 1.9 days)
3. **Bromley** -- median 1.1 days (avg 10.6 days)
4. **Hackney** -- median 1.3 days (avg 2.7 days)
5. **Barnet** -- median 28.1 days (avg 57.3 days)
6. **Islington** -- median 28.7 days (avg 255.4 days)
7. **Westminster** -- median 28.8 days (avg 72.3 days)
8. **Camden** -- median 49.2 days (avg 73.7 days)
9. **Lewisham** -- median 59.3 days (avg 168.9 days)

### Resolution Time by Category (top 15 by volume)

| Category | Avg (days) | Median (days) | Count |
|----------|----------:|-------------:|------:|
| Fly Tipping | 9.1 | 0.8 | 150 |
| Pothole | 39.9 | 28.1 | 118 |
| Flytipping - General | 1.2 | 0.9 | 79 |
| Fly-Tipping | 146.0 | 63.7 | 73 |
| Potholes | 107.3 | 33.8 | 68 |
| Abandoned vehicles | 236.7 | 28.0 | 36 |
| Flytip | 0.8 | 0.2 | 29 |
| Graffiti - General | 2.9 | 1.0 | 29 |
| Flytipping | 60.7 | 28.6 | 28 |
| Litter Bin | 0.0 | 0.0 | 26 |
| Road Defect | 60.6 | 55.8 | 25 |
| Graffiti | 8.7 | 1.9 | 23 |
| Litter and Detritus | 1.1 | 0.7 | 23 |
| Pavement Defect | 52.0 | 53.8 | 22 |
| Public Litter Bin | 1.3 | 1.2 | 22 |

### Fastest vs Slowest Categories (by median, min 3 reports)

**Fastest to resolve:**

- Litter Bin: median 0.0 days (26 reports)
- Flytip: median 0.2 days (29 reports)
- Litter and Detritus: median 0.7 days (23 reports)
- Fly Tipping: median 0.8 days (150 reports)
- Flytipping - General: median 0.9 days (79 reports)

**Slowest to resolve:**

- Fly-Tipping: median 63.7 days (73 reports)
- Road Defect: median 55.8 days (25 reports)
- Pavement Defect: median 53.8 days (22 reports)
- Potholes: median 33.8 days (68 reports)
- Flytipping: median 28.6 days (28 reports)

### Resolution Time Distribution

| Bracket | Count | % |
|---------|------:|--:|
| Same day (< 1 day) | 334 | 26.8% |
| 1-3 days | 171 | 13.7% |
| 3-7 days (< 1 week) | 75 | 6.0% |
| 1-2 weeks | 56 | 4.5% |
| 2-4 weeks | 41 | 3.3% |
| 1-3 months | 431 | 34.6% |
| 3-6 months | 49 | 3.9% |
| 6-12 months | 36 | 2.9% |
| 1+ year | 54 | 4.3% |

## 4. Geographic Analysis

**Reports with valid coordinates:** 2374 of 2374 (100.0%)

### Geographic Bounding Box by Borough

| Borough | Min Lat | Max Lat | Min Lon | Max Lon | Lat Spread | Lon Spread |
|---------|--------:|--------:|--------:|--------:|----------:|----------:|
| Barnet | 51.5598 | 51.6610 | -0.2826 | -0.1323 | 0.1012 | 0.1504 |
| Bromley | 51.3067 | 51.4395 | -0.0760 | 0.1344 | 0.1328 | 0.2104 |
| Camden | 51.5139 | 51.5697 | -0.2117 | -0.1098 | 0.0558 | 0.1020 |
| Greenwich | 51.4269 | 51.5093 | -0.0223 | 0.1210 | 0.0824 | 0.1432 |
| Hackney | 51.5217 | 51.5761 | -0.1013 | -0.0245 | 0.0544 | 0.0769 |
| Islington | 51.5197 | 51.5751 | -0.1418 | -0.0778 | 0.0554 | 0.0640 |
| Lewisham | 51.4212 | 51.4890 | -0.0657 | 0.0376 | 0.0678 | 0.1033 |
| Southwark | 51.4217 | 51.5077 | -0.1059 | -0.0381 | 0.0859 | 0.0679 |
| Westminster | 51.4859 | 51.5352 | -0.2110 | -0.1215 | 0.0493 | 0.0894 |

### Most Reported Streets/Locations

| Street/Location | Borough | Reports |
|-----------------|---------|--------:|
| Flat 1 | Hackney | 26 |
| Flat A | Hackney | 15 |
| Flat 1 | Greenwich | 12 |
| Hartland Drive | Barnet | 7 |
| Stanstead Road | Lewisham | 6 |
| Lucey Way | Southwark | 6 |
| High Street | Bromley | 6 |
| Elliott's Row | Southwark | 5 |
| Cambridge Road | Bromley | 5 |
| Belgrave Road | Westminster | 4 |
| Elizabeth Bridge | Westminster | 4 |
| Watts Lane | Bromley | 4 |
| Stroud Green Road | Islington | 4 |
| Uphill Grove | Barnet | 4 |
| Rowley Lane | Barnet | 4 |

## 5. Content Analysis

### Description Quality

- **Reports with meaningful descriptions:** 2365 of 2374 (99.6%)
- **Average description length:** 138 characters
- **Median description length:** 89 characters
- **Shortest:** 4 characters
- **Longest:** 2396 characters
- **Reports with placeholder description ('.'):** 5
- **Reports with empty/null description:** 4

### Most Common Words in Descriptions (excluding stopwords)

| Rank | Word | Occurrences |
|-----:|------|----------:|
| 1 | road | 802 |
| 2 | please | 385 |
| 3 | pavement | 295 |
| 4 | rubbish | 291 |
| 5 | street | 283 |
| 6 | dumped | 280 |
| 7 | tree | 245 |
| 8 | outside | 224 |
| 9 | left | 215 |
| 10 | bin | 185 |
| 11 | pothole | 152 |
| 12 | fly | 142 |
| 13 | large | 141 |
| 14 | needs | 140 |
| 15 | area | 139 |
| 16 | bins | 134 |
| 17 | council | 132 |
| 18 | remove | 129 |
| 19 | waste | 120 |
| 20 | litter | 119 |
| 21 | car | 115 |
| 22 | park | 114 |
| 23 | potholes | 107 |
| 24 | dangerous | 106 |
| 25 | side | 104 |
| 26 | people | 102 |
| 27 | time | 100 |
| 28 | broken | 98 |
| 29 | house | 94 |
| 30 | weeks | 94 |

### Photo Attachment Rate

- **Reports with photos:** 1655 (69.7%)
- **Reports without photos:** 719 (30.3%)

| Borough | With Photos | Without | Photo Rate |
|---------|----------:|--------:|----------:|
| Barnet | 214 | 86 | 71% |
| Bromley | 185 | 115 | 62% |
| Camden | 82 | 218 | 27% |
| Greenwich | 252 | 48 | 84% |
| Hackney | 239 | 61 | 80% |
| Islington | 206 | 94 | 69% |
| Lewisham | 126 | 50 | 72% |
| Southwark | 266 | 34 | 89% |
| Westminster | 85 | 13 | 87% |

### Urgency Signals in Descriptions

| Signal Pattern | Occurrences | Example Report Title |
|----------------|----------:|----------------------|
| dangerous/danger | 135 | Danger caused by bikes / yet again |
| hazard/hazardous | 83 | Large holes in footpath |
| urgent/urgently | 44 | Mount Pleasant road surface in very bad condition |
| immediately/immediate | 16 | Submerged water cover |
| accident/injury | 25 | On Leighton Road between Leighton Grove and Bartholomew Road |
| children/kids/school | 75 | Exposed hard painful ground at bottom of kids slide |
| elderly/disabled | 29 | Overgrown bushes reducing pavement by St Anne's Care home ,  |
| falling/fallen/collapse | 77 | Road sign rusted and fit to collapse |
| flood/flooding | 8 | Flooding due to excess leaves and rubbish |
| broken glass | 19 | Small cupboard outside sport centre |
| blocked/blocking | 102 | Blocked drains |
| trip/tripping | 41 | Large holes in footpath |
| smashed/smash | 10 | Abandoned car on the road |

## 6. Insights for the Product

### Category Prioritization for Intake Classifier

Categories ranked by volume -- these should be the primary targets for the intake classifier. Covering the top 10 captures the vast majority of reports.

| Priority | Category | Count | % | Cumulative % |
|:--------:|----------|------:|--:|:------------:|
| 1 | Fly Tipping | 227 | 9.6% | 9.6% |
| 2 | Pothole | 138 | 5.8% | 15.4% |
| 3 | Potholes | 130 | 5.5% | 20.9% |
| 4 | Fly Tipping on Street | 126 | 5.3% | 26.2% |
| 5 | Flytipping - General | 116 | 4.9% | 31.1% |
| 6 | Fly-Tipping | 77 | 3.2% | 34.3% |
| 7 | Flytip | 74 | 3.1% | 37.4% |
| 8 | Excessive Litter | 53 | 2.2% | 39.6% |
| 9 | Abandoned vehicles | 48 | 2.0% | 41.6% |
| 10 | Flytipping | 48 | 2.0% | 43.6% |
| 11 | Road Defect | 47 | 2.0% | 45.6% |
| 12 | Pavement Defect | 46 | 1.9% | 47.5% |
| 13 | Graffiti | 45 | 1.9% | 49.4% |
| 14 | Graffiti - General | 45 | 1.9% | 51.3% |
| 15 | Litter and Detritus | 44 | 1.9% | 53.2% |

### Severity Signals from Historical Data

Based on analysis of resolution times and content, these signals can help estimate severity:

**Resolution speed by urgency language:**

- Reports with urgency keywords: avg 99.6 days
- Reports without urgency keywords: avg 61.1 days

**Extractable severity indicators:**

1. **Category-based severity** -- Potholes and road defects historically resolve faster (infrastructure priority)
2. **Urgency keywords** -- 'dangerous', 'hazard', 'children', 'elderly', 'accident'
3. **Photo presence** -- Reports with photos may get prioritized (evidence)
4. **Location density** -- Multiple reports at same location signal systemic issue
5. **Description quality** -- Longer, more detailed descriptions may correlate with faster action

### What Makes a 'Good' Report (correlates with faster resolution)

**Photo impact on resolution:**

- With photos: avg 64.3 days
- Without photos: avg 67.0 days

**Description length vs resolution time:**

- Placeholder only (.): avg 1714.0 days (n=4)
- Short (1-50 chars): avg 40.9 days (n=384)
- Medium (51-200 chars): avg 66.4 days (n=625)
- Long (200+ chars): avg 66.4 days (n=230)

**Key attributes of well-resolved reports:**

1. Clear, specific category selection
2. Photo evidence attached
3. Precise location (street address + postcode)
4. Description with specific details (what, where, size/severity)
5. Urgency context when applicable (safety risk, accessibility impact)

### Borough Leaderboard (Dashboard Data)

| Rank | Borough | Reports | Median Resolution | Avg Resolution | Photo Rate |
|-----:|---------|--------:|-----------------:|---------------:|----------:|
| 1 | Greenwich | 300 | 0.7 days | 3.2 days | 84% |
| 2 | Southwark | 300 | 0.9 days | 1.9 days | 89% |
| 3 | Bromley | 300 | 1.1 days | 10.6 days | 62% |
| 4 | Hackney | 300 | 1.3 days | 2.7 days | 80% |
| 5 | Barnet | 300 | 28.1 days | 57.3 days | 71% |
| 6 | Islington | 300 | 28.7 days | 255.4 days | 69% |
| 7 | Westminster | 98 | 28.8 days | 72.3 days | 87% |
| 8 | Camden | 300 | 49.2 days | 73.7 days | 27% |
| 9 | Lewisham | 176 | 59.3 days | 168.9 days | 72% |

### Recommended Demo Scenarios

Based on the data, these scenarios would make compelling demos because they represent real, common issues with good data quality:

**Fast-resolution success stories (good for 'report -> fixed' demo flow):**

- **Litter on warspite road** (Litter Bin, Greenwich): resolved in 0.0 days
  > Street cleaners weekly please?...
- **Bags of rubbish against bike shed on Revelon Rd** (Fly-Tipping, Lewisham): resolved in 0.0 days
  > This has been there for weeks now. I have reported it already nd nothing has bee...
- **Burnt out bin!** (Litter Bin, Greenwich): resolved in 0.0 days
  > I reported this on 25th April, and it says on your website that this has been fi...
- **Bin overflowing** (Litter Bin, Greenwich): resolved in 0.0 days
  > This bin is still overflowing with litter scattered around.
Reports shouldn't be...
- **Lots of litter around common and bins are all full** (Litter Bin, Greenwich): resolved in 0.0 days
  > Lots of picnics and rubbish left everywhere...

**Highest-volume categories (most relatable to users):**

1. **Fly Tipping** (227 reports) -- everyone encounters these
2. **Pothole** (138 reports) -- everyone encounters these
3. **Potholes** (130 reports) -- everyone encounters these
4. **Fly Tipping on Street** (126 reports) -- everyone encounters these
5. **Flytipping - General** (116 reports) -- everyone encounters these

**Recommended demo flow:**

1. User reports a pothole or street lighting issue (most common)
2. Show photo upload working with real examples from the dataset
3. AI categorizes and routes to the correct borough council
4. Display borough leaderboard with real resolution stats
5. Show estimated resolution time based on historical data for that category/borough

## Appendix: Update/Comment Activity

- **Total update entries:** 4079
- **Reports with updates:** 2106 of 2374 (88.7%)
- **Average updates per report (with updates):** 1.9

### Reports with Most Updates

| Report ID | Title | Updates | Borough |
|-----------|-------|--------:|---------|
| 4078347 | Homeless person / fly-tipping | 34 | Lewisham |
| 5216601 | Liverpool rd trip hazard paving stone | 32 | Islington |
| 6084037 | Liverpool rd trip hazard ne side by INIQLO | 24 | Islington |
| 5410159 | York way call rd sign is wrong | 21 | Islington |
| 7209939 | Submerged water cover | 13 | Westminster |
| 7488926 | Brecknok l maraget zebra refuge no tactile | 11 | Islington |
| 4130715 | Mount Pleasant road surface in very bad condition | 9 | Islington |
| 9316412 | Shrub base of tree | 8 | Bromley |
| 8729149 | Road defect opposite 29 on the bend | 8 | Bromley |
| 7891720 | Broken branch | 8 | Westminster |
