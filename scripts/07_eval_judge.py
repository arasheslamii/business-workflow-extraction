#!/usr/bin/env python3
"""Layer 3: Gemini-as-judge. Login node, NEEDS INTERNET AND GEMINI_API_KEY.

Every response is cached to results/judge_cache/, so re-running is free and
deterministic. Use --dry-run first to see the exact call count before spending
any quota.

Usage:
  python scripts/07_eval_judge.py --dry-run          # count calls, no API
  python scripts/07_eval_judge.py --rubric           # per-field 1-5, all arms
  python scripts/07_eval_judge.py --pairwise         # blinded head-to-head
  python scripts/07_eval_judge.py --rubric --pairwise
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.data.loading import load_split  # noqa: E402
from nextverse.eval.judge import (  # noqa: E402
    aggregate_pairwise,
    bootstrap_ci,
    compare_pairwise,
    score_rubric,
)
from nextverse.eval.parsing import parse  # noqa: E402
from nextverse.llm_api import GeminiClient  # noqa: E402

ARMS = ["base_zeroshot", "base_fewshot", "tuned"]
# tuned vs BOTH baselines. The fewshot comparison is the competitive one; the
# zeroshot comparison is reported for completeness but is the easy win.
PAIRS = [("tuned", "base_fewshot"), ("tuned", "base_zeroshot")]


def load_arm(res: Path, arm: str, splits) -> dict[str, dict]:
    out = {}
    for split in splits:
        p = res / arm / f"{split}.jsonl"
        if not p.exists():
            raise SystemExit(f"missing {p}")
        for line in p.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["id"]] = row
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", action="store_true")
    ap.add_argument("--pairwise", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-models", action="store_true",
                    help="print judge model ids available to this key, then exit")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cfg = Config.load()

    if args.list_models:
        # Confirms the configured judge.model id is real BEFORE any quota is
        # spent on a run that would fail partway through.
        import os

        from google import genai

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY not set in this environment")
        want = cfg.get("judge.model")
        names = []
        for m in genai.Client(api_key=key).models.list():
            n = getattr(m, "name", "")
            if "generateContent" in (getattr(m, "supported_actions", None) or ["generateContent"]):
                names.append(n)
        for n in sorted(names):
            print(("* " if want in n else "  ") + n)
        print(f"\nconfigured judge.model = {want!r}")
        print("MATCH" if any(want in n for n in names) else "NOT FOUND - update config.yaml")
        return 0

    if not (args.rubric or args.pairwise or args.dry_run):
        raise SystemExit("choose --rubric and/or --pairwise (or --dry-run)")
    raw, res = cfg.path("paths.raw"), cfg.path("paths.results")
    splits = cfg.get("eval.splits")

    refs = {r["id"]: r for s in splits for r in load_split(raw, s)}
    arms = {a: load_arm(res, a, splits) for a in ARMS}
    ids = sorted(refs)
    if args.limit:
        ids = ids[: args.limit]

    n_rubric = len(ids) * len(ARMS)
    n_pair = len(ids) * len(PAIRS) * 2  # both orders, always
    print(f"eval items: {len(ids)}")
    print(f"  rubric calls  : {n_rubric}  ({len(ARMS)} arms x {len(ids)} items)")
    print(f"  pairwise calls: {n_pair}  ({len(PAIRS)} pairs x {len(ids)} items x 2 orders)")
    print(f"  TOTAL         : {n_rubric + n_pair}")
    if args.dry_run:
        print("\ndry run - no API calls made")
        return 0

    client = GeminiClient(
        cfg.get("judge.model"),
        res / "judge_cache",
        temperature=cfg.get("judge.temperature"),
        max_output_tokens=cfg.get("judge.max_output_tokens"),
        min_interval_s=cfg.get("judge.min_interval_s"),
    )

    out: dict = {"judge_model": cfg.get("judge.model"), "n_items": len(ids)}

    if args.rubric:
        print("\n== rubric ==")
        rub: dict = {}
        for arm in ARMS:
            rows = []
            for i, rid in enumerate(ids, 1):
                row = arms[arm][rid]
                obj = parse(row["raw_output"]).obj if row["parse_ok"] else None
                # Unparseable output is scored 1 across the board WITHOUT an API
                # call: there is nothing for a judge to read, and sending it
                # would spend quota to be told the obvious.
                if obj is None:
                    rows.append({"id": rid, "unparseable": True,
                                 "scores": {f: 1 for f in cfg_fields()}})
                else:
                    r = score_rubric(client, refs[rid]["input"], obj, tag=f"{arm}:{rid}")
                    rows.append({"id": rid, "unparseable": False, **r})
                if i % 10 == 0:
                    print(f"  {arm} {i}/{len(ids)}  cache_hits={client.stats['cache_hits']}")
            rub[arm] = rows
            print(f"  {arm}: done")
        out["rubric"] = rub

    if args.pairwise:
        print("\n== pairwise (both orders per item) ==")
        pw: dict = {}
        for x, y in PAIRS:
            rows = []
            for i, rid in enumerate(ids, 1):
                ox = parse(arms[x][rid]["raw_output"]).obj if arms[x][rid]["parse_ok"] else None
                oy = parse(arms[y][rid]["raw_output"]).obj if arms[y][rid]["parse_ok"] else None
                if ox is None or oy is None:
                    # One side is unreadable; award to the parseable side
                    # without an API call.
                    v = "Y" if ox is None and oy is not None else (
                        "X" if oy is None and ox is not None else "tie")
                    rows.append({"id": rid, "verdict": v, "order1_verdict": v,
                                 "order2_verdict": v, "position_consistent": True,
                                 "x_presented_first": True, "reasons": ["unparseable output"]})
                else:
                    r = compare_pairwise(
                        client, refs[rid]["input"], ox, oy,
                        item_id=rid, seed=cfg.get("seed"),
                    )
                    rows.append({"id": rid, **r})
                if i % 10 == 0:
                    print(f"  {x} vs {y} {i}/{len(ids)}  cache_hits={client.stats['cache_hits']}")
            agg = aggregate_pairwise(rows)
            lo, hi = bootstrap_ci(rows, seed=cfg.get("seed"))
            agg["margin_ci95"] = [lo, hi]
            pw[f"{x}_vs_{y}"] = {"aggregate": agg, "rows": rows}
            print(f"  {x} vs {y}: {agg['x_wins']}W/{agg['ties']}T/{agg['y_wins']}L  "
                  f"pos-inconsistency {agg['position_inconsistency_rate']:.0%}")
        out["pairwise"] = pw

    out["client_stats"] = client.stats
    path = res / "metrics_judge.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {path}")
    print(f"api_calls={client.stats['api_calls']} cache_hits={client.stats['cache_hits']} "
          f"retries={client.stats['retries']}")
    return 0


def cfg_fields():
    from nextverse.schema import FIELDS

    return FIELDS


if __name__ == "__main__":
    sys.exit(main())
