# Evaluation report

Model: `Qwen/Qwen2.5-1.5B-Instruct` | LoRA r=16 alpha=32 | seed 20260807

Three arms. **Base (2-shot) is the competitive baseline** - a zero-shot small model fails mostly on JSON formatting, so comparing only against it would report a formatting win as if it were a reasoning win.


## Layer 1 - structural (deterministic)

`strict` = model emitted bare JSON. `lenient` = parsed after fence-stripping and balanced-brace extraction. **The same repair function is applied to every arm.** The strict/lenient gap is formatting discipline alone.

| Arm | Strict JSON | Lenient JSON | Schema valid | Fields present |
|---|---|---|---|---|
| Base (0-shot) | 0% | 100% | 70% | 96% |
| Base (2-shot) | 0% | 100% | 80% | 98% |
| Tuned (LoRA) | 98% | 98% | 98% | 98% |

### Per-field presence (non-empty)

| Field | Base (0-shot) | Base (2-shot) | Tuned (LoRA) |
|---|---|---|---|
| `objective` | 100% | 100% | 98% |
| `trigger` | 100% | 100% | 98% |
| `owner_and_participants` | 100% | 100% | 98% |
| `inputs_data_required` | 100% | 100% | 98% |
| `systems_involved` | 100% | 100% | 98% |
| `current_process` | 100% | 100% | 98% |
| `bottlenecks_and_risks` | 100% | 100% | 98% |
| `recommended_improved_process` | 100% | 100% | 98% |
| `ai_agent_steps` | 72% | 80% | 98% |
| `human_approvals_controls` | 82% | 100% | 98% |

## Layer 2 - content heuristics (deterministic, judge-independent)

This layer carries equal weight to the judge. Gold answers were LLM-authored and the judge is an LLM, so layer 3 cannot fully escape circularity; these metrics can.

**Metric definitions** (a grounding number is meaningless without its definition - our own QC produced 0.23, 0.51 and 0.83 for 'the same' metric under three definitions):

- **`systems_grounded`** - Of the systems named in `systems_involved`, the fraction whose content words appear in the INPUT description. Measures hallucinated tooling. Scoped to `systems_involved` and `current_process` ONLY - see systems_novel_in_recommendation.
- **`systems_novel_in_recommendation`** - Count of systems named in `recommended_improved_process` that do NOT appear in the input. Reported as INFORMATION, never as an error: proposing a tool the business does not yet use is the point of the task. Penalising this would score the best outputs worst.
- **`current_process_grounded`** - Mean content-word recall of each `current_process` step against the input. Measures whether the described as-is process is supported by what the business actually said.
- **`step_coverage_vs_reference`** - For each reference `current_process` step, the best content-word recall achieved by any candidate step; averaged over reference steps. Recall-oriented: penalises omitting steps, not adding them.
- **`ai_steps_grounded_recall`** - HEADLINE grounding variant. Mean content-word recall of each `ai_agent_steps` entry against the union of `recommended_improved_process`. Answers: do the proposed AI steps refer to steps that were actually recommended?
- **`ai_steps_grounded_ngram`** - STRICTER variant of the same quantity: mean 3-gram Jaccard of each `ai_agent_steps` entry against the union of `recommended_improved_process`. Requires matching word order, so paraphrased-but-correct references score near zero. Reported alongside the recall variant precisely because the two disagree.
- **`length_ratio_vs_reference`** - Total characters across all list fields, divided by the same for the reference. 1.0 = reference length. Detects under-generation, the dominant base-model failure.

| Arm | `systems_grounded` | `current_process_grounded` | `step_coverage_vs_reference` | `ai_steps_grounded_recall` | `ai_steps_grounded_ngram` | `length_ratio_vs_reference` | `systems_novel_in_recommendation` |
|---|---|---|---|---|---|---|---|
| Base (0-shot) | 0.992 | 0.638 | 0.255 | 0.230 | 0.010 | 0.389 | 24.925 |
| Base (2-shot) | 0.728 | 0.619 | 0.328 | 0.326 | 0.017 | 0.702 | 32.325 |
| Tuned (LoRA) | 0.956 | 0.759 | 0.502 | 0.420 | 0.021 | 0.838 | 32.325 |

## Breakdowns by analysis axis

Axis definitions:

- **`source`** - synthetic vs pet_real (delivered field)
- **`ood_vertical`** - the delivered flag: synthetic records authored as out-of-domain
- **`vertical_unseen_in_train`** - DERIVED at analysis time: record's vertical does not occur in train+dev. Differs from ood_vertical because all 12 PET verticals are unseen yet flagged False.
- **`difficulty`** - standard / vague / contradictory (delivered field)


### Axis: `source`

| Group | Arm | n | `schema_valid` | `ai_steps_grounded_recall` | `length_ratio_vs_reference` |
|---|---|---|---|---|---|
| `pet_real` | Base (0-shot) | 12 | 0.833 | 0.348 | 0.387 |
| `pet_real` | Base (2-shot) | 12 | 0.917 | 0.396 | 0.638 |
| `pet_real` | Tuned (LoRA) | 12 | 1.000 | 0.475 | 0.870 |
| `synthetic` | Base (0-shot) | 28 | 0.643 | 0.179 | 0.390 |
| `synthetic` | Base (2-shot) | 28 | 0.750 | 0.296 | 0.730 |
| `synthetic` | Tuned (LoRA) | 28 | 0.964 | 0.397 | 0.824 |

