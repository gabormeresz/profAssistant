# 2.3 LLM-as-a-Judge — Results Summary

## Status

**Fail: 2/5 assertions pass** — Zero-shot quality falls below the production threshold under the GPT-5.2 judge. Meta-evaluation and floor assertions pass. Run date: 2026-03-03.

## Configuration

- **Generation model**: gpt-4o-mini (generator + internal evaluator)
- **Judge model**: GPT-5.2 (reasoning_effort=low via evaluator preset)
- **Approval threshold**: 0.8 (production default)
- **Prompt set**: 15 prompts — 3 per discipline across 5 disciplines
- **Phase 2 duration**: 137.83s (15 GPT-5.2 calls)

## Scope Limitations

- Results validated on **gpt-4o-mini only**; other models may exhibit different zero-shot quality levels.
- Tested on **Course Outline only**; the shared base architecture (`agent/base/`) suggests similar behavior for other modules, but this remains unverified.

## Zero-Shot Quality (GPT-5.2 judge scores on first-pass drafts)

| Metric                            | Threshold | Actual         | Pass |
| --------------------------------- | --------- | -------------- | ---- |
| Mean draft score                  | ≥ 0.80    | **0.784**      | ❌   |
| % prompts with draft score ≥ 0.80 | ≥ 80%     | **20%** (3/15) | ❌   |
| Min draft score                   | ≥ 0.70    | **0.74**       | ✅   |
| Max draft score                   | —         | 0.816          | —    |
| Std                               | —         | 0.0221         | —    |

### Per-Dimension Mean Draft Scores (GPT-5.2 judge)

| Dimension           | Mean  | Min  | Threshold (≥ 0.75) | Pass |
| ------------------- | ----- | ---- | ------------------ | ---- |
| learning_objectives | 0.803 | 0.78 | ≥ 0.75             | ✅   |
| content_coverage    | 0.705 | 0.62 | ≥ 0.75             | ❌   |
| progression         | 0.788 | 0.70 | ≥ 0.75             | ✅   |
| activities          | 0.755 | 0.72 | ≥ 0.75             | ✅   |
| completeness        | 0.901 | 0.90 | ≥ 0.75             | ✅   |

### Per-Prompt Scores

| Prompt ID                      | Discipline       | Judge | Internal | Verdict          |
| ------------------------------ | ---------------- | ----- | -------- | ---------------- |
| cs_01_data_structures          | Computer Science | 0.794 | 0.90     | NEEDS_REFINEMENT |
| cs_02_operating_systems        | Computer Science | 0.784 | 0.88     | NEEDS_REFINEMENT |
| cs_03_intro_ml                 | Computer Science | 0.790 | 0.90     | NEEDS_REFINEMENT |
| ns_01_organic_chemistry        | Natural Sciences | 0.766 | 0.92     | NEEDS_REFINEMENT |
| ns_02_cell_biology             | Natural Sciences | 0.808 | 0.88     | APPROVED         |
| ns_03_thermodynamics           | Natural Sciences | 0.785 | 0.87     | NEEDS_REFINEMENT |
| hum_01_modern_philosophy       | Humanities       | 0.746 | 0.88     | NEEDS_REFINEMENT |
| hum_02_20th_century_literature | Humanities       | 0.790 | 0.88     | NEEDS_REFINEMENT |
| hum_03_macroeconomics          | Humanities       | 0.788 | 0.88     | NEEDS_REFINEMENT |
| ss_01_research_methods         | Social Sciences  | 0.815 | 0.88     | APPROVED         |
| ss_02_social_psychology        | Social Sciences  | 0.775 | 0.88     | NEEDS_REFINEMENT |
| ss_03_public_policy            | Social Sciences  | 0.816 | 0.92     | APPROVED         |
| eng_01_dsp                     | Engineering      | 0.770 | 0.87     | NEEDS_REFINEMENT |
| eng_02_structural_mechanics    | Engineering      | 0.794 | 0.92     | NEEDS_REFINEMENT |
| eng_03_robotics                | Engineering      | 0.740 | 0.90     | NEEDS_REFINEMENT |

