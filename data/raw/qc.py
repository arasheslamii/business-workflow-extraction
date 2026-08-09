"""Quality control for the business-workflow extraction dataset.

Run:  python3 qc.py            (from the output/ directory)

Performs:
  1. Pydantic schema validation of every record. Hard fail on any violation.
  2. Near-duplicate detection across all inputs (TF-IDF char n-gram cosine, >0.75).
  3. Completeness stats: empty-field rates, length distributions, distribution tables.
  4. Leakage checks: zero scenario overlap between train/dev and any eval file;
     reserved verticals absent from train/dev.
  5. Writes data_manifest.json and review_sample.md.

Exits non-zero if any hard check fails.
"""

from __future__ import annotations

import collections
import datetime
import json
import os
import re
import sys
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))

SPLITS = {
    "train": "train.jsonl",
    "dev": "dev.jsonl",
    "eval_synthetic": "eval_synthetic.jsonl",
    "eval_pet": "eval_pet.jsonl",
}

RESERVED_VERTICALS = {"vet clinic", "law firm", "car repair garage"}
NOT_SPECIFIED = "Not specified in input"
DUP_THRESHOLD = 0.75
PLACEHOLDERS = re.compile(
    r"\b(lorem ipsum|lorem|TODO|TBD|FIXME|example business|placeholder|XXX|foo bar)\b",
    re.IGNORECASE,
)
# scenarios.json legitimately uses TBD markers for PET slots before extraction
PET_TBD = re.compile(r"TBD_from_pet_document")


