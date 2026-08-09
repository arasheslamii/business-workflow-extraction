# Business Workflow Extraction Dataset

172 records. Generated 2026-08-07. All figures recomputed from the JSONL files.

## 1. Purpose and task

Train an small LLM that convert a free-text description of how a small business currently runs a process, like receiving a rambling owner email, a process document, consultant notes, a chat transcript, into a strict 10-field structured workflow analysis. Output is a JSON object with exactly these keys, all required:

| # | Field | Definition |
|---|---|---|
| 1 | `objective` | What the workflow is for (string) |
| 2 | `trigger` | The event that initiates it (string) |
| 3 | `owner_and_participants` | `{owner: string, participants: [string]}` |
| 4 | `inputs_data_required` | Data and documents the process consumes |
| 5 | `systems_involved` | Systems named or clearly implied in the input; empty if none |
| 6 | `current_process` | Ordered steps as described |
| 7 | `bottlenecks_and_risks` | Failure modes tied to the specific process described |
| 8 | `recommended_improved_process` | Ordered target-state steps; may introduce new tools |
| 9 | `ai_agent_steps` | Which steps of field 8 an AI agent could perform |
| 10 | `human_approvals_controls` | Approvals and controls the improved process must retain |

## 2. Record schema

One JSON object per line:

| Key | Purpose |
|---|---|
| `id` | e.g. `train_001`, `eval_syn_013`, `eval_pet_004` |
| `source` | `synthetic` (160) or `pet_real` (12) |
| `split` | `train` / `dev` / `eval_synthetic` / `eval_pet` |
| `vertical` | Business type — for slicing eval by domain |
| `process` | Process family — for slicing eval by process type |
| `style` | Input register (4 values) — for detecting format-sensitivity |
| `difficulty` | `standard` / `vague` / `contradictory` — the intended failure mode |
| `ood_vertical` | `true` for the reserved eval-only verticals (scope limit in §7) |
| `input` | The free-text description |
| `gold` | The 10-field object |
| `reference_type` | `authored_gold` (synthetic) or `model_generated_unverified` (PET) |
| `pet_document_id` | PET source document, on `eval_pet` records only |

## 3. Generation method

All content was written by a frontier LLM (Claude Opus 5) in three decoupled passes.

**Pass 1 — scenario grid** (`scenarios.json`). A 12×12 grid of in-domain verticals × processes. The `(v_i, p_i)` diagonal is held out of train/dev and used for eval, so every (vertical, process) pair appears exactly once in train/dev (132 pairs) with zero overlap against eval (28 pairs). Three verticals — vet clinic, law firm, car repair garage — are reserved as eval-only. Each of the 160 stubs carries a distinct quirk plus an assigned style and difficulty.

**Pass 2 — inputs only**, written from the stubs with no gold outputs in context.

**Pass 3 — golds only**, written afterwards, reading each input as if authored by a third party. The passes were decoupled so the gold reflects what the input actually says rather than what its author intended: a single-pass generator tends to encode facts into the gold that never reached the input, producing golds unattainable from the input alone.

**Grounding rules.** Fields 1–7 are grounded strictly in the input; where information is absent the gold records `"Not specified in input"` or an empty array, and never invents. Fields 8–10 are advisory, may introduce systems not in the input, but must stay consistent with it. Where an input is self-contradictory, `bottlenecks_and_risks` names the contradiction rather than resolving it silently.

Result: `owner` is `"Not specified in input"` on 57/172 records (33%); `systems_involved` is empty on 19/172 (11%).

## 4. Composition and distribution

| Split | n | Median words | Min | Max |
|---|---|---|---|---|
| train | 120 | 272 | 178 | 341 |
| dev | 12 | 217 | 161 | 248 |
| eval_synthetic | 28 | 233 | 174 | 281 |
| eval_pet | 12 | 225 | 148 | 696 |

All 160 synthetic inputs fall inside the 80–350 word target; 4 PET inputs exceed it (real documents, deliberately preferring longer ones).

**Verticals.** 27 distinct. Train and dev share the same 12 in-domain verticals (10 each in train, 1 each in dev). `eval_synthetic` holds those 12 at 1 each plus the reserved three — vet clinic 6, law firm 5, car repair garage 5 (16 OOD records). PET contributes 12 further verticals, one record each.

**Processes** (synthetic, 12 families): train 10 each, dev 1 each, eval_synthetic 2–3 each (invoicing/billing, customer support, compliance/reporting, quote generation have 3; the rest 2).

| Style | train | dev | eval_syn | eval_pet |
|---|---|---|---|---|
| chat_transcript | 32 | 2 | 6 | 0 |
| consultant_call_notes | 31 | 3 | 6 | 0 |
| formal_process_doc | 30 | 2 | 8 | 12 |
| rambling_owner_email | 27 | 5 | 8 | 0 |

| Difficulty | train | dev | eval_syn | eval_pet |
|---|---|---|---|---|
| standard | 75 | 6 | 10 | 10 |
| vague | 30 | 2 | 11 | 2 |
| contradictory | 15 | 4 | 7 | 0 |

`eval_synthetic` is deliberately biased toward hard cases: 18 of 28 are vague or contradictory, against 45 of 120 in train.

## 5. The PET slice

