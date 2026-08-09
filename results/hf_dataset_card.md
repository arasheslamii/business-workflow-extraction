---
license: mit
task_categories:
- text2text-generation
language:
- en
tags:
- business-process
- structured-extraction
- workflow-analysis
- json
size_categories:
- n<1K
---

# Business Process → Structured Workflow Analysis

A small, carefully-controlled dataset for turning free-text descriptions of how
a small business runs a process into a strict 10-field structured workflow
analysis.

Built to support a clean fine-tuning experiment: the splits are separated by
business *scenario* (not just by record), the evaluation set deliberately
includes harder and out-of-domain cases, and one evaluation slice is **real
human-written text** rather than synthetic.

## Task

**Input** — a description of how a small business currently handles a process.
Styles vary deliberately: a rambling owner email, consultant call notes, a
formal process document, a chat transcript.

**Output** — a JSON object with exactly these 10 fields:

| # | Field | Type / meaning |
|---|---|---|
| 1 | `objective` | string - the business objective this workflow exists to achieve |
| 2 | `trigger` | string - the specific event that initiates the workflow |
| 3 | `owner_and_participants` | object with "owner" (string) and "participants" (array of strings) |
| 4 | `inputs_data_required` | array of strings - inputs and data the process consumes |
| 5 | `systems_involved` | array of strings - software, tools or physical systems used today (may be empty if genuinely none) |
| 6 | `current_process` | array of strings - the process as it runs today, in order |
| 7 | `bottlenecks_and_risks` | array of strings - delays, failure modes and risks |
| 8 | `recommended_improved_process` | array of strings - the improved process, in order |
| 9 | `ai_agent_steps` | array of strings - steps of the improved process an AI agent could carry out |
| 10 | `human_approvals_controls` | array of strings - approvals and controls that must stay with a human |

## Splits

| Split | n | Purpose |
|---|---|---|
| `train` | 120 | Fine-tuning |
| `dev` | 12 | Held-out overfitting check during training |
| `eval_synthetic` | 28 | Primary evaluation, includes out-of-domain verticals |
| `eval_pet` | 12 | **Real human-written** process descriptions |

Each record carries: `id`, `source`, `split`, `vertical`, `process`, `style`,
`difficulty` (`standard` / `vague` / `contradictory`), `ood_vertical`, `input`,
`gold`, `reference_type`.

`train` spans 12 business verticals × 12 process types. `eval_synthetic` adds
three verticals never seen in training (vet clinic, law firm, car repair
garage).

## Generation method

Synthetic records were authored by a frontier LLM in a **two-pass** process:
business scenarios and input descriptions were generated first, and gold
outputs generated separately in a later pass. Decoupling the two reduces
trivial stylistic coupling between an input and its own answer.

Diversity was enforced by construction across vertical, process type, writing
style, and difficulty — including inputs with **missing information** (`vague`)
and inputs that **contradict themselves** (`contradictory`).

### Quality control

Every claim below is independently re-derived by `scripts/02_verify_data.py` in
the companion repository, written separately from the generator's own QC:

- **Schema validation** on all 172 reference outputs — 100% valid.
- **Near-duplicate detection** — word 5-gram Jaccard over every record pair.
  Maximum observed similarity: **0.011** (threshold 0.75).
- **Leakage checks** — zero exact input collisions; zero shared scenarios
  between train/dev and evaluation splits.
- **Field completeness and length distributions** recorded per split in
  `data_manifest.json`.
- **Stratified manual review** of a sampled subset.

## The PET slice (real text)

`eval_pet` is built from **real, human-written** business process descriptions,
so the evaluation is not purely synthetic-on-synthetic.

- **Source**: [https://huggingface.co/datasets/patriziobellan/PET](https://huggingface.co/datasets/patriziobellan/PET)
- **Paper**: arXiv:2203.04860
- **Licence**: MIT — permissive, allows redistribution with attribution.
- **Documents used** (12): `doc-1.3`, `doc-1.4`, `doc-10.2`, `doc-2.1`, `doc-2.2`, `doc-3.5`, `doc-4.1`, `doc-5.3`, `doc-5.4`, `doc-6.1`, `doc-6.4`, `doc-9.1`
- **What was taken**: only the raw narrative text. All PET annotations
  (`ner_tags`, relations, sentence-IDs, token-IDs) were discarded.

> ⚠️ **PET reference outputs are `model_generated_unverified`.** They were
> produced by a model under the same grounding rules and have **not** been
> checked by a human annotator. For this slice, treat the references as a
> comparison point rather than ground truth — pairwise judging is the more
> appropriate signal.

## Known weaknesses

1. **Synthetic references.** Apart from the input text of the PET slice, both
   inputs and gold outputs are LLM-authored. Models trained on this learn one
   frontier model's *idea* of a good workflow analysis, not a validated
   business standard.
2. **The `ood_vertical` flag understates novelty.** All 12 PET
   records are flagged `False`, yet every PET vertical is absent from training.
   Compute vertical novelty against the training set directly rather than
   trusting the flag alone.
3. **Contradiction coverage is thin.** Only 3 records embed a contradiction
   *within a single document* (as opposed to between speakers), which is the
   harder and more realistic case.
4. **Scale.** 120 training examples is enough to demonstrate a method,
   not to saturate one.
5. **`systems_involved` is legitimately empty** in some records — a business may
   genuinely use no software. Do not treat empty as a defect for that field.
6. **English only, UK-centric small-business framing.**

## Intended use

Research and evaluation of structured-extraction fine-tuning. Suitable for
demonstrating method, ablations and evaluation design. **Not** suitable as a
source of business advice, nor as a benchmark of real-world workflow-analysis
quality — the references are not expert-validated.

## Licence

MIT, consistent with the PET source dataset.