# --------------------------------------------------------------------------
# 1. Schema
# --------------------------------------------------------------------------
class OwnerParticipants(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner: str = Field(min_length=1)
    participants: List[str]

    @field_validator("participants")
    @classmethod
    def no_blank_participants(cls, v):
        if any(not s.strip() for s in v):
            raise ValueError("blank participant string")
        return v


class Gold(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective: str = Field(min_length=1)
    trigger: str = Field(min_length=1)
    owner_and_participants: OwnerParticipants
    inputs_data_required: List[str]
    systems_involved: List[str]
    current_process: List[str]
    bottlenecks_and_risks: List[str]
    recommended_improved_process: List[str]
    ai_agent_steps: List[str]
    human_approvals_controls: List[str]

    @field_validator("inputs_data_required", "systems_involved", "current_process",
                     "bottlenecks_and_risks", "recommended_improved_process",
                     "ai_agent_steps", "human_approvals_controls")
    @classmethod
    def no_blank_items(cls, v):
        if any(not s.strip() for s in v):
            raise ValueError("blank list item")
        return v


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source: Literal["synthetic", "pet_real"]
    split: Literal["train", "dev", "eval_synthetic", "eval_pet"]
    vertical: str
    process: str
    style: str
    difficulty: Literal["standard", "vague", "contradictory"]
    ood_vertical: bool
    input: str = Field(min_length=1)
    gold: Gold
    reference_type: Literal["authored_gold", "model_generated_unverified"]
    pet_document_id: str | None = None


# --------------------------------------------------------------------------
def load_all():
    records, failures = [], []
    for split, fname in SPLITS.items():
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            failures.append(f"missing file: {fname}")
            continue
        for i, line in enumerate(open(path), 1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            try:
                rec = Record.model_validate(raw)
            except ValidationError as e:
                failures.append(f"{fname}:{i} id={raw.get('id')} {e.errors()[:2]}")
                continue
            if rec.split != split:
                failures.append(f"{fname}:{i} id={rec.id} split field is {rec.split!r}")
            records.append((rec, raw))
    return records, failures


# --------------------------------------------------------------------------
def check_consistency(records):
    """Cross-field rules that the type system cannot express."""
    problems = []
    ids = collections.Counter(r.id for r, _ in records)
    for rid, n in ids.items():
        if n > 1:
            problems.append(f"duplicate id {rid} appears {n} times")

    for rec, _ in records:
        g = rec.gold
        # placeholder text anywhere in the record
        blob = json.dumps(_[1] if isinstance(_, tuple) else rec.model_dump(),
                          ensure_ascii=False) if False else json.dumps(
            rec.model_dump(), ensure_ascii=False)
        hit = PLACEHOLDERS.search(PET_TBD.sub("", blob))
        if hit:
            problems.append(f"{rec.id}: placeholder text {hit.group(0)!r}")

        # source / split / reference_type coherence
        if rec.source == "pet_real":
            if rec.split != "eval_pet":
                problems.append(f"{rec.id}: pet_real must be in eval_pet")
            if rec.reference_type != "model_generated_unverified":
                problems.append(f"{rec.id}: PET record must be model_generated_unverified")
            if not rec.pet_document_id:
                problems.append(f"{rec.id}: PET record missing pet_document_id")
        else:
            if rec.reference_type != "authored_gold":
                problems.append(f"{rec.id}: synthetic record must be authored_gold")

        # ood flag must agree with the reserved-vertical list
        if (rec.vertical in RESERVED_VERTICALS) != rec.ood_vertical:
            problems.append(
                f"{rec.id}: ood_vertical={rec.ood_vertical} but vertical={rec.vertical!r}")

        # a workflow must describe at least some current process and a recommendation
        if not g.current_process:
            problems.append(f"{rec.id}: current_process is empty")
        if not g.recommended_improved_process:
            problems.append(f"{rec.id}: recommended_improved_process is empty")
        if not g.bottlenecks_and_risks:
            problems.append(f"{rec.id}: bottlenecks_and_risks is empty")
        if not g.ai_agent_steps:
            problems.append(f"{rec.id}: ai_agent_steps is empty")
        if not g.human_approvals_controls:
            problems.append(f"{rec.id}: human_approvals_controls is empty")

        # contradictory examples must name the contradiction somewhere in the gold
        if rec.difficulty == "contradictory":
            text = " ".join(g.bottlenecks_and_risks + [g.owner_and_participants.owner]).lower()
            if not any(w in text for w in
                       ("contradict", "conflict", "inconsisten", "both descriptions",
                        "both accounts", "both statements", "unreconciled", "disagree")):
                problems.append(
                    f"{rec.id}: difficulty=contradictory but no contradiction noted "
                    f"in bottlenecks_and_risks or owner")

        # ai_agent_steps must reference the recommended process, not the current one
        if len(g.ai_agent_steps) > len(g.recommended_improved_process):
            problems.append(
                f"{rec.id}: more ai_agent_steps ({len(g.ai_agent_steps)}) than "
                f"recommended steps ({len(g.recommended_improved_process)})")
    return problems


def ai_grounding_score(rec) -> float:
    """Fraction of ai_agent_steps with meaningful lexical overlap with a
    recommended_improved_process step. Reported, not hard-failed."""
    stop = set("""a an the and or of to in for on with by is are be as at from that this it its
    can could should would will may an any every each all not no than then so if where when who
    which what into onto up down out over under again further more most other some such only own
    same very s t just now agent ai human step steps process""".split())

    def toks(s):
        return {w for w in re.findall(r"[a-z]{4,}", s.lower())} - stop

    rec_tok = [toks(s) for s in rec.gold.recommended_improved_process]
    if not rec_tok:
        return 0.0
    hits = 0
    for a in rec.gold.ai_agent_steps:
        at = toks(a)
        if not at:
            continue
        if max((len(at & r) / max(1, min(len(at), len(r))) for r in rec_tok), default=0) >= 0.25:
            hits += 1
    return hits / max(1, len(rec.gold.ai_agent_steps))


# --------------------------------------------------------------------------
def near_duplicates(records):
    ids = [r.id for r, _ in records]
    texts = [r.input for r, _ in records]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                          min_df=2, sublinear_tf=True)
    X = vec.fit_transform(texts)
    S = cosine_similarity(X)
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if S[i, j] > DUP_THRESHOLD:
                pairs.append((round(float(S[i, j]), 4), ids[i], ids[j]))
    pairs.sort(reverse=True)
    top = sorted(((round(float(S[i, j]), 4), ids[i], ids[j])
                  for i in range(len(ids)) for j in range(i + 1, len(ids))),
                 reverse=True)[:10]
    return pairs, top


def leakage(records):
    problems = []
    traindev = [r for r, _ in records if r.split in ("train", "dev")]
    evals = [r for r, _ in records if r.split in ("eval_synthetic", "eval_pet")]

    td_pairs = {(r.vertical, r.process) for r in traindev}
    ev_pairs = {(r.vertical, r.process) for r in evals if r.source == "synthetic"}
    overlap = td_pairs & ev_pairs
    if overlap:
        problems.append(f"scenario (vertical, process) overlap train/dev vs eval: {sorted(overlap)}")

    bad = sorted({r.vertical for r in traindev} & RESERVED_VERTICALS)
    if bad:
        problems.append(f"reserved eval-only verticals present in train/dev: {bad}")

    td_ids = {r.id for r in traindev}
    ev_ids = {r.id for r in evals}
    if td_ids & ev_ids:
        problems.append(f"id overlap between train/dev and eval: {sorted(td_ids & ev_ids)}")

    # exact input text overlap
    td_txt = {r.input.strip() for r in traindev}
    for r in evals:
        if r.input.strip() in td_txt:
            problems.append(f"{r.id}: eval input text also appears in train/dev")
    return problems, sorted(td_pairs), sorted(ev_pairs)


# --------------------------------------------------------------------------
LIST_FIELDS = ["inputs_data_required", "systems_involved", "current_process",
               "bottlenecks_and_risks", "recommended_improved_process",
               "ai_agent_steps", "human_approvals_controls"]


def stats(records):
    out = {}
    for split in SPLITS:
        rows = [r for r, _ in records if r.split == split]
        if not rows:
            continue
        wl = sorted(len(r.input.split()) for r in rows)
        empty = {f: sum(1 for r in rows if not getattr(r.gold, f)) for f in LIST_FIELDS}
        ns = {
            "objective": sum(1 for r in rows if r.gold.objective == NOT_SPECIFIED),
            "trigger": sum(1 for r in rows if r.gold.trigger == NOT_SPECIFIED),
            "owner": sum(1 for r in rows if r.gold.owner_and_participants.owner == NOT_SPECIFIED),
        }
        out[split] = {
            "n": len(rows),
            "input_words": {
                "min": wl[0], "p25": wl[len(wl) // 4], "median": wl[len(wl) // 2],
                "p75": wl[3 * len(wl) // 4], "max": wl[-1],
                "mean": round(sum(wl) / len(wl), 1),
                "outside_80_350": sum(1 for w in wl if w < 80 or w > 350),
            },
            "empty_list_fields_pct": {
                f: round(100 * c / len(rows), 1) for f, c in empty.items()},
            "not_specified_counts": ns,
            "avg_items_per_list_field": {
                f: round(sum(len(getattr(r.gold, f)) for r in rows) / len(rows), 1)
                for f in LIST_FIELDS},
            "vertical": dict(sorted(collections.Counter(r.vertical for r in rows).items())),
            "process": dict(sorted(collections.Counter(r.process for r in rows).items())),
            "style": dict(sorted(collections.Counter(r.style for r in rows).items())),
            "difficulty": dict(sorted(collections.Counter(r.difficulty for r in rows).items())),
            "ood_vertical_count": sum(1 for r in rows if r.ood_vertical),
            "mean_ai_step_grounding": round(
                sum(ai_grounding_score(r) for r in rows) / len(rows), 3),
        }
    return out


# --------------------------------------------------------------------------
def review_sample(records, path):
    by_id = {r.id: r for r, _ in records}

    def pick(split, n, prefer=None, prefer_ood=False):
        """Weighted greedy: cover the wanted difficulties first, then spread across
        processes and verticals, so a reviewer never sees five of the same process.
        Always fills to n where enough rows exist."""
        rows = [r for r, _ in records if r.split == split]
        prefer = set(prefer or [])
        chosen, seen = [], set()
        used_proc, used_vert, used_diff = set(), set(), set()

        while len(chosen) < n and len(seen) < len(rows):
            best, best_score = None, None
            for r in rows:
                if r.id in seen:
                    continue
                score = (
                    4 * (r.difficulty in prefer and r.difficulty not in used_diff)
                    + 3 * (prefer_ood and r.ood_vertical
                           and not any(c.ood_vertical for c in chosen))
                    + 2 * (r.process not in used_proc)
                    + 1 * (r.vertical not in used_vert)
                )
                if best_score is None or score > best_score:
                    best, best_score = r, score
            chosen.append(best); seen.add(best.id)
            used_proc.add(best.process)
            used_vert.add(best.vertical)
            used_diff.add(best.difficulty)
        return chosen

    sel = (pick("train", 5, ["standard", "vague", "contradictory"])
           + pick("eval_synthetic", 5, ["vague", "contradictory", "standard"],
                  prefer_ood=True)
           + pick("eval_pet", 5))

    L = ["# Review sample", "",
         f"Generated {datetime.date.today().isoformat()}. "
         f"{len(sel)} stratified examples: 5 train, 5 synthetic eval (hard cases first), "
         f"5 PET real-text.", ""]
    for r in sel:
        L += [f"## `{r.id}` — {r.vertical} / {r.process}", "",
              f"- **split**: {r.split} · **style**: {r.style} · "
              f"**difficulty**: {r.difficulty} · **ood**: {r.ood_vertical} · "
              f"**reference**: {r.reference_type}"
              + (f" · **PET doc**: {r.pet_document_id}" if r.pet_document_id else ""), "",
              "### Input", "", "```text", r.input.strip(), "```", "",
              "### Gold", "", "```json",
              json.dumps(r.gold.model_dump(), indent=2, ensure_ascii=False), "```", "", "---", ""]
    open(path, "w").write("\n".join(L))
    return [r.id for r in sel]


# --------------------------------------------------------------------------
def main():
    records, failures = load_all()
    print(f"loaded {len(records)} records")

    hard = list(failures)
    hard += check_consistency(records)

    dup_pairs, top_pairs = near_duplicates(records)
    leak_problems, td_pairs, ev_pairs = leakage(records)
    hard += leak_problems

    st = stats(records)

    pet_docs = sorted({r.pet_document_id for r, _ in records
                       if r.pet_document_id})

    manifest = {
        "dataset": "business-workflow-extraction",
        "generation_date": datetime.date.today().isoformat(),
        "generator": "Claude Opus 5 (synthetic authoring); PET slice is real human-written text",
        "task": "free-text description of a small-business process -> 10-field structured JSON",
        "record_counts": {s: st.get(s, {}).get("n", 0) for s in SPLITS},
        "total_records": len(records),
        "splits": st,
        "grid_design": {
            "in_domain_verticals": 12,
            "processes": 12,
            "note": ("12x12 grid; the (v_i, p_i) diagonal is held out of train/dev and used "
                     "for eval_synthetic, so every (vertical, process) pair appears exactly "
                     "once in train/dev. 3 reserved verticals are eval-only."),
            "reserved_eval_only_verticals": sorted(RESERVED_VERTICALS),
            "train_dev_vertical_process_pairs": len(td_pairs),
            "eval_synthetic_vertical_process_pairs": len(ev_pairs),
        },
        "pet_slice": {
            "source": "https://huggingface.co/datasets/patriziobellan/PET",
            "paper": "arXiv:2203.04860",
            "license": "MIT",
            "license_note": ("MIT is permissive and allows use, modification and "
                             "redistribution with attribution; suitable for building an "
                             "evaluation slice. Only the raw narrative token text was used; "
                             "all PET annotations (ner_tags, relations, sentence-IDs, "
                             "tokens-IDs) were discarded."),
            "documents_used": pet_docs,
            "n_documents": len(pet_docs),
            "reference_type": "model_generated_unverified",
            "reference_caveat": ("Gold outputs for the PET slice were generated by the model "
                                 "under the same grounding rules and have not been verified "
                                 "by a human annotator."),
        },
        "qc": {
            "schema_validation": "pass" if not failures else "FAIL",
            "schema_failures": failures,
            "consistency_problems": check_consistency(records),
            "near_duplicate_threshold": DUP_THRESHOLD,
            "near_duplicate_pairs_over_threshold": dup_pairs,
            "n_near_duplicate_pairs": len(dup_pairs),
            "highest_similarity_pairs": top_pairs,
            "leakage_problems": leak_problems,
            "leakage_checks": {
                "train_dev_vs_eval_scenario_overlap": 0 if not any(
                    "overlap" in p for p in leak_problems) else "FAIL",
                "reserved_verticals_absent_from_train_dev": not any(
                    "reserved" in p for p in leak_problems),
            },
        },
    }

    with open(os.path.join(HERE, "data_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    sample_ids = review_sample(records, os.path.join(HERE, "review_sample.md"))

    # ------------------------------------------------------------------ report
    print("\n=== SCHEMA ===")
    print(f"  validation: {'PASS' if not failures else 'FAIL'} ({len(failures)} failures)")
    for f in failures[:10]:
        print("   ", f)

    cons = check_consistency(records)
    print(f"\n=== CONSISTENCY === {len(cons)} problems")
    for p in cons[:15]:
        print("   ", p)

    print(f"\n=== NEAR-DUPLICATES (char 3-5gram cosine > {DUP_THRESHOLD}) ===")
    print(f"  pairs over threshold: {len(dup_pairs)}")
    for s, a, b in dup_pairs[:10]:
        print(f"    {s}  {a}  {b}")
    print("  highest similarities observed:")
    for s, a, b in top_pairs[:5]:
        print(f"    {s}  {a}  {b}")

    print(f"\n=== LEAKAGE === {len(leak_problems)} problems")
    for p in leak_problems:
        print("   ", p)
    if not leak_problems:
        print("    zero (vertical, process) overlap train/dev vs eval_synthetic")
        print("    reserved verticals absent from train/dev")

    print("\n=== SPLITS ===")
    for split, s in st.items():
        w = s["input_words"]
        print(f"  {split:15s} n={s['n']:3d}  words min/med/max="
              f"{w['min']}/{w['median']}/{w['max']}  outside 80-350: {w['outside_80_350']}")
        print(f"                  difficulty={s['difficulty']}")
        print(f"                  empty list fields %: "
              f"{ {k: v for k, v in s['empty_list_fields_pct'].items() if v} or 'none'}")
        print(f"                  'Not specified' counts: {s['not_specified_counts']}"
              f"  ai-step grounding={s['mean_ai_step_grounding']}")

    print(f"\nwrote data_manifest.json and review_sample.md ({len(sample_ids)} examples)")

    if hard:
        print(f"\nHARD FAIL: {len(hard)} problems")
        sys.exit(1)
    print("\nALL HARD CHECKS PASSED")


if __name__ == "__main__":
    main()
