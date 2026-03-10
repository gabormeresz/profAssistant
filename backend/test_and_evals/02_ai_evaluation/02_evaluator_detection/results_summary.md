# 02 — Evaluator Error Detection Rate: Results Summary

> **Status:** Executed — 2026-03-02

## Configuration

| Parameter | Value                            |
| --------- | -------------------------------- |
| Model     | gpt-4o-mini                      |
| Date      | 2026-03-02                       |
| Runtime   | 42.53s                           |
| Pytest    | 1 failed, 7 passed (8 collected) |

## Detection Rate

| ID                                 | Category    | Verdict          | Score | Targeted Dim. Scores                                        |
| ---------------------------------- | ----------- | ---------------- | ----- | ----------------------------------------------------------- |
| S1_missing_fields                  | Structural  | NEEDS_REFINEMENT | 0.73  | completeness=0.60                                           |
| S2_wrong_class_count               | Structural  | NEEDS_REFINEMENT | 0.66  | content_coverage=0.60, completeness=0.60                    |
| P1_vague_objectives                | Pedagogical | NEEDS_REFINEMENT | 0.73  | learning_objectives=0.50                                    |
| P2_bad_progression                 | Pedagogical | NEEDS_REFINEMENT | 0.68  | progression=0.50                                            |
| P3_generic_activities              | Pedagogical | NEEDS_REFINEMENT | 0.73  | activities=0.60                                             |
| M1_vague_and_offtopic              | Mixed       | NEEDS_REFINEMENT | 0.50  | learning_objectives=0.30, content_coverage=0.50             |
| M2_progression_activities_complet. | Mixed       | NEEDS_REFINEMENT | 0.66  | progression=0.60, activities=0.50, completeness=**0.80** ⚠️ |

**Detection Rate: 7/7 (100%)** ✅

**Dimension Accuracy: 6/7 (86%)** — M2 `completeness` scored 0.80 (above 0.75 threshold)

## Key Findings

1. **100% detection rate** — All 7 deliberately flawed outputs were correctly classified as `NEEDS_REFINEMENT` by `gpt-4o-mini`. No false negatives on the verdict level.
2. **Dimension localisation mostly accurate** — In 6/7 cases the evaluator scored the targeted dimensions below 0.75, correctly identifying _where_ the flaw was.
3. **M2 completeness false-high** — The M2 case (missing `key_topics` in 2/6 classes) received `completeness=0.80`. The evaluator flagged the case overall (score=0.66, verdict=NEEDS_REFINEMENT) but did not penalise the completeness dimension specifically. This suggests the model conflates "completeness" with having all 6 classes present rather than checking for missing subsections within classes.
4. **M1 strongest detection** — The mixed off-topic case (cooking, gardening, music in a CS course) was the most clearly rejected (score=0.50), with `learning_objectives=0.30` — the lowest dimension score across all cases.
5. **Score range** — Flawed outputs scored between 0.50–0.73, all below the 0.80 approval threshold.

## Log References

- `tests/logs/run.log` — Full pytest output
- `tests/artifacts/detection_results.json` — Detection rate raw data (7 cases with full breakdowns)
