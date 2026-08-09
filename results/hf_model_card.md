---
license: apache-2.0
base_model: Qwen/Qwen2.5-1.5B-Instruct
library_name: peft
pipeline_tag: text2text-generation
tags:
- lora
- peft
- business-process
- structured-extraction
- json
datasets:
- ArashEslam/business-workflow-extraction
language:
- en
---

# Qwen2.5-1.5B-Instruct — Workflow Analysis LoRA

A LoRA adapter that makes `Qwen/Qwen2.5-1.5B-Instruct` reliably convert free-text descriptions of
small-business processes into a strict 10-field structured workflow analysis.

Trained on [ArashEslam/business-workflow-extraction](https://huggingface.co/datasets/ArashEslam/business-workflow-extraction).

## Results

Evaluated on 40 held-out records (28 synthetic + 12 **real** human-written).
The meaningful comparison is against a **2-shot baseline**, not zero-shot: a
zero-shot 1.5B fails mostly on JSON *formatting*, so a naive before/after would
report a formatting win as a reasoning win.

| Metric | Base (0-shot) | Base (2-shot) | **This adapter** |
|---|---|---|---|
| Schema-valid rate | 70% | 80% | **98%** |
| AI-step grounding | 0.230 | 0.326 | **0.420** |
| Length ratio vs reference | 0.389 | 0.702 | **0.838** |
| LLM-judge rubric (1-5) | 3.04 | 3.23 | **3.41** |

Blinded pairwise vs the 2-shot baseline, **judged in both orders** to control
position bias: **30 wins / 7 ties / 3 losses** (91% excluding ties), margin 95% CI [+0.47, +0.85], position inconsistency 18%.

Strict-JSON compliance rises from 0% to ~98%, but this is *deliberately
deprioritised*: all base generations were markdown-fenced, and an identical
repair function applied to every arm recovers 100% of them. That swing is
formatting discipline, not workflow quality.

## Training

| | |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Method | LoRA (bf16; 4-bit QLoRA path available) |
| Rank / alpha / dropout | 16 / 32 / 0.05 |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Trainable params | 18,464,768 (1.18%) |
| LR / schedule | 0.0002 / cosine, warmup 0.03 |
| Epochs / optimizer steps | 3 / 90 |
| Effective batch | 1 × 4 grad-accum |
| Max sequence length | 2560 |
| Loss | **completion tokens only** (prompt masked to -100) |

Dev loss by epoch:

| Epoch | Dev loss |
|---|---|
| 1 | 1.1796 |
| 2 | 1.1320 |
| 3 | 1.1375 |

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

BASE = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER = "ArashEslam/qwen2.5-1.5b-workflow-lora"

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16).to("cuda")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()

messages = [
    {"role": "system", "content": "You are an operations analyst. You read descriptions of how a small business currently runs a process and turn them into a structured workflow analysis."},
    {"role": "user", "content": "<the instructions + business process description>"},
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
