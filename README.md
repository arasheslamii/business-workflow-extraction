# Business Process → Structured Workflow Analysis

Post-training a small open-weight model to turn free-text descriptions of how a
small business runs a process into a strict 10-field structured workflow
analysis.

The experiment is fully scripted, seeded and reproducible. Everything below has
actually been run end to end.

---

## What this is

**Task.** Input: a description of how a small business currently handles a
process (an owner's rambling email, consultant call notes, a formal process
doc, a chat transcript). Output: a JSON object with exactly 10 fields —
`objective`, `trigger`, `owner_and_participants`, `inputs_data_required`,
`systems_involved`, `current_process`, `bottlenecks_and_risks`,
`recommended_improved_process`, `ai_agent_steps`, `human_approvals_controls`.

**Model.** `Qwen/Qwen2.5-1.5B-Instruct` + LoRA (r=16), bf16.

**Headline result.** Against the *competitive* 2-shot baseline (not the easy
zero-shot one), the tuned model improves schema validity 80% → 98%, AI-step
grounding 0.33 → 0.42, and output length ratio 0.70 → 0.84 of reference. See
`results/report.md` for the full three-layer evaluation and `SUMMARY.md` for
what it means and what it does not.

---

## Repository layout

```
config.yaml                 Single source of truth: seeds, paths, model, hyperparameters
data/raw/                   Delivered dataset (train 120 / dev 12 / eval 28 synthetic + 12 PET)
src/nextverse/
  schema.py                 The 10-field contract; types derived from the data
  seeding.py                Global seed control
  config.py                 Config loader that raises on missing keys
  llm_api.py                Cached, paced, retrying Gemini client for the judge
  prompts/task.py           THE task prompt - one definition shared by train and eval
  prompts/judge.py          Rubric + pairwise judge prompts
  data/loading.py           Split loading + deterministic few-shot selection
  modeling/loader.py        Model/tokenizer loading (bf16 or 4-bit)
  modeling/collator.py      Completion-only masking (the highest-risk code here)
  eval/parsing.py           ONE JSON repair function, applied identically to every arm
  eval/text.py              content_recall / ngram_jaccard primitives
  eval/structural.py        Layer 1 metrics
  eval/heuristics.py        Layer 2 metrics + their definitions
  eval/judge.py             Layer 3: both-orders pairwise, bootstrap CI
  eval/axes.py              The three analysis slice axes
scripts/                    Numbered entrypoints, run in order
slurm/run_gpu.sh            Single environment definition for srun AND sbatch
tests/                      28 tests; the masking tests are the important ones
results/                    All outputs: raw generations, metrics, report, failures
```

---

## Reproducing

### 0. Prep — **login node** (needs internet)

```bash
cd /home/s2806882/projects/nextVerse
bash scripts/00_prep_env.sh          # add --flexible if a pin will not resolve
```

Creates `.venv`, installs pinned dependencies, downloads model weights into a
project-local `.hf_cache`, writes `requirements.lock.txt`, and verifies the
sequence-length budget with the real tokenizer. Must end in `RESULT: PASS`.

### 1. Verify the data — login node, CPU

```bash
source .venv/bin/activate
python scripts/02_verify_data.py     # independent QC, pure stdlib
python -m pytest tests/ -q           # 28 tests
```

### 2. Baselines — **GPU node**

Two arms, run as parallel jobs (`saxa` has 35 free MIG slices):

```bash
sbatch slurm/run_gpu.sh python scripts/03_run_base.py --arm zeroshot
sbatch slurm/run_gpu.sh python scripts/03_run_base.py --arm fewshot
```

Smoke test first (~2 min) before committing an hour:

```bash
srun -p Teaching -w saxa --gres=gpu:h200_1g.18gb:1 --mem=64G --cpus-per-task=4 \
     --time=00:20:00 --pty bash slurm/run_gpu.sh \
     python scripts/03_run_base.py --arm zeroshot --limit 2 --out /tmp/smoke
```

> **`--gres=gpu:h200_1g.18gb:1`, not `--gres gpu:1`.** `saxa` has three GRES
> types configured (`h200`, `h200_3g.71gb`, `h200_1g.18gb`); a bare count does
> not pin one, so the slice you get — and your VRAM ceiling — is not
> reproducible.

### 3. Train — GPU node

```bash
sbatch slurm/run_gpu.sh python scripts/04_train.py
```

Verify masking and step counts on CPU first: `python scripts/04_train.py --dry-run`.

### 4. Tuned inference — GPU node

```bash
sbatch slurm/run_gpu.sh python scripts/03_run_base.py --arm tuned --adapter results/adapter
```

### 5. Evaluation — login node

```bash
python scripts/06_eval_deterministic.py            # layers 1+2, no API, seconds
python scripts/07_eval_judge.py --dry-run          # shows call count, spends nothing
python scripts/07_eval_judge.py --list-models      # confirm judge.model exists
python scripts/07_eval_judge.py --rubric --pairwise
python scripts/08_report.py                        # -> results/report.md
python scripts/09_failure_analysis.py              # -> results/failures.md
```

