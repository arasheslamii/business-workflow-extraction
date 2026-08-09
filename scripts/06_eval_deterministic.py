#!/usr/bin/env python3
"""Layers 1 and 2: structural + heuristic metrics. Login node, CPU, no API.

Runs in seconds and requires no key, so it can be re-run freely.
Writes results/metrics_deterministic.json

Usage:  python scripts/06_eval_deterministic.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.data.loading import load_split  # noqa: E402
from nextverse.eval.axes import AXES, build_axis_fns, train_vertical_set  # noqa: E402
from nextverse.eval.heuristics import METRIC_DEFS, score_output  # noqa: E402
from nextverse.eval.parsing import parse  # noqa: E402
from nextverse.eval.structural import score_row  # noqa: E402

ARMS = {"base_zeroshot": "base_zeroshot", "base_fewshot": "base_fewshot", "tuned": "tuned"}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def main() -> int:
    cfg = Config.load()
    raw = cfg.path("paths.raw")
    res = cfg.path("paths.results")

    refs = {}
    for split in cfg.get("eval.splits"):
        for r in load_split(raw, split):
            refs[r["id"]] = r
    tv = train_vertical_set(load_split(raw, "train"), load_split(raw, "dev"))
    axis_fns = build_axis_fns(tv)

    per_record: list[dict] = []
    for arm in ARMS:
        for split in cfg.get("eval.splits"):
            p = res / arm / f"{split}.jsonl"
            if not p.exists():
                raise SystemExit(f"missing {p} - run scripts/03_run_base.py --arm ... first")
            for line in p.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                ref = refs[row["id"]]
                obj = parse(row["raw_output"]).obj if row["parse_ok"] else None
                m = score_row(row)
                m.update(
                    score_output(obj if isinstance(obj, dict) else {}, ref["input"], ref["gold"])
                )
                per_record.append(
                    {
                        "arm": arm,
                        "id": row["id"],
                        "split": split,
                        **{a: fn(ref) for a, fn in axis_fns.items()},
                        "metrics": m,
                    }
                )

    # Aggregate: overall, by split, and by each declared axis.
    keys = sorted({k for r in per_record for k in r["metrics"]})
    agg: dict = {"overall": {}, "by_split": {}, "by_axis": {}}
    for arm in ARMS:
        rows = [r for r in per_record if r["arm"] == arm]
        agg["overall"][arm] = {k: mean([r["metrics"].get(k) for r in rows]) for k in keys}
        for split in cfg.get("eval.splits"):
            sr = [r for r in rows if r["split"] == split]
            agg["by_split"].setdefault(split, {})[arm] = {
                k: mean([r["metrics"].get(k) for r in sr]) for k in keys
            }
        for axis in AXES:
            groups = defaultdict(list)
            for r in rows:
                groups[r[axis]].append(r)
            for gval, gr in groups.items():
                agg["by_axis"].setdefault(axis, {}).setdefault(gval, {})[arm] = {
                    "n": len(gr),
                    **{k: mean([r["metrics"].get(k) for r in gr]) for k in keys},
                }

    out = {
        "metric_definitions": METRIC_DEFS,
        "axis_definitions": AXES,
        "aggregate": agg,
        "per_record": per_record,
    }
    path = res / "metrics_deterministic.json"
    path.write_text(json.dumps(out, indent=2))

    print(f"wrote {path}  ({len(per_record)} records x {len(ARMS)} arms)\n")
    hdr = ["strict_json", "lenient_json", "schema_valid", "fields_present",
           "ai_steps_grounded_recall", "length_ratio_vs_reference"]
    print(f"{'arm':16s}" + "".join(f"{h[:18]:>20s}" for h in hdr))
    for arm in ARMS:
        v = agg["overall"][arm]
        print(f"{arm:16s}" + "".join(f"{v[h]:>20.3f}" for h in hdr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
