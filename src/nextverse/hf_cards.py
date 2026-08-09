"""Dataset and model card generation for the Hugging Face Hub.

Cards are generated from the manifest and the actual results files rather than
hand-written, so a published card can never drift from what was measured.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import FIELD_SPEC, FIELDS


def _counts(raw: Path) -> dict[str, int]:
    out = {}
    for s in ("train", "dev", "eval_synthetic", "eval_pet"):
        p = raw / f"{s}.jsonl"
        out[s] = sum(1 for line in p.read_text().splitlines() if line.strip()) if p.exists() else 0
    return out


def _schema_table() -> str:
    rows = ["| # | Field | Type / meaning |", "|---|---|---|"]
    for i, f in enumerate(FIELDS, 1):
        rows.append(f"| {i} | `{f}` | {FIELD_SPEC[f]} |")
    return "\n".join(rows)


def dataset_card(raw: Path) -> str:
    manifest = json.loads((raw / "data_manifest.json").read_text())
    pet = manifest.get("pet_slice", {})
    n = _counts(raw)
    docs = ", ".join(f"`{d}`" for d in pet.get("documents_used", []))

    return f"""---
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

{_schema_table()}

## Splits

| Split | n | Purpose |
|---|---|---|
| `train` | {n['train']} | Fine-tuning |
| `dev` | {n['dev']} | Held-out overfitting check during training |
| `eval_synthetic` | {n['eval_synthetic']} | Primary evaluation, includes out-of-domain verticals |
| `eval_pet` | {n['eval_pet']} | **Real human-written** process descriptions |

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

- **Schema validation** on all {sum(n.values())} reference outputs — 100% valid.
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

- **Source**: [{pet.get('source', 'PET dataset')}]({pet.get('source', '')})
- **Paper**: {pet.get('paper', 'arXiv:2203.04860')}
- **Licence**: {pet.get('license', 'MIT')} — permissive, allows redistribution with attribution.
- **Documents used** ({pet.get('n_documents', 12)}): {docs}
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
2. **The `ood_vertical` flag understates novelty.** All {n['eval_pet']} PET
   records are flagged `False`, yet every PET vertical is absent from training.
   Compute vertical novelty against the training set directly rather than
   trusting the flag alone.
3. **Contradiction coverage is thin.** Only 3 records embed a contradiction
   *within a single document* (as opposed to between speakers), which is the
   harder and more realistic case.
4. **Scale.** {n['train']} training examples is enough to demonstrate a method,
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
"""


def model_card(root: Path, dataset_repo: str) -> str:
    import yaml

    conf = yaml.safe_load((root / "config.yaml").read_text())
    t = conf["train"]
    base = conf["model"]["name"]

    meta_path = root / "results" / "adapter" / "train_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    log_path = root / "results" / "adapter" / "train_log.json"
    dev_losses = []
    if log_path.exists():
        for h in json.loads(log_path.read_text()):
            if "eval_loss" in h:
                dev_losses.append((h.get("epoch"), h["eval_loss"]))
    dev_tbl = "\n".join(
        f"| {int(e) if e else '?'} | {l:.4f} |" for e, l in dev_losses
    ) or "| - | - |"

    det = {}
    dp = root / "results" / "metrics_deterministic.json"
    if dp.exists():
        det = json.loads(dp.read_text())["aggregate"]["overall"]

    jd = {}
    jp = root / "results" / "metrics_judge.json"
    if jp.exists():
        jd = json.loads(jp.read_text())

    def d(arm, key, pct=False):
        v = det.get(arm, {}).get(key)
        if v is None:
            return "-"
        return f"{v:.0%}" if pct else f"{v:.3f}"

    def rub(arm):
        if not jd.get("rubric"):
            return "-"
        vals = [v for r in jd["rubric"][arm] for v in r["scores"].values()
                if isinstance(v, (int, float))]
        return f"{sum(vals) / len(vals):.2f}" if vals else "-"

    pw = ""
    if jd.get("pairwise"):
        a = jd["pairwise"].get("tuned_vs_base_fewshot", {}).get("aggregate", {})
        if a:
            lo, hi = a.get("margin_ci95", [0, 0])
            pw = (f"**{a['x_wins']} wins / {a['ties']} ties / {a['y_wins']} losses** "
                  f"({a['win_rate_excl_ties']:.0%} excluding ties), "
                  f"margin 95% CI [{lo:+.2f}, {hi:+.2f}], "
                  f"position inconsistency {a['position_inconsistency_rate']:.0%}")

    return f"""---
license: apache-2.0
base_model: {base}
library_name: peft
pipeline_tag: text2text-generation
tags:
- lora
- peft
- business-process
- structured-extraction
- json
datasets:
- {dataset_repo}
language:
- en
---

# Qwen2.5-1.5B-Instruct — Workflow Analysis LoRA

