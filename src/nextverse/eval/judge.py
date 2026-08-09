"""Layer 3: LLM-as-judge orchestration.

Two independent measurements:

  rubric   - absolute per-field 1-5 scores for each arm, judged one output at a
             time. Comparable across arms but susceptible to the judge's own
             calibration drift.
  pairwise - blinded head-to-head. EVERY pair is judged in BOTH orders. If the
             two orders disagree, the result is recorded as a position-bias
             inconsistency and counted as a tie rather than quietly taking one
             of the two verdicts. The inconsistency rate is itself reported: it
             is the honest measure of how much to trust this layer.

The gold answers were authored by Claude Opus 5 and the judge is Gemini, so
judge and reference-author are different model families - which removes the
most direct form of self-preference, though not the general circularity of
grading synthetic data with an LLM.
"""

from __future__ import annotations

import json
import random
from typing import Any

from ..llm_api import GeminiClient
from ..prompts.judge import field_rubric_prompt, pairwise_prompt
from ..schema import FIELDS
from .parsing import parse


def _parse_json_response(text: str, where: str) -> dict[str, Any]:
    # Judge output gets the SAME repair leniency as the arms: markdown fences
    # are stripped and a balanced object is extracted. An unrecoverable failure
    # here almost always means the response was cut mid-object, so say so.
    r = parse(text)
    if not r.ok or not isinstance(r.obj, dict):
        looks_cut = text.count("{") > text.count("}")
        hint = (
            " - response appears TRUNCATED (unbalanced braces); raise "
            "judge.max_output_tokens" if looks_cut else ""
        )
        raise ValueError(
            f"{where}: judge returned unparseable output{hint}: ...{text[-200:]!r}"
        )
    return r.obj


def score_rubric(
    client: GeminiClient, description: str, output: Any, *, tag: str = ""
) -> dict[str, Any]:
    raw = client.generate(field_rubric_prompt(description, output), tag=f"rubric:{tag}")
    obj = _parse_json_response(raw, f"rubric {tag}")
    scores: dict[str, int] = {}
    for f in FIELDS:
        v = obj.get(f)
        if isinstance(v, (int, float)) and 1 <= v <= 5:
            scores[f] = int(v)
        else:
            # Missing or out-of-range: record as None rather than defaulting to
            # a number, so a broken judge response cannot masquerade as a score.
            scores[f] = None  # type: ignore[assignment]
    return {"scores": scores, "notes": obj.get("notes", ""), "raw": raw}


def compare_pairwise(
    client: GeminiClient,
    description: str,
    out_x: Any,
    out_y: Any,
    *,
    item_id: str,
    seed: int,
) -> dict[str, Any]:
    """Blinded, position-controlled comparison of arm X against arm Y.

    Runs both orders. `presented_first` is randomised per item purely so the
    cached prompts are not all in the same arrangement; correctness does not
    depend on it because both orders are always run.
    """
    rng = random.Random(f"{seed}:{item_id}")
    x_first = rng.random() < 0.5

    a1, b1 = (out_x, out_y) if x_first else (out_y, out_x)
    r1 = _parse_json_response(
        client.generate(pairwise_prompt(description, a1, b1), tag=f"pw1:{item_id}"),
        f"pairwise {item_id} order1",
    )
    a2, b2 = (b1, a1)
    r2 = _parse_json_response(
        client.generate(pairwise_prompt(description, a2, b2), tag=f"pw2:{item_id}"),
        f"pairwise {item_id} order2",
    )

    def to_arm(winner: str, first_is_x: bool) -> str:
        w = str(winner).strip().lower()
        if w in ("tie", "draw", "equal"):
            return "tie"
        if w in ("1", "analysis 1", "a"):
            return "X" if first_is_x else "Y"
        if w in ("2", "analysis 2", "b"):
            return "Y" if first_is_x else "X"
        return "tie"

    v1 = to_arm(r1.get("winner", "tie"), x_first)
    v2 = to_arm(r2.get("winner", "tie"), not x_first)

    consistent = v1 == v2
    # Disagreement between orders means the verdict was driven by position, not
    # content. Counting it as a tie is the conservative choice; silently taking
    # order 1 would import the very bias we are controlling for.
    verdict = v1 if consistent else "tie"

    return {
        "verdict": verdict,
        "order1_verdict": v1,
        "order2_verdict": v2,
        "position_consistent": consistent,
        "x_presented_first": x_first,
        "reasons": [r1.get("reason", ""), r2.get("reason", "")],
    }


def aggregate_pairwise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    wins = sum(1 for r in rows if r["verdict"] == "X")
    losses = sum(1 for r in rows if r["verdict"] == "Y")
    ties = n - wins - losses
    inconsistent = sum(1 for r in rows if not r["position_consistent"])
    return {
        "n": n,
        "x_wins": wins,
        "y_wins": losses,
        "ties": ties,
        "win_rate_excl_ties": wins / (wins + losses) if (wins + losses) else None,
        "position_inconsistency_rate": inconsistent / n if n else 0.0,
    }


def bootstrap_ci(
    rows: list[dict[str, Any]], *, n_boot: int = 10000, seed: int = 0
) -> tuple[float, float]:
    """Percentile bootstrap CI on (wins - losses) / n.

    n=40 cannot support a confident claim; this exists so the report states the
    uncertainty instead of implying precision it does not have.
    """
    vals = [1 if r["verdict"] == "X" else (-1 if r["verdict"] == "Y" else 0) for r in rows]
    if not vals:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(n_boot):
        means.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return (means[int(0.025 * n_boot)], means[int(0.975 * n_boot)])
