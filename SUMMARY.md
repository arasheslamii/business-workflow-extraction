# Summary

Post-training `Qwen2.5-1.5B-Instruct` to convert free-text descriptions of small
business processes into a strict 10-field structured workflow analysis.

## What was built

A fully scripted, seeded pipeline: synthetic data generation → LoRA fine-tune
(bf16; 4-bit path available) → three-layer evaluation → failure analysis. All of it runs
non-interactively; the numbers below were produced by the code in this repo.

**Data.** 120 train / 12 dev / 40 eval (28 synthetic + 12 real human-written PET
process descriptions). Split by scenario with zero shared scenarios; independently
re-verified (max pairwise 5-gram Jaccard across all 172 records: **0.011** against
a 0.75 threshold).

**Training.** LoRA r=16 on attention *and* MLP projections, bf16, 90 optimizer
steps, loss on completion tokens only. 18.5M trainable params (1.18%).

**Evaluation.** Three layers: structural (deterministic), content heuristics
(deterministic, judge-independent), and LLM-as-judge (per-field 1–5 rubric plus
blinded pairwise in both orders).

## Key results

**The honest comparison is against the 2-shot baseline, not zero-shot.** A
zero-shot 1.5B fails mostly on JSON *formatting*, so a two-arm before/after would
report a formatting win as a reasoning win. The 2-shot arm (exemplars from train
only) closes that gap and is what the tuned model is measured against.

| | Base 0-shot | Base 2-shot | **Tuned** |
|---|---|---|---|
| Schema valid | 70% | 80% | **98%** |
| AI-step grounding (content recall) | 0.230 | 0.326 | **0.420** |
| Length ratio vs reference | 0.389 | 0.702 | **0.838** |
| Judge rubric mean (1–5) | 3.04 | 3.23 | **3.41** |
| Tuned's pairwise record vs this arm | 31W/6T/3L | 30W/7T/3L | — |

Blinded pairwise, both orders: tuned wins **30/40 against the 2-shot baseline**
(91% excluding ties), margin 95% CI **[+0.47, +0.85]** — clear of zero.

The gains concentrate where the baseline was weakest: `contradictory` inputs go
from 57% to 100% schema-valid, and `vague` inputs show the largest rubric gain
(+0.50). The base model's dominant deficit was *declining to fill the hardest
fields* — 11 empty `ai_agent_steps` at zero-shot, 8 at 2-shot, **0 after tuning**.

**Strict-JSON went 0% → 98%, and this is deliberately deprioritised.** Every one
of the 80 base generations was markdown-fenced; the identical repair function
applied to all arms recovers 100% of them. That 98-point swing is formatting
discipline, not workflow quality, and reporting it as the headline would be
misleading.

## Limitations

**Synthetic-data circularity, partially mitigated.** References were authored by
an LLM and the judge is an LLM, so layer 3 grades synthetic data with the same
class of system that produced it. Three things reduce but do not remove this: the
judge is a **different model family** from the reference author; the **12 PET
records are real human-written text**; and the **deterministic layer is entirely
judge-independent** and carries equal weight. All three signals agree on
direction.

**n=40 limits precision.** The pairwise CI is clear of zero, but per-slice
findings (7 contradictory records, 12 PET) are indicative only. Nothing here
should be read as a precise effect size.

**The judge is not deterministic even at temperature 0.** It is a thinking model
(~1300–1900 thinking tokens per call) and was measured returning different field
scores for the same prompt. The on-disk response cache, not temperature, is what
makes the numbers reproducible. **Position inconsistency was 15–18%** — that
fraction of pairwise verdicts flipped when the two responses swapped places, and
those are counted as ties.

**The judge is lite-tier by force.** `gemini-3.6-flash` and `gemini-3.5-flash`
are capped at 20 requests/day on free tier; `gemini-2.5-flash` and
`gemini-2.5-flash-lite` return 404. `gemini-3.5-flash-lite` was the only reachable
model with adequate quota for a 280-call run.

**The dev curve shows a plateau, not detected overfitting.** Dev loss went
1.1796 → 1.1320 → 1.1375 while train loss fell 1.578 → 0.889. The epoch-3 uptick
is **+0.0055 on 12 examples** — far inside noise. The defensible reading is that
the model *extracted what it can from 120 examples*, not that overfitting was
observed. This matters for v0.2: it argues for more **data**, not more epochs.

**Two fields regressed.** `bottlenecks_and_risks` (3.19 → 2.77) and
`human_approvals_controls` (2.53 → 2.35). Not under-generation — tuned is closer
to reference length than either baseline. It learned the reference's rhetorical
form (long causal "X, so Y" statements) without its evidential specificity
(named entities, figures from the input). Style is cheap to learn from 120
examples; specificity is not. See `results/failures.md`.

**One catastrophic failure.** `eval_syn_012` emitted Python-style string
concatenation inside JSON (`"..." + "..."`) on an input stating a refund policy
three inconsistent ways — a structure never seen in training. Not truncation.
Strict-JSON compliance is real but shallow: it breaks when content pushes toward
an unsupervised structure.

## v0.2

Assuming weekly responsibility for this, in priority order:

1. **More data, not more epochs.** The dev plateau says the 120-example signal is
   exhausted. Target ~500–1000 examples, weighted toward the failure modes:
   single-document contradictions (only 3 exist in train — `train_017`,
   `train_068`, `dev_010`), and inputs that enumerate competing alternatives.
2. **Real customer data.** The PET slice shows transfer to real text, but 12
   records with unverified references is not an evaluation. Replacing synthetic
   references with Next Verse's own annotated workflows removes the circularity
   at its root rather than mitigating it.
3. **Schema-constrained decoding.** Would eliminate the `eval_syn_012` class of
   failure entirely and make the strict-JSON metric uninformative by
   construction — which is the right outcome, since it never measured quality.
4. **Better judge, and calibrate it.** A stronger judge plus a small
   human-labelled subset to measure judge–human agreement. A 15–18% position
   inconsistency rate is the current ceiling on how much layer 3 can be trusted.
5. **Continuous evaluation.** The pipeline is already scripted and cached; wiring
   it to run per-checkpoint would turn each week's change into a tracked
   regression test rather than a one-off comparison.
6. **Targeted work on the two regressed fields.** They are the most open-ended
   reasoning targets in the schema and the clearest evidence that the model
   learned form before substance.