PET (Process Extraction from Text) is a corpus of 45 human-written business process descriptions with process-element annotations.

- Source `huggingface.co/datasets/patriziobellan/PET` · citation arXiv:2203.04860 · **licence MIT** (permissive; use and redistribution with attribution).
- Only the raw narrative token text was used; all annotations (`ner_tags`, `relations`, `sentence-IDs`, `tokens-IDs`) discarded. The dataset's loader script points at a dead host, so the parquet was read directly from the hub.
- 12 documents across 8 of the 10 PET families: `doc-1.3, doc-1.4, doc-2.1, doc-2.2, doc-3.5, doc-4.1, doc-5.3, doc-5.4, doc-6.1, doc-6.4, doc-9.1, doc-10.2`.

**Warning:** every PET gold is model-generated with no human verification. All 12 carry `reference_type: model_generated_unverified`. Treat scores on this slice as indicative only until the references are checked by a person.

## 6. Quality control

`qc.py` runs all checks and hard-fails on any violation.

| Check | Method | Result |
|---|---|---|
| Schema | Pydantic model of all 10 fields, `extra="forbid"`, non-empty strings, no blank list items | 172/172 pass |
| Cross-field consistency | id uniqueness; `source`/`split`/`reference_type` coherence; `ood_vertical` matches reserved list; required fields non-empty; every `contradictory` record names the contradiction in `bottlenecks_and_risks` or `owner`; `ai_agent_steps` ≤ `recommended_improved_process` steps | 0 problems |
| Near-duplicates | TF-IDF char\_wb 3–5-gram cosine over all 172 inputs, threshold 0.75 | 0 pairs over; **max observed 0.4795** (`train_078`/`train_118`); 172 unique input texts |
| Leakage | Zero (vertical, process) overlap train/dev vs eval; reserved verticals absent from train/dev; no id or exact-text overlap | 0 problems |
| Placeholder scan | Regex for lorem/TODO/TBD/placeholder/"example business" over every serialised record | 0 hits |
| Human review | `review_sample.md`: 15 stratified examples (5 train, 5 eval_synthetic incl. 1 OOD, 5 PET), weighted-greedy selected to cover all difficulties and spread verticals and processes | Reviewed; no regeneration required |

## 7. Known weaknesses

1. **Single-generator bias.** One model wrote every input and every gold. Lexical habits and the taxonomy of bottlenecks it reaches for are correlated corpus-wide in ways the duplicate check cannot catch.
2. **Inputs are too clean.** Even the rambling ones are coherent and on-topic. Real documents contain interleaved topics, half-finished sentences, contradictory dates, OCR noise and irrelevant material.
3. **Small n.** 120 training records over 144 grid cells is roughly one example per cell — thin for learning process-specific patterns.
4. **Golds encode one model's taste.** Fields 8–10 are design judgements, not verifiable facts, and no domain expert has confirmed any of them.
5. **Contradiction placement is skewed.** Of 26 `contradictory` records, only 8 state the contradiction inside a single document (`formal_process_doc`); the other 18 present it as two speakers or two accounts disagreeing, a much easier signal. (An earlier estimate of 3 was wrong; the recomputed figure is 8.)
6. **PET references unverified** — see §5.
7. **`ood_vertical` is scoped to the synthetic taxonomy.** It flags only the three reserved verticals, so all 12 PET records carry `false` despite every PET vertical being unseen in training. Use `source == "pet_real"` alongside it to measure out-of-domain generalisation.
8. **Style/split confounding.** `eval_pet` is 100% `formal_process_doc`, so PET results conflate domain shift with register shift.

## 8. Improving this with real data

- **Real inputs.** Replace synthetic inputs with real customer emails, documents and call transcripts, with permission and after PII removal — addresses weaknesses 1, 2 and 8 directly.
- **Expert golds on a subset.** Have a process consultant author or correct 30–50 golds, then measure the distance from the LLM-authored ones. That quantifies weakness 4 rather than noting it.
- **Inter-annotator agreement.** Two independent annotators on a shared subset, reported per field. Expect low agreement on fields 8–10; that figure is the useful result, since it bounds achievable eval precision.
- **Targeted collection against observed failures.** After evaluating a trained model, collect specifically against the failing cells — likely contradiction-inside-one-document and inputs whose correct answer is `"Not specified in input"`.
- **Production feedback loop.** Capture cases where a deployed model's output was edited by a user and feed the corrections back. This is the only source reflecting the true input distribution.

## 9. Reproducing

Files, repo-relative to `output/`:

| File | Contents |
|---|---|
| `train.jsonl`, `dev.jsonl`, `eval_synthetic.jsonl`, `eval_pet.jsonl` | The records |
| `scenarios.json` | 172 scenario stubs and the grid design |
| `data_manifest.json` | Counts, distributions, PET IDs and licence, all QC results |
| `review_sample.md` | The 15-example stratified review set |
| `qc.py` | All checks in §6; writes the manifest and review sample; exits non-zero on hard failure |

Run `python3 qc.py` from `output/`. Requires `pydantic` and `scikit-learn`.

The grid, split assignment and QC are deterministic and reproduce exactly. The input and gold **text** will not: it is LLM-authored, so re-running generation yields different wording. The JSONL files are the artifact of record.
