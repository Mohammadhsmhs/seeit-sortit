# Evaluation Report

- **Date:** 2026-06-02 05:22
- **Reports tested:** 50
- **Mode:** mock (keyword matching)

---

## Classification Accuracy

**Overall accuracy:** 54.0% (27/50)

### Per-Category Precision

| Category | Precision | Predicted Count |
|---|---|---|
| Street Lighting and Traffic | 100.0% | 1 |
| Street Cleanliness | 100.0% | 1 |
| Trees and Vegetation | 60.0% | 5 |
| Roads and Highways | 56.0% | 25 |
| Waste and Fly-Tipping | 53.3% | 15 |
| Vehicles | 0.0% | 1 |
| Pavements and Footways | 0.0% | 1 |
| Parks and Public Spaces | 0.0% | 1 |

### Confusion Matrix (Top 10 Categories)

| Actual \ Predicted | Road and High | Wast and Fly- | Street Cleanliness | Tree and Vege | Vehicles | Antisocial Behaviour | Utilities | Housing | Stre Ligh and | Pave and Foot |
|---|---|---|---|---|---|---|---|---|---|---|
| Road and High | **14** | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| Wast and Fly- | 5 | **8** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Street Cleanliness | 3 | 5 | **1** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tree and Vege | 1 | 0 | 0 | **3** | 0 | 0 | 0 | 0 | 0 | 1 |
| Vehicles | 0 | 1 | 0 | 0 | **0** | 0 | 0 | 0 | 0 | 0 |
| Antisocial Behaviour | 1 | 0 | 0 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| Utilities | 1 | 0 | 0 | 0 | 0 | 0 | **0** | 0 | 0 | 0 |
| Housing | 0 | 0 | 0 | 1 | 0 | 0 | 0 | **0** | 0 | 0 |
| Stre Ligh and | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **1** | 0 |
| Pave and Foot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |

### Top Misclassifications

| Actual | Predicted | Count |
|---|---|---|
| Waste and Fly-Tipping | Roads and Highways | 5 |
| Street Cleanliness | Waste and Fly-Tipping | 5 |
| Street Cleanliness | Roads and Highways | 3 |
| Trees and Vegetation | Roads and Highways | 1 |
| Vehicles | Waste and Fly-Tipping | 1 |
| Roads and Highways | Vehicles | 1 |
| Antisocial Behaviour | Roads and Highways | 1 |
| Trees and Vegetation | Pavements and Footways | 1 |
| Utilities | Roads and Highways | 1 |
| Roads and Highways | Trees and Vegetation | 1 |

---

## Routing Accuracy

**Borough match accuracy:** 94.0% (47/50)

### Sample Mismatches

| Report ID | Actual Borough | Predicted Borough |
|---|---|---|
| 9388636 | Southwark | Lambeth |
| 9161213 | Islington | Haringey |
| 9517262 | Southwark | Lambeth |

---

## Severity Distribution

- **Range:** 3 - 9
- **Mean:** 6.3
- **Out of range (not 1-10):** 0

```
   1 |  (0)
   2 |  (0)
   3 | # (1)
   4 | ##### (3)
   5 | ################ (9)
   6 | ############################## (16)
   7 | ###################### (12)
   8 | ############### (8)
   9 | # (1)
  10 |  (0)
```

---

## Interpretation

The mock provider uses keyword matching rather than LLM reasoning. Classification accuracy reflects how well keyword banks align with FixMyStreet's own category labels. With Llama 3.3 70B via NVIDIA NIM, we expect significantly higher accuracy due to semantic understanding.

Routing accuracy depends on whether the report has GPS coordinates and/or a recognisable postcode in the address field. The mock provider does not affect routing since it is entirely rule-based.