# Business Process → Structured Workflow Analysis

Post-training a small open-weight model to turn free-text descriptions of how a
small business runs a process into a strict 10-field structured workflow
analysis.

Fully scripted, seeded and reproducible. Every number below was produced by the
code in this repository.

**Published artifacts**

| | |
|---|---|
| Dataset | [`ArashEslam/business-workflow-extraction`](https://huggingface.co/datasets/ArashEslam/business-workflow-extraction) |
| LoRA adapter | [`ArashEslam/qwen2.5-1.5b-workflow-lora`](https://huggingface.co/ArashEslam/qwen2.5-1.5b-workflow-lora) |
| Results | [`SUMMARY.md`](SUMMARY.md) · [`results/report.md`](results/report.md) · [`results/failures.md`](results/failures.md) |

---

## The task

**Input** — a description of how a small business currently handles a process
(a rambling owner email, consultant call notes, a formal process doc, a chat
transcript).

**Output** — a JSON object with exactly 10 fields: `objective`, `trigger`,
`owner_and_participants`, `inputs_data_required`, `systems_involved`,
`current_process`, `bottlenecks_and_risks`, `recommended_improved_process`,
`ai_agent_steps`, `human_approvals_controls`.

**Model** — `Qwen/Qwen2.5-1.5B-Instruct` + LoRA (r=16), bf16.

**Headline** — against the *competitive 2-shot baseline* (not the easy zero-shot
one), the tuned model wins **30/40 blinded pairwise comparisons** (91% excluding
ties, margin 95% CI [+0.47, +0.85]), lifts schema validity 80% → 98%, AI-step
grounding 0.33 → 0.42, and output length 0.70 → 0.84 of reference.

---

## Requirements

- **Python 3.10+**
- **Any CUDA GPU with ≥8 GB VRAM** for the training and inference steps (bf16
  LoRA on a 1.5B model). Developed and tested on an 18 GB MIG partition of an
  H200; nothing depends on that specific hardware.
- **CPU only** is sufficient for data verification, deterministic evaluation,
  judging, reporting and failure analysis.
- A **Gemini API key** for the LLM-judge layer only (layers 1–2 reproduce fully
  without one).

Determinism is best-effort: seeds are set globally and evaluation uses greedy
decoding at batch size 1, but greedy decoding on GPU is **not bitwise
reproducible** across different hardware, kernel selections or driver versions.
Expect the same conclusions, not identical floating-point values.

---

## Reproducing

All commands run from the repository root. Nothing requires a job scheduler.

### 1. Environment

```bash
cd nextVerse
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-gpu.txt
```

`requirements.lock.txt` records the exact versions the reported results were
produced with. `scripts/00_prep_env.sh` automates the above and additionally
pre-downloads model weights into a project-local `./.hf_cache`, which is useful
when the machine that trains has no internet access.

Scripts set `HF_HOME=./.hf_cache` themselves unless you export your own, so
model weights land beside the repo rather than in your home directory.

### 2. Data

The canonical copy lives **in this repository** at `./data/raw/` — the pipeline
reads it directly and needs no download. The identical data is also published as
a Hugging Face dataset for citation and reuse:

```bash
# Optional - the in-repo copy is what the scripts use
huggingface-cli download ArashEslam/business-workflow-extraction \
    --repo-type dataset --local-dir ./data/hf_download
```

Verify it independently (pure stdlib, no venv required):

```bash
python scripts/02_verify_data.py     # schema, near-duplicates, leakage, OOD flags
python -m pytest tests/ -q           # 28 tests
```

### 3. Baselines — needs a GPU

Two arms. The 2-shot arm is the one that matters: a zero-shot 1.5B fails mostly
on JSON formatting, so comparing only against it would report a formatting win
as a reasoning win.

```bash
python scripts/03_run_base.py --arm zeroshot
python scripts/03_run_base.py --arm fewshot
```

Smoke-test the setup on two records first: append `--limit 2 --out /tmp/smoke`.

### 4. Train — needs a GPU

```bash
python scripts/04_train.py --dry-run   # CPU: verifies masking and step counts
python scripts/04_train.py
```

Writes the adapter to `./results/adapter/`.

### 5. Tuned inference — needs a GPU

```bash
python scripts/03_run_base.py --arm tuned --adapter results/adapter
```

### 6. Evaluation layers 1–2 — CPU, no API key

```bash
python scripts/06_eval_deterministic.py
```

### 7. Evaluation layer 3, LLM judge — CPU, needs `GEMINI_API_KEY`

```bash
export GEMINI_API_KEY=...
python scripts/07_eval_judge.py --list-models   # confirm judge.model is reachable
python scripts/07_eval_judge.py --dry-run       # 280 calls, spends nothing
python scripts/07_eval_judge.py --rubric --pairwise
```

Reported results used **`gemini-3.5-flash-lite`** (set in `config.yaml`). Every
response is cached to `results/judge_cache/`, so re-runs are free, resumable and
identical; deleting that directory forces a fresh billable run. **Without a key,
skip this step** — layers 1–2 and the report still reproduce completely, and the
report marks the judge section as not run.

### 8. Report and failure analysis — CPU, no API key

```bash
python scripts/08_report.py            # -> results/report.md
python scripts/09_failure_analysis.py  # -> results/failures.md
```

### Optional: SLURM

If your environment uses SLURM, `slurm/run_gpu.sh` wraps any of the above in a
job. **Its `#SBATCH` directives — partition name and GRES string — are
site-specific and almost certainly wrong for your cluster**; check
`sinfo -o "%P %N %G"` and edit before use. On nodes exposing several GPU types,
name the exact GRES type rather than a bare count, or the slice you get (and
your VRAM ceiling) will not be reproducible.

```bash
sbatch slurm/run_gpu.sh python scripts/04_train.py
```

The wrapper only sets environment variables and activates the venv; it is a
convenience, not a dependency.

### Optional: publish to Hugging Face

```bash
huggingface-cli login
python scripts/10_publish_hf.py --dataset --model --dry-run   # render cards only
python scripts/10_publish_hf.py --dataset --model
```

---

## Deliverables map

| # | Deliverable | Location |
|---|---|---|
| 1 | Code repository — clean, runnable, seeded, reproducible | `config.yaml`, `src/nextverse/`, `scripts/`, `tests/` (28 passing), `requirements.lock.txt` |
| 2 | Training dataset + generation method, quality controls, weaknesses, real-data plan | `data/raw/train.jsonl` (120) · [HF dataset](https://huggingface.co/datasets/ArashEslam/business-workflow-extraction) · QC in `scripts/02_verify_data.py` · weaknesses & plan in `SUMMARY.md` |
| 3 | Evaluation dataset, strictly separate, no leakage | `data/raw/eval_synthetic.jsonl` (28) + `eval_pet.jsonl` (12 real texts) — verified 0 shared scenarios, max 5-gram Jaccard **0.011** |
| 4 | Before/after evaluation, quantitative + example outputs | `results/report.md` · raw generations in `results/{base_zeroshot,base_fewshot,tuned}/` |
| 5 | Failure analysis incl. cases worse than base | `results/failures.md` (machine-found + written analysis from `analysis_notes.md`) |
| 6 | README — how to reproduce | this file |
| 7 | Max 2-page summary | `SUMMARY.md` |

---

## Repository layout

```
config.yaml                 Single source of truth: seeds, paths, model, hyperparameters
data/raw/                   Dataset: train 120 / dev 12 / eval 28 synthetic + 12 PET
src/nextverse/
  schema.py                 The 10-field contract; types derived from the data
  env.py                    Environment defaults so scripts run standalone
  config.py  seeding.py     Config loader (raises on missing keys); global seeds
  llm_api.py                Cached, paced, retrying Gemini client
  prompts/task.py           THE task prompt - one definition shared by train and eval
  prompts/judge.py          Rubric + pairwise judge prompts
  modeling/collator.py      Completion-only masking (the highest-risk code here)
  eval/parsing.py           ONE JSON repair function, applied identically to every arm
  eval/heuristics.py        Layer 2 metrics + their definitions
  eval/judge.py             Layer 3: both-orders pairwise, bootstrap CI
  eval/axes.py              The three analysis slice axes
  hf_cards.py               Dataset/model cards generated from live results
scripts/                    Numbered entrypoints, run in order
slurm/run_gpu.sh            Optional SLURM convenience wrapper
tests/                      28 tests; the masking tests are the important ones
results/                    Generations, metrics, report, failure analysis
```

---

## Design decisions

Each was a real choice with a real alternative.

**`Qwen2.5-1.5B-Instruct`.** Fits an 8–18 GB VRAM budget with room for
2560-token training sequences; ungated; already competent at JSON, so the
experiment measures content learning rather than syntax learning.

**bf16 LoRA, not 4-bit QLoRA.** At 1.5B, bf16 weights are ~3.1 GB — *4-bit was
measured to be unnecessary at this scale*, and would have added a
bitsandbytes-vs-CUDA dependency risk for no memory benefit. The 4-bit path
remains tested behind `model.load_in_4bit`.

**Three arms, not two.** Measured: **all 80 base generations were
markdown-fenced**. A two-arm comparison would have shown "valid JSON 0% → 98%",
which is true and nearly meaningless. The 2-shot arm (exemplars from train only,
chosen deterministically) closes the formatting gap and is the honest baseline.

**One JSON repair function for all arms.** `eval/parsing.py` is applied
identically everywhere; `strict` and `lenient` rates are both always reported.
It uses a brace-balancing scanner, not a regex — the schema contains a nested
object and a regex stops at the first `}`.

**Completion-only loss.** Prompt tokens masked to `-100`. A masking bug produces
a healthy-looking run that optimises the wrong objective with no symptom in any
log, so `tests/test_collator.py` asserts the *unmasked span decodes to exactly
the target*, not merely that something is masked.

**Sequence length set by measurement.** `max_seq_len_train: 2560` against a
measured maximum of 1857 tokens. `scripts/01_check_lengths.py` re-verifies with
the real tokenizer and exits non-zero if anything would truncate;
`encode_example` raises rather than truncating, because truncation removes the
*tail* of the JSON target.

**`grad_accum: 4`, not 8.** At n=120 the binding constraint is optimizer steps:
accum 8 gives 45 total, too few for a cosine schedule. Accum 4 gives 90.

**LoRA on MLP as well as attention.** The measured baseline deficit was content
generation (empty reasoning fields, ~1/3 of reference length), not attention
routing.

**Cross-family judge.** References were authored by Claude Opus 5; the judge is
Gemini. Different families, so direct self-preference is removed — though not
the general circularity of grading LLM-authored data with an LLM. Hence the
judge-independent deterministic layer carrying equal weight.

**Pairwise judged in both orders.** Every pair is scored twice with positions
swapped. Disagreement means the verdict was driven by position, not content:
those count as **ties**, and the inconsistency rate (15–18%) is reported as the
honest measure of judge reliability.

**Field-scoped grounding.** A system named in `current_process` but absent from
the input is a hallucination; the same system in
`recommended_improved_process` is a *recommendation*. A naive check conflates
them and would score the best outputs worst.

**Every metric ships with its definition** in `results/report.md` — our own QC
produced 0.23, 0.51 and 0.83 for "the same" grounding metric under three
definitions.