Requires `GEMINI_API_KEY` in the environment for the judge steps only. Every
judge response is cached to `results/judge_cache/`, so re-runs are free and
identical; deleting that directory forces a fresh (and billable) run.

---

## Design decisions

Each of these was a real choice with a real alternative.

**`Qwen2.5-1.5B-Instruct`.** Fits an 18 GB MIG slice with room for 2560-token
training sequences; ungated (no licence friction); already competent at JSON,
so the experiment measures content learning rather than syntax learning.

**bf16 LoRA, not QLoRA 4-bit.** The brief assumed QLoRA. At 1.5B, bf16 weights
are ~3.1 GB against an 18 GB budget — *4-bit was measured to be unnecessary at
this scale*, and it would have added a bitsandbytes-vs-CUDA-13.2 dependency
risk for no memory benefit. 4-bit remains a tested path behind
`model.load_in_4bit`.

**Three arms, not two.** A zero-shot 1.5B fails mostly on JSON *formatting*, so
a two-arm before/after would report a formatting win as though it were a
reasoning win. The 2-shot arm (exemplars drawn from train only, chosen
deterministically) closes most of the formatting gap and is the honest
comparison. Measured: **every one of the 80 base generations was
markdown-fenced** — a "valid JSON rate" headline would have shown 0% → 98%,
which is true and nearly meaningless.

**One JSON repair function for all arms.** `eval/parsing.py` is applied
identically everywhere; `strict` (bare JSON) and `lenient` (after repair) are
both always reported. Applying repair selectively would manufacture the result.
It uses a brace-balancing scanner rather than a regex, because the schema
contains a nested object and a regex stops at the first `}`.

**Completion-only loss.** Prompt tokens are masked to `-100`; only the assistant
JSON carries loss. This is the highest-risk code in the project — a masking bug
produces a healthy-looking run that optimises the wrong objective, with no
symptom in any log — so `tests/test_collator.py` asserts that the *unmasked
span decodes to exactly the target*, not merely that something is masked.

**Sequence length set by measurement, not assumption.** `max_seq_len_train:
2560` against a measured maximum of 1857 tokens.
`scripts/01_check_lengths.py` re-verifies with the real tokenizer and exits
non-zero if anything would truncate; `encode_example` raises rather than
truncating, because truncation removes the *tail* of the JSON target.

**`grad_accum: 4`, not 8.** At n=120 the binding constraint is optimizer steps,
not batch size: accum 8 gives 45 steps total, too few for a cosine schedule to
do anything. Accum 4 gives 90.

**LoRA on MLP as well as attention.** The measured baseline deficit was content
generation (empty reasoning fields, ~1/3 of reference length), not attention
routing. Attention-only would have targeted the wrong failure.

**Cross-family judge.** Reference answers were authored by Claude Opus 5; the
judge is Gemini. Different families, so the most direct form of self-preference
is removed — though not the general circularity of grading LLM-authored data
with an LLM. That is why the judge-independent deterministic layer carries
equal weight in the report.

**Pairwise judged in BOTH orders.** Every pair is scored twice with the
positions swapped. Where the two orders disagree the verdict was driven by
position rather than content: those are counted as **ties**, and the
inconsistency rate is reported as a headline number — it is the honest measure
of how much to trust the judge layer.

**Grounding metrics are field-scoped.** A system named in `current_process`
that is absent from the input is a hallucination; the same system in
`recommended_improved_process` is a *recommendation* and is correct behaviour.
A naive "output systems not in input" check conflates these and would score the
best outputs worst. Novel systems in the recommendation are counted and
reported as information, never as error.

**Every metric ships with its definition** in `results/report.md`. Our own QC
produced 0.23, 0.51 and 0.83 for "the same" grounding metric under three
definitions — a bare number is not a result.

---

## Known rough edges

- **`results/adapter/` contains a `checkpoint-60/` subdirectory.** Harmless for
  loading (the top-level adapter is the artifact, and it is bit-identical to
  the best checkpoint), but the directory is not a clean single artifact.
  Delete `results/adapter/checkpoint-60/` if you want one.
- **Determinism is best-effort.** Seeds are set globally and eval uses greedy
  decoding at batch size 1, but greedy decoding on GPU is not bitwise
  reproducible across kernel or driver changes.
- **The judge is not deterministic even at temperature 0.** It is a thinking
  model (~1300–1900 thinking tokens per rubric call), and the same prompt was
  measured returning different field scores across calls. The disk cache — not
  temperature — is what makes the reported numbers reproducible.
- **Free-tier judge quota is the real constraint.** `gemini-3.6-flash` and
  `gemini-3.5-flash` are both capped at **20 requests/day**; `gemini-2.5-flash`
  and `gemini-2.5-flash-lite` return 404. The run uses
  `gemini-3.5-flash-lite`, the only reachable model with adequate daily quota.
  The judge model actually used is recorded in `results/report.md`.
