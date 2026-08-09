#!/usr/bin/env python3
"""Stage 5: find and format failure candidates. CPU only, no API.

Surfaces three distinct kinds of failure, because they have different causes
and different fixes:

  1. REGRESSIONS  - tuned scores worse than a baseline arm. The most important
                    category: fine-tuning actively made these worse.
  2. ABSOLUTE     - lowest-scoring tuned outputs regardless of the baseline.
  3. PATTERNS     - systematic weakness along a slice axis.

Machine-found candidates only. The written interpretation lives in
results/failures.md's analysis sections and in SUMMARY.md.

Usage:  python scripts/09_failure_analysis.py
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
from nextverse.eval.parsing import parse  # noqa: E402
from nextverse.schema import FIELDS  # noqa: E402

ARMS = ["base_zeroshot", "base_fewshot", "tuned"]
LABEL = {"base_zeroshot": "Base 0-shot", "base_fewshot": "Base 2-shot", "tuned": "Tuned"}
# Deterministic composite used when the judge is unavailable, and as a
# judge-independent cross-check when it is.
DET_KEYS = ["schema_valid", "step_coverage_vs_reference", "ai_steps_grounded_recall",
            "current_process_grounded", "systems_grounded"]


def trunc(s: str, n: int = 700) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n].rstrip() + " ...[truncated]"


def render_fields(obj, keys=("current_process", "ai_agent_steps", "bottlenecks_and_risks")):
    if not isinstance(obj, dict):
        return "_(unparseable)_"
    out = []
    for k in keys:
        v = obj.get(k)
        if isinstance(v, list):
            items = "\n".join(f"  - {x}" for x in v[:5] if isinstance(x, str))
            more = f"\n  - _(+{len(v) - 5} more)_" if len(v) > 5 else ""
            out.append(f"**`{k}`**\n{items or '  _(empty)_'}{more}")
        elif isinstance(v, str):
            out.append(f"**`{k}`** {v}")
        else:
            out.append(f"**`{k}`** _(missing)_")
    return "\n\n".join(out)


def main() -> int:
    cfg = Config.load()
    res = cfg.path("paths.results")
    raw = cfg.path("paths.raw")

    det = json.loads((res / "metrics_deterministic.json").read_text())
    judge_path = res / "metrics_judge.json"
    judge = json.loads(judge_path.read_text()) if judge_path.exists() else None

    refs = {r["id"]: r for s in cfg.get("eval.splits") for r in load_split(raw, s)}
    outputs = {a: {} for a in ARMS}
    for a in ARMS:
        for s in cfg.get("eval.splits"):
            for line in (res / a / f"{s}.jsonl").read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    outputs[a][row["id"]] = row

    # metrics[arm][id] -> dict
    metrics = defaultdict(dict)
    axes_of = {}
    for r in det["per_record"]:
        metrics[r["arm"]][r["id"]] = r["metrics"]
        axes_of[r["id"]] = {k: r[k] for k in
                            ("source", "ood_vertical", "vertical_unseen_in_train", "difficulty")}

    def det_score(arm, rid):
        m = metrics[arm][rid]
        return sum(m.get(k) or 0.0 for k in DET_KEYS) / len(DET_KEYS)

    rubric = {}
    if judge and "rubric" in judge:
        for a in ARMS:
            rubric[a] = {}
            for row in judge["rubric"][a]:
                vals = [v for v in row["scores"].values() if isinstance(v, (int, float))]
                rubric[a][row["id"]] = sum(vals) / len(vals) if vals else None

    pairwise_losses = defaultdict(list)
    if judge and "pairwise" in judge:
        for name, blk in judge["pairwise"].items():
            for row in blk["rows"]:
                if row["verdict"] == "Y":  # baseline beat tuned
                    pairwise_losses[row["id"]].append((name, row.get("reasons", [])))

    ids = sorted(refs)

    # ---- candidate ranking ------------------------------------------------
    regressions = []
    for rid in ids:
        d_t = det_score("tuned", rid)
        d_b = max(det_score("base_zeroshot", rid), det_score("base_fewshot", rid))
        r_t = rubric.get("tuned", {}).get(rid)
        r_b = max([rubric.get(a, {}).get(rid) or 0 for a in
                   ("base_zeroshot", "base_fewshot")], default=0) if rubric else None
        det_delta = d_t - d_b
        rub_delta = (r_t - r_b) if (r_t is not None and r_b is not None) else None
        lost = pairwise_losses.get(rid, [])
        if det_delta < -0.01 or (rub_delta is not None and rub_delta < 0) or lost:
            regressions.append({
                "id": rid, "det_delta": det_delta, "rub_delta": rub_delta,
                "det_tuned": d_t, "det_base": d_b, "rub_tuned": r_t, "rub_base": r_b,
                "pairwise_losses": lost,
            })
    regressions.sort(key=lambda x: (x["rub_delta"] if x["rub_delta"] is not None else 0,
                                    x["det_delta"]))

    absolute = sorted(
        ids,
        key=lambda r: (rubric.get("tuned", {}).get(r) if rubric else det_score("tuned", r)) or 0,
    )[:6]

    # ---- write ------------------------------------------------------------
    L = ["# Failure analysis\n"]
    L.append(f"Machine-found candidates from {len(ids)} eval records across "
             f"{len(ARMS)} arms. Judge: "
             f"`{judge['judge_model'] if judge else 'not run'}`.\n")
    L.append("Three categories, because they have different causes and different "
             "fixes: **regressions** (fine-tuning made it worse), **absolute** "
             "(worst tuned outputs regardless of baseline), and **patterns** "
             "(systematic weakness on a slice).\n")

    # 1. structural catastrophes
    L.append("\n## 1. Structural failures\n")
    bad = [(a, rid) for a in ARMS for rid in ids if not outputs[a][rid]["parse_ok"]]
    if bad:
        L.append("| Arm | id | difficulty | vertical | gen tokens | parse error |")
        L.append("|---|---|---|---|---|---|")
        for a, rid in bad:
            row = outputs[a][rid]
            L.append(f"| {LABEL[a]} | `{rid}` | {row['difficulty']} | {row['vertical']} "
                     f"| {row['gen_tokens']} | `{row['parse_error']}` |")
    else:
        L.append("_None._")

    # 2. regressions
    L.append(f"\n## 2. Regressions - tuned worse than the better baseline ({len(regressions)})\n")
    L.append("`det_delta` = tuned minus best-baseline on the deterministic "
             f"composite ({', '.join('`' + k + '`' for k in DET_KEYS)}). "
             "`rub_delta` = same on the judge's mean rubric score. "
             "Pairwise losses are items where a baseline won in BOTH orders.\n")
    if regressions:
        L.append("| id | difficulty | source | det_delta | rub_delta | tuned rubric | base rubric | pairwise losses |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in regressions:
            ax = axes_of[r["id"]]
            rd = f"{r['rub_delta']:+.2f}" if r["rub_delta"] is not None else "-"
            rt = f"{r['rub_tuned']:.2f}" if r["rub_tuned"] is not None else "-"
            rb = f"{r['rub_base']:.2f}" if r["rub_base"] is not None else "-"
            pl = ", ".join(n.replace("tuned_vs_", "") for n, _ in r["pairwise_losses"]) or "-"
            L.append(f"| `{r['id']}` | {ax['difficulty']} | {ax['source']} | "
                     f"{r['det_delta']:+.3f} | {rd} | {rt} | {rb} | {pl} |")
    else:
        L.append("_No regressions found._")

    # 3. patterns
    L.append("\n## 3. Patterns by slice axis\n")
    L.append("Tuned minus best-baseline on the deterministic composite, per group. "
             "Negative = fine-tuning hurt this slice.\n")
    for axis in ("source", "ood_vertical", "vertical_unseen_in_train", "difficulty"):
        groups = defaultdict(list)
        for rid in ids:
            groups[axes_of[rid][axis]].append(rid)
        L.append(f"\n**`{axis}`**\n")
        L.append("| Group | n | tuned | best baseline | delta | rubric delta |")
        L.append("|---|---|---|---|---|---|")
        for g in sorted(groups):
            gr = groups[g]
            t = sum(det_score("tuned", r) for r in gr) / len(gr)
            b = sum(max(det_score("base_zeroshot", r), det_score("base_fewshot", r))
                    for r in gr) / len(gr)
            if rubric:
                rt = [rubric["tuned"].get(r) for r in gr]
                rb = [max(rubric["base_zeroshot"].get(r) or 0,
                          rubric["base_fewshot"].get(r) or 0) for r in gr]
                rt = [x for x in rt if x is not None]
                rd = (sum(rt) / len(rt) - sum(rb) / len(rb)) if rt else None
                rds = f"{rd:+.2f}" if rd is not None else "-"
            else:
                rds = "-"
            L.append(f"| `{g}` | {len(gr)} | {t:.3f} | {b:.3f} | {t - b:+.3f} | {rds} |")

    # 4. side-by-side
    L.append("\n## 4. Side-by-side detail\n")
    shown = []
    for r in regressions[:4]:
        shown.append(r["id"])
    for rid in absolute:
        if rid not in shown and len(shown) < 7:
            shown.append(rid)
    for rid in shown:
        ref = refs[rid]
        ax = axes_of[rid]
        L.append(f"\n### `{rid}` - {ref['vertical']} / {ref['process']} "
                 f"({ax['difficulty']}, {ax['source']})\n")
        rt = rubric.get("tuned", {}).get(rid)
        L.append(f"Tuned rubric {f'{rt:.2f}' if rt else '-'} | "
                 f"det composite {det_score('tuned', rid):.3f} vs best baseline "
                 f"{max(det_score('base_zeroshot', rid), det_score('base_fewshot', rid)):.3f}\n")
        if rid in pairwise_losses:
            for name, reasons in pairwise_losses[rid]:
                L.append(f"- **Judge preferred {name.replace('tuned_vs_', '')}**: "
                         f"{reasons[0] if reasons else ''}")
            L.append("")
        L.append("<details><summary>Input description</summary>\n")
        L.append(f"```\n{trunc(ref['input'], 1400)}\n```\n")
        L.append("</details>\n")
        L.append("| | |")
        L.append("|---|---|")
        L.append("")
        for a in ("base_fewshot", "tuned"):
            obj = parse(outputs[a][rid]["raw_output"]).obj if outputs[a][rid]["parse_ok"] else None
            L.append(f"\n**{LABEL[a]}**\n")
            L.append(render_fields(obj))
        L.append("\n**Reference**\n")
        L.append(render_fields(ref["gold"]))
        if ref.get("reference_type") == "model_generated_unverified":
            L.append("\n_Reference is `model_generated_unverified` (PET slice): treat "
                     "as a comparison point, not ground truth._")

    # Hand-written interpretation lives in its own file so that regenerating
    # this report can never destroy it.
    notes = ROOT / "analysis_notes.md"
    if notes.exists():
        L.append("\n---\n")
        L.append(notes.read_text())

    L.append("\n---\n_Machine-found sections generated by "
             "`scripts/09_failure_analysis.py`; written analysis from "
             "`analysis_notes.md`._\n")

    path = res / "failures.md"
    path.write_text("\n".join(L))
    print(f"wrote {path}")
    print(f"  structural failures: {len(bad)}")
    print(f"  regressions:         {len(regressions)}")
    print(f"  detailed:            {len(shown)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
