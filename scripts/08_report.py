#!/usr/bin/env python3
"""Aggregate every layer into results/report.md. CPU only, no API.

Runs with whatever exists: if the judge has not been run, the deterministic
layers are still reported and the judge sections say so explicitly rather than
being silently omitted.

Usage:  python scripts/08_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.schema import FIELDS  # noqa: E402

ARMS = ["base_zeroshot", "base_fewshot", "tuned"]
LABEL = {
    "base_zeroshot": "Base (0-shot)",
    "base_fewshot": "Base (2-shot)",
    "tuned": "Tuned (LoRA)",
}


def fmt(v, pct=False):
    if v is None:
        return "-"
    return f"{v:.0%}" if pct else f"{v:.3f}"


def table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def main() -> int:
    cfg = Config.load()
    res = cfg.path("paths.results")

    det_path = res / "metrics_deterministic.json"
    if not det_path.exists():
        raise SystemExit("run scripts/06_eval_deterministic.py first")
    det = json.loads(det_path.read_text())
    agg = det["aggregate"]

    judge_path = res / "metrics_judge.json"
    judge = json.loads(judge_path.read_text()) if judge_path.exists() else None

    L: list[str] = []
    L.append("# Evaluation report\n")
    L.append(f"Model: `{cfg.get('model.name')}` | LoRA r={cfg.get('train.lora_r')} "
             f"alpha={cfg.get('train.lora_alpha')} | seed {cfg.get('seed')}\n")
    L.append("Three arms. **Base (2-shot) is the competitive baseline** - a "
             "zero-shot small model fails mostly on JSON formatting, so "
             "comparing only against it would report a formatting win as if it "
             "were a reasoning win.\n")

    # ---- Layer 1 ----------------------------------------------------------
    L.append("\n## Layer 1 - structural (deterministic)\n")
    L.append("`strict` = model emitted bare JSON. `lenient` = parsed after "
             "fence-stripping and balanced-brace extraction. **The same repair "
             "function is applied to every arm.** The strict/lenient gap is "
             "formatting discipline alone.\n")
    rows = []
    for a in ARMS:
        v = agg["overall"][a]
        rows.append([LABEL[a], fmt(v["strict_json"], True), fmt(v["lenient_json"], True),
                     fmt(v["schema_valid"], True), fmt(v["fields_present"], True)])
    L.append(table(rows, ["Arm", "Strict JSON", "Lenient JSON", "Schema valid",
                          "Fields present"]))

    L.append("\n### Per-field presence (non-empty)\n")
    rows = []
    for f in FIELDS:
        rows.append([f"`{f}`"] + [fmt(agg["overall"][a].get(f"present.{f}"), True) for a in ARMS])
    L.append(table(rows, ["Field"] + [LABEL[a] for a in ARMS]))

    # ---- Layer 2 ----------------------------------------------------------
    L.append("\n## Layer 2 - content heuristics (deterministic, judge-independent)\n")
    L.append("This layer carries equal weight to the judge. Gold answers were "
             "LLM-authored and the judge is an LLM, so layer 3 cannot fully "
             "escape circularity; these metrics can.\n")
    L.append("**Metric definitions** (a grounding number is meaningless without "
             "its definition - our own QC produced 0.23, 0.51 and 0.83 for "
             "'the same' metric under three definitions):\n")
    for k, d in det["metric_definitions"].items():
        L.append(f"- **`{k}`** - {d}")
    L.append("")
    hkeys = ["systems_grounded", "current_process_grounded", "step_coverage_vs_reference",
             "ai_steps_grounded_recall", "ai_steps_grounded_ngram",
             "length_ratio_vs_reference", "systems_novel_in_recommendation"]
    rows = []
    for a in ARMS:
        v = agg["overall"][a]
        rows.append([LABEL[a]] + [fmt(v.get(k)) for k in hkeys])
    L.append(table(rows, ["Arm"] + [f"`{k}`" for k in hkeys]))

    # ---- Slices -----------------------------------------------------------
    L.append("\n## Breakdowns by analysis axis\n")
    L.append("Axis definitions:\n")
    for k, d in det["axis_definitions"].items():
        L.append(f"- **`{k}`** - {d}")
    L.append("")
    key_metrics = ["schema_valid", "ai_steps_grounded_recall", "length_ratio_vs_reference"]
    for axis, groups in det["aggregate"]["by_axis"].items():
        L.append(f"\n### Axis: `{axis}`\n")
        rows = []
        for gval in sorted(groups):
            for a in ARMS:
                g = groups[gval].get(a)
                if not g:
                    continue
                rows.append([f"`{gval}`", LABEL[a], str(g["n"])] +
                            [fmt(g.get(k)) for k in key_metrics])
        L.append(table(rows, ["Group", "Arm", "n"] + [f"`{k}`" for k in key_metrics]))

    # ---- Layer 3 ----------------------------------------------------------
    L.append("\n## Layer 3 - LLM-as-judge\n")
    if judge is None:
        L.append("_Not yet run._ Execute `python scripts/07_eval_judge.py "
                 "--rubric --pairwise` to populate this section.\n")
    else:
        cs = judge.get("client_stats", {})
        L.append(f"Judge: **`{judge['judge_model']}`**, temperature 0, "
                 f"{judge['n_items']} items. Different model family from the "
                 "reference author (Claude Opus 5), which removes direct "
                 "self-preference but not general circularity.\n")
        L.append(f"Call stats: {cs.get('api_calls', '?')} API calls, "
                 f"{cs.get('cache_hits', '?')} cache hits, "
                 f"{cs.get('retries', '?')} retries.\n")
        L.append("> **Judge determinism caveat.** Temperature 0 is *not* "
                 "sufficient here: this is a thinking model (measured "
                 "~1300-1900 thinking tokens per rubric call) and the same "
                 "prompt was observed returning different field scores across "
                 "calls. The on-disk response cache - not temperature - is what "
                 "makes these numbers reproducible after the fact.\n")
        L.append("> **Model selection was quota-forced.** `gemini-3.6-flash` and "
                 "`gemini-3.5-flash` are both capped at 20 requests/day on the "
                 "free tier and `gemini-2.5-flash`/`gemini-2.5-flash-lite` "
                 "return 404, so the judge is a *lite*-tier model. A stronger "
                 "judge would be a straightforward v0.2 upgrade.\n")

        if "rubric" in judge:
            L.append("\n### Per-field rubric (1-5)\n")
            rows = []
            for f in FIELDS:
                r = [f"`{f}`"]
                for a in ARMS:
                    vals = [x["scores"].get(f) for x in judge["rubric"][a]]
                    vals = [v for v in vals if isinstance(v, (int, float))]
                    r.append(f"{sum(vals) / len(vals):.2f}" if vals else "-")
                rows.append(r)
            overall = ["**mean**"]
            for a in ARMS:
                vals = [v for x in judge["rubric"][a] for v in x["scores"].values()
                        if isinstance(v, (int, float))]
                overall.append(f"**{sum(vals) / len(vals):.2f}**" if vals else "-")
            rows.append(overall)
            L.append(table(rows, ["Field"] + [LABEL[a] for a in ARMS]))

        if "pairwise" in judge:
            L.append("\n### Blinded pairwise\n")
            L.append("Every pair judged in **both orders**. Where the two orders "
                     "disagree the verdict was driven by position, not content; "
                     "those are counted as ties and the inconsistency rate is "
                     "reported as the honest measure of judge reliability.\n")
            rows = []
            for name, blk in judge["pairwise"].items():
                a = blk["aggregate"]
                lo, hi = a["margin_ci95"]
                wr = a["win_rate_excl_ties"]
                rows.append([
                    name.replace("_vs_", " vs "), str(a["n"]),
                    str(a["x_wins"]), str(a["ties"]), str(a["y_wins"]),
                    f"{wr:.0%}" if wr is not None else "-",
                    f"[{lo:+.2f}, {hi:+.2f}]",
                    f"{a['position_inconsistency_rate']:.0%}",
                ])
            L.append(table(rows, ["Comparison", "n", "Wins", "Ties", "Losses",
                                  "Win rate (excl. ties)", "Margin 95% CI",
                                  "Position inconsistency"]))
            L.append("\n**Margin** = (wins - losses)/n, percentile bootstrap. "
                     "At n=40 a CI spanning 0 means the result is not "
                     "statistically distinguishable from no difference.\n")

    L.append("\n---\n")
    L.append("Regenerate: `python scripts/06_eval_deterministic.py && "
             "python scripts/08_report.py`\n")

    path = res / "report.md"
    path.write_text("\n".join(L))
    print(f"wrote {path} ({len(L)} blocks)")
    if judge is None:
        print("NOTE: judge layer absent - report marks it as not yet run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