## Meta-Evaluation (Internal evaluator vs GPT-5.2 judge)

| Metric                  | Threshold | Actual                     | Pass |
| ----------------------- | --------- | -------------------------- | ---- |
| MAE (internal vs judge) | < 0.15    | **0.1066**                 | ✅   |
| Bias                    | —         | +0.1066 (internal lenient) | —    |
| Internal mean           | —         | 0.8907                     | —    |
| Judge mean              | —         | 0.7840                     | —    |

### Per-Dimension MAE

| Dimension           | MAE    |
| ------------------- | ------ |
| learning_objectives | 0.0553 |
| content_coverage    | 0.2087 |
| progression         | 0.1013 |
| activities          | 0.1247 |
| completeness        | 0.0547 |

## Assertion Results

| #   | Assertion                         | Threshold | Actual      | Result |
| --- | --------------------------------- | --------- | ----------- | ------ |
| A   | Mean draft score ≥ 0.80           | ≥ 0.80    | 0.784       | ❌     |
| B   | % prompts with draft score ≥ 0.80 | ≥ 80%     | 20%         | ❌     |
| C   | Min draft score ≥ 0.70            | ≥ 0.70    | 0.740       | ✅     |
| D   | Per-dimension means ≥ 0.75        | ≥ 0.75    | 0.705–0.901 | ❌     |
| E   | MAE (internal vs judge) < 0.15    | < 0.15    | 0.1066      | ✅     |

## Key Findings

1. **Zero-shot quality falls short under the strongest available judge.** The mean draft score (0.784) misses the 0.80 production threshold by −0.016. Only 3 of 15 prompts (20%) reach APPROVED status. This indicates that gpt-4o-mini's first-pass outputs, while structurally complete, lack the depth of content coverage and activity specificity that GPT-5.2 demands.

2. **The refinement loop is justified for gpt-4o-mini.** Unlike the internal evaluator (which approves all 15 drafts), the GPT-5.2 judge flags 12/15 as NEEDS_REFINEMENT. This validates the system's iterative evaluate→refine architecture: the refinement loop exists precisely to close the gap between draft quality and the production threshold, and the strongest model confirms that gap is real.

3. **Content coverage is the weakest dimension.** The content_coverage mean (0.705) is the only dimension that fails the ≥ 0.75 threshold, with a minimum of 0.62 (hum_01_modern_philosophy). The judge consistently identified missing subtopics, gaps in foundational coverage, and insufficient depth — areas where a single generation pass inherently struggles without external tool augmentation or iterative refinement.

4. **Completeness remains a strong point.** The completeness dimension scores 0.901 mean with a 0.90 floor — every prompt produces structurally well-formed outlines with all required fields populated. The generation prompts excel at structural adherence even when content depth is lacking.

5. **The internal evaluator is significantly more lenient than GPT-5.2.** The MAE of 0.1066 passes the < 0.15 threshold but the bias is notable: +0.1066 means the internal gpt-4o-mini evaluator consistently scores ~0.11 points higher than GPT-5.2. The largest disagreement is on content_coverage (MAE 0.209), where gpt-4o-mini lacks the domain expertise to identify missing subtopics that GPT-5.2 catches. This lenient bias means the internal evaluator may approve drafts that a stronger model would refine further.

6. **Cross-discipline patterns emerge.** Social Sciences prompts perform best (2/3 approved, mean ~0.80), while Engineering and Humanities trail (0/3 approved each). The weakest prompt overall is eng_03_robotics (0.74), followed by hum_01_modern_philosophy (0.746) — both are interdisciplinary topics where content coverage gaps are most pronounced.

## Log References

- `tests/logs/phase2_2026-03-03.log` — Phase 2 (judge scoring + analysis + assertions)
