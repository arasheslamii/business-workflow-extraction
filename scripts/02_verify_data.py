#!/usr/bin/env python3
"""Independent verification of the delivered dataset.

Deliberately does NOT import data/raw/qc.py: the point is to re-derive the
claims from the records themselves with separately written checks, so that a
bug in the factory's QC cannot pass through silently.

Pure stdlib so it runs before any virtualenv exists.

Usage:  python3 scripts/02_verify_data.py
Exit 1 if any hard check fails.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.prompts.task import build_messages, target_json  # noqa: E402
from nextverse.schema import FIELDS, LIST_FIELDS, validate  # noqa: E402

RAW = ROOT / "data" / "raw"
SPLITS = ("train", "dev", "eval_synthetic", "eval_pet")

# Near-duplicate threshold agreed with the factory. Word 5-grams: strict enough
# to catch paraphrase-level reuse, loose enough not to fire on shared domain
# vocabulary ("invoice", "customer", "spreadsheet") that all records contain.
NGRAM_N = 5
DUP_THRESHOLD = 0.75

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def ngrams(text: str, n: int = NGRAM_N) -> set[tuple[str, ...]]:
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {tuple(w[i : i + n]) for i in range(max(0, len(w) - n + 1))}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load() -> dict[str, list[dict]]:
    out = {}
    for s in SPLITS:
        p = RAW / f"{s}.jsonl"
        if not p.exists():
            fail(f"missing split file {p}")
            continue
        recs = []
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as e:
                fail(f"{s}.jsonl line {i}: invalid JSON ({e})")
        out[s] = recs
    return out


def main() -> int:
    data = load()
    if failures:
        report(data)
        return 1

    allrecs = [(s, r) for s in SPLITS for r in data.get(s, [])]
    print(f"Loaded {len(allrecs)} records across {len(data)} splits\n")

    # ---- 1. Schema validity of every gold/reference output -------------------
    print("== 1. Schema validity ==")
    bad = 0
    for s, r in allrecs:
        errs = validate(r.get("gold"))
        if errs:
            bad += 1
            fail(f"{r.get('id')}: schema {errs}")
    print(f"  {len(allrecs) - bad}/{len(allrecs)} references schema-valid")

    # ---- 2. Record-level required metadata ----------------------------------
    print("\n== 2. Metadata integrity ==")
    required = {
        "id", "source", "split", "vertical", "process", "style",
        "difficulty", "ood_vertical", "input", "gold", "reference_type",
    }
    ids = Counter()
    for s, r in allrecs:
        missing = required - set(r)
        if missing:
            fail(f"{r.get('id')}: missing metadata {sorted(missing)}")
        ids[r.get("id")] += 1
        if r.get("split") != s:
            fail(f"{r.get('id')}: split field {r.get('split')!r} != file {s}")
    dupe_ids = [i for i, c in ids.items() if c > 1]
    if dupe_ids:
        fail(f"duplicate ids: {dupe_ids}")
    print(f"  unique ids: {len(ids)}; metadata complete: {not failures}")

    # ---- 3. Leakage: no input reused across splits --------------------------
    print("\n== 3. Cross-split leakage ==")
    seen: dict[str, str] = {}
    exact = 0
    for s, r in allrecs:
        key = re.sub(r"\s+", " ", r["input"].strip().lower())
        if key in seen and seen[key] != r["id"]:
            fail(f"identical input text: {seen[key]} and {r['id']}")
            exact += 1
        seen[key] = r["id"]
    print(f"  exact input collisions: {exact}")

    grams = {r["id"]: (s, ngrams(r["input"])) for s, r in allrecs}
    worst = (0.0, None, None)
    cross = 0
    for (i1, (s1, g1)), (i2, (s2, g2)) in combinations(grams.items(), 2):
        j = jaccard(g1, g2)
        if j > worst[0]:
            worst = (j, i1, i2)
        if j >= DUP_THRESHOLD:
            cross += 1
            fail(f"near-duplicate {j:.2f}: {i1} ({s1}) vs {i2} ({s2})")
    print(f"  pairs >= {DUP_THRESHOLD}: {cross}")
    print(f"  max pairwise {NGRAM_N}-gram Jaccard: {worst[0]:.3f} ({worst[1]} vs {worst[2]})")

    # ---- 4. Scenario separation --------------------------------------------
    print("\n== 4. Scenario separation ==")
    scen_path = RAW / "scenarios.json"
    if scen_path.exists():
        scen = json.loads(scen_path.read_text())
        by_split = defaultdict(set)
        entries = scen if isinstance(scen, list) else scen.get("scenarios", [])
        for e in entries:
            if isinstance(e, dict) and "split" in e:
                by_split[e["split"]].add(e.get("scenario_id") or e.get("id"))
        tr = by_split.get("train", set()) | by_split.get("dev", set())
        ev = by_split.get("eval_synthetic", set()) | by_split.get("eval_pet", set())
        overlap = {x for x in tr & ev if x is not None}
        if overlap:
            fail(f"scenario ids shared between train/dev and eval: {sorted(overlap)}")
        print(f"  train+dev scenarios: {len(tr)}, eval scenarios: {len(ev)}, shared: {len(overlap)}")
    else:
        warn("scenarios.json not found; scenario-level separation not independently checked")

    # ---- 5. OOD flag consistency (the check the factory did not do) ---------
    print("\n== 5. OOD flag vs actual vertical novelty ==")
    train_verticals = {r["vertical"] for r in data["train"]} | {
        r["vertical"] for r in data["dev"]
    }
    for s in ("eval_synthetic", "eval_pet"):
        mismatched = [
            r["id"]
            for r in data[s]
            if (r["vertical"] not in train_verticals) != bool(r["ood_vertical"])
        ]
        unseen = sorted({r["vertical"] for r in data[s] if r["vertical"] not in train_verticals})
        print(f"  {s}: verticals unseen in train = {len(unseen)} {unseen if len(unseen) < 6 else ''}")
        if mismatched:
            warn(
                f"{s}: {len(mismatched)} records whose ood_vertical flag disagrees "
                f"with actual novelty vs train verticals (e.g. {mismatched[:3]})"
            )

    # ---- 6. Grounding sanity: ai_agent_steps vs recommended process ---------
    print("\n== 6. ai_agent_steps grounding (independent recomputation) ==")
    for s in SPLITS:
        scores = []
        for r in data[s]:
            g = r["gold"]
            rec = ngrams(" ".join(g.get("recommended_improved_process", [])), 3)
            for step in g.get("ai_agent_steps", []):
                sg = ngrams(step, 3)
                scores.append(1.0 if sg and jaccard(sg, rec) > 0.02 else 0.0)
        m = sum(scores) / len(scores) if scores else 0.0
        print(f"  {s}: {m:.2f} of ai_agent_steps overlap the recommended process")

    # ---- 7. Length budget for Stage 2 --------------------------------------
    print("\n== 7. Prompt length budget (chars; tokens ~= chars/3.6) ==")
    shots = pick_shots(data["train"])
    print(f"  few-shot exemplars selected: {[s['id'] for s in shots]}")
    for s in ("eval_synthetic", "eval_pet"):
        z, f2, tgt = [], [], []
        for r in data[s]:
            z.append(sum(len(m["content"]) for m in build_messages(r["input"])))
            f2.append(sum(len(m["content"]) for m in build_messages(r["input"], shots)))
            tgt.append(len(target_json(r["gold"])))
        print(
            f"  {s}: zero-shot max {max(z)} (~{max(z) // 36 * 10} tok) | "
            f"2-shot max {max(f2)} (~{max(f2) // 36 * 10} tok) | "
            f"target max {max(tgt)} (~{max(tgt) // 36 * 10} tok)"
        )
    tr_tot = [
        sum(len(m["content"]) for m in build_messages(r["input"])) + len(target_json(r["gold"]))
        for r in data["train"]
    ]
    tr_tot.sort()
    print(
        f"  train prompt+target: median ~{tr_tot[len(tr_tot) // 2] // 36 * 10} tok, "
        f"max ~{tr_tot[-1] // 36 * 10} tok"
    )

    # ---- 8. Distribution summary -------------------------------------------
    print("\n== 8. Composition ==")
    for s in SPLITS:
        d = Counter(r["difficulty"] for r in data[s])
        print(f"  {s:16s} n={len(data[s]):3d}  {dict(d)}")

    # ---- 9. Empty-field audit ----------------------------------------------
    print("\n== 9. Empty list fields in references ==")
    empt = defaultdict(int)
    for s, r in allrecs:
        for f in LIST_FIELDS:
            if not r["gold"].get(f):
                empt[f] += 1
    print(f"  {dict(empt) if empt else 'none'}")

    report(data)
    return 1 if failures else 0


def pick_shots(train: list[dict], k: int = 2) -> list[dict]:
    """Deterministic few-shot exemplar choice.

    Shortest total length, one per vertical, tie-broken by id. Short exemplars
    keep the 2-shot prompt inside context for the 696-word PET inputs; fixing
    them across all eval items (rather than retrieving per item) keeps the arm
    deterministic and cheap to explain.
    """
    ranked = sorted(train, key=lambda r: (len(r["input"]) + len(json.dumps(r["gold"])), r["id"]))
    out: list[dict] = []
    used: set[str] = set()
    for r in ranked:
        if r["vertical"] in used:
            continue
        out.append(r)
        used.add(r["vertical"])
        if len(out) == k:
            break
    return out


def report(data) -> None:
    print("\n" + "=" * 70)
    if warnings:
        print(f"WARNINGS ({len(warnings)}) - judgement calls, not blockers:")
        for w in warnings:
            print(f"  ! {w}")
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures[:40]:
            print(f"  X {f}")
        print("\nRESULT: FAIL")
    else:
        print("RESULT: PASS (all hard checks)")


if __name__ == "__main__":
    sys.exit(main())