### Axis: `ood_vertical`

| Group | Arm | n | `schema_valid` | `ai_steps_grounded_recall` | `length_ratio_vs_reference` |
|---|---|---|---|---|---|
| `False` | Base (0-shot) | 24 | 0.750 | 0.279 | 0.384 |
| `False` | Base (2-shot) | 24 | 0.833 | 0.367 | 0.706 |
| `False` | Tuned (LoRA) | 24 | 0.958 | 0.428 | 0.834 |
| `True` | Base (0-shot) | 16 | 0.625 | 0.157 | 0.397 |
| `True` | Base (2-shot) | 16 | 0.750 | 0.263 | 0.696 |
| `True` | Tuned (LoRA) | 16 | 1.000 | 0.409 | 0.843 |

### Axis: `vertical_unseen_in_train`

| Group | Arm | n | `schema_valid` | `ai_steps_grounded_recall` | `length_ratio_vs_reference` |
|---|---|---|---|---|---|
| `False` | Base (0-shot) | 12 | 0.667 | 0.209 | 0.380 |
| `False` | Base (2-shot) | 12 | 0.750 | 0.338 | 0.774 |
| `False` | Tuned (LoRA) | 12 | 0.917 | 0.382 | 0.798 |
| `True` | Base (0-shot) | 28 | 0.714 | 0.239 | 0.393 |
| `True` | Base (2-shot) | 28 | 0.821 | 0.320 | 0.671 |
| `True` | Tuned (LoRA) | 28 | 1.000 | 0.437 | 0.855 |

### Axis: `difficulty`

| Group | Arm | n | `schema_valid` | `ai_steps_grounded_recall` | `length_ratio_vs_reference` |
|---|---|---|---|---|---|
| `contradictory` | Base (0-shot) | 7 | 0.429 | 0.038 | 0.408 |
| `contradictory` | Base (2-shot) | 7 | 0.571 | 0.262 | 0.653 |
| `contradictory` | Tuned (LoRA) | 7 | 1.000 | 0.443 | 0.833 |
| `standard` | Base (0-shot) | 20 | 0.850 | 0.327 | 0.388 |
| `standard` | Base (2-shot) | 20 | 0.900 | 0.387 | 0.656 |
| `standard` | Tuned (LoRA) | 20 | 1.000 | 0.457 | 0.846 |
| `vague` | Base (0-shot) | 13 | 0.615 | 0.184 | 0.380 |
| `vague` | Base (2-shot) | 13 | 0.769 | 0.266 | 0.799 |
| `vague` | Tuned (LoRA) | 13 | 0.923 | 0.351 | 0.827 |

## Layer 3 - LLM-as-judge

Judge: **`gemini-3.5-flash-lite`**, temperature 0, 40 items. Different model family from the reference author (Claude Opus 5), which removes direct self-preference but not general circularity.

Call stats: 254 API calls, 21 cache hits, 83 retries.

> **Judge determinism caveat.** Temperature 0 is *not* sufficient here: this is a thinking model (measured ~1300-1900 thinking tokens per rubric call) and the same prompt was observed returning different field scores across calls. The on-disk response cache - not temperature - is what makes these numbers reproducible after the fact.

> **Model selection was quota-forced.** `gemini-3.6-flash` and `gemini-3.5-flash` are both capped at 20 requests/day on the free tier and `gemini-2.5-flash`/`gemini-2.5-flash-lite` return 404, so the judge is a *lite*-tier model. A stronger judge would be a straightforward v0.2 upgrade.


### Per-field rubric (1-5)

| Field | Base (0-shot) | Base (2-shot) | Tuned (LoRA) |
|---|---|---|---|
| `objective` | 3.97 | 4.22 | 4.47 |
| `trigger` | 3.45 | 3.56 | 3.83 |
| `owner_and_participants` | 3.26 | 3.31 | 3.38 |
| `inputs_data_required` | 3.32 | 3.42 | 3.60 |
| `systems_involved` | 2.71 | 2.94 | 3.90 |
| `current_process` | 2.66 | 3.08 | 3.35 |
| `bottlenecks_and_risks` | 3.32 | 3.19 | 2.77 |
| `recommended_improved_process` | 3.11 | 3.33 | 3.30 |
| `ai_agent_steps` | 2.29 | 2.72 | 3.17 |
| `human_approvals_controls` | 2.34 | 2.53 | 2.35 |
| **mean** | **3.04** | **3.23** | **3.41** |

### Blinded pairwise

Every pair judged in **both orders**. Where the two orders disagree the verdict was driven by position, not content; those are counted as ties and the inconsistency rate is reported as the honest measure of judge reliability.

| Comparison | n | Wins | Ties | Losses | Win rate (excl. ties) | Margin 95% CI | Position inconsistency |
|---|---|---|---|---|---|---|---|
| tuned vs base_fewshot | 40 | 30 | 7 | 3 | 91% | [+0.47, +0.85] | 18% |
| tuned vs base_zeroshot | 40 | 31 | 6 | 3 | 91% | [+0.50, +0.88] | 15% |

**Margin** = (wins - losses)/n, percentile bootstrap. At n=40 a CI spanning 0 means the result is not statistically distinguishable from no difference.


---

Regenerate: `python scripts/06_eval_deterministic.py && python scripts/08_report.py`