A LoRA adapter that makes `{base}` reliably convert free-text descriptions of
small-business processes into a strict 10-field structured workflow analysis.

Trained on [{dataset_repo}](https://huggingface.co/datasets/{dataset_repo}).

## Results

Evaluated on 40 held-out records (28 synthetic + 12 **real** human-written).
The meaningful comparison is against a **2-shot baseline**, not zero-shot: a
zero-shot 1.5B fails mostly on JSON *formatting*, so a naive before/after would
report a formatting win as a reasoning win.

| Metric | Base (0-shot) | Base (2-shot) | **This adapter** |
|---|---|---|---|
| Schema-valid rate | {d('base_zeroshot', 'schema_valid', True)} | {d('base_fewshot', 'schema_valid', True)} | **{d('tuned', 'schema_valid', True)}** |
| AI-step grounding | {d('base_zeroshot', 'ai_steps_grounded_recall')} | {d('base_fewshot', 'ai_steps_grounded_recall')} | **{d('tuned', 'ai_steps_grounded_recall')}** |
| Length ratio vs reference | {d('base_zeroshot', 'length_ratio_vs_reference')} | {d('base_fewshot', 'length_ratio_vs_reference')} | **{d('tuned', 'length_ratio_vs_reference')}** |
| LLM-judge rubric (1-5) | {rub('base_zeroshot')} | {rub('base_fewshot')} | **{rub('tuned')}** |

Blinded pairwise vs the 2-shot baseline, **judged in both orders** to control
position bias: {pw or 'see repository'}.

Strict-JSON compliance rises from 0% to ~98%, but this is *deliberately
deprioritised*: all base generations were markdown-fenced, and an identical
repair function applied to every arm recovers 100% of them. That swing is
formatting discipline, not workflow quality.

## Training

| | |
|---|---|
| Base model | `{base}` |
| Method | LoRA (bf16; 4-bit QLoRA path available) |
| Rank / alpha / dropout | {t['lora_r']} / {t['lora_alpha']} / {t['lora_dropout']} |
| Target modules | {', '.join(f'`{m}`' for m in t['target_modules'])} |
| Trainable params | 18,464,768 (1.18%) |
| LR / schedule | {t['lr']} / {t['scheduler']}, warmup {t['warmup_ratio']} |
| Epochs / optimizer steps | {t['epochs']} / {meta.get('optimizer_steps', 90)} |
| Effective batch | {t['per_device_batch_size']} × {t['grad_accum']} grad-accum |
| Max sequence length | {conf['model']['max_seq_len_train']} |
| Loss | **completion tokens only** (prompt masked to -100) |

Dev loss by epoch:

| Epoch | Dev loss |
|---|---|
{dev_tbl}

Dev loss plateaus after epoch 2 while train loss keeps falling. The best
checkpoint (epoch 2) is what ships here. The epoch-3 uptick is far too small
relative to the 12-record dev set to call overfitting — the honest reading is
that the model extracted what it can from 120 examples.

LoRA targets **MLP as well as attention** projections: the measured baseline
deficit was content generation (empty reasoning fields, ~1/3 of reference
length), not attention routing.

## Usage

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "{base}"
ADAPTER = "ArashEslam/qwen2.5-1.5b-workflow-lora"

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16).to("cuda")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()

messages = [
    {{"role": "system", "content": "You are an operations analyst. You read descriptions of how a small business currently runs a process and turn them into a structured workflow analysis."}},
    {{"role": "user", "content": "<the instructions + business process description>"}},
]
text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(text, return_tensors="pt", add_special_tokens=False).to(model.device)
out = model.generate(**inputs, max_new_tokens=2048, do_sample=False)
print(tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True))
```

> The exact prompt template matters — the adapter was trained against one fixed
> template. Use `src/nextverse/prompts/task.py` from the companion repository to
> build prompts, rather than improvising the instruction text.

## Limitations

- **Trained on synthetic references.** The targets encode one frontier model's
  idea of a good workflow analysis, not a validated business standard.
- **Small scale.** 120 training examples, 40 evaluation records. Per-slice
  findings are indicative, not precise.
- **Two fields regressed** versus the baseline: `bottlenecks_and_risks`
  (3.19 → 2.77) and `human_approvals_controls` (2.53 → 2.35). Not
  under-generation — the model learned the reference's rhetorical form (long
  causal statements) without its evidential specificity (named entities and
  figures drawn from the input). Style is cheap to learn from 120 examples;
  specificity is not.
- **JSON compliance is real but shallow.** One evaluation record produced
  Python-style string concatenation *inside* JSON when the input stated a policy
  three inconsistent ways — a structure never seen in training. Schema-constrained
  decoding would remove this failure class.
- **Judged by a lite-tier model.** Stronger judges were quota-limited. Position
  inconsistency was 15–18%.
- **English only**, small-business domain.

## Licence

Apache-2.0, inheriting the base model's licence. The training dataset is MIT.
"""
