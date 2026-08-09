"""Layer 2: deterministic content heuristics.

These are the judge-independent metrics. Because gold answers were authored by a
frontier LLM and the judge is a frontier LLM, layer 3 cannot escape a degree of
circularity; this layer can, so it carries equal billing in the report.

EVERY metric below is reported with its definition attached (see METRIC_DEFS,
which is emitted verbatim into report.md). Field scoping is deliberate and is
the part most likely to be got wrong - see grounding_systems.
"""

from __future__ import annotations

from typing import Any

from ..schema import LIST_FIELDS
from .text import best_match, content_recall, content_words, ngram_jaccard

METRIC_DEFS: dict[str, str] = {
    "systems_grounded": (
        "Of the systems named in `systems_involved`, the fraction whose content "
        "words appear in the INPUT description. Measures hallucinated tooling. "
        "Scoped to `systems_involved` and `current_process` ONLY - see "
        "systems_novel_in_recommendation."
    ),
    "systems_novel_in_recommendation": (
        "Count of systems named in `recommended_improved_process` that do NOT "
        "appear in the input. Reported as INFORMATION, never as an error: "
        "proposing a tool the business does not yet use is the point of the "
        "task. Penalising this would score the best outputs worst."
    ),
    "current_process_grounded": (
        "Mean content-word recall of each `current_process` step against the "
        "input. Measures whether the described as-is process is supported by "
        "what the business actually said."
    ),
    "step_coverage_vs_reference": (
        "For each reference `current_process` step, the best content-word recall "
        "achieved by any candidate step; averaged over reference steps. "
        "Recall-oriented: penalises omitting steps, not adding them."
    ),
    "ai_steps_grounded_recall": (
        "HEADLINE grounding variant. Mean content-word recall of each "
        "`ai_agent_steps` entry against the union of "
        "`recommended_improved_process`. Answers: do the proposed AI steps refer "
        "to steps that were actually recommended?"
    ),
    "ai_steps_grounded_ngram": (
        "STRICTER variant of the same quantity: mean 3-gram Jaccard of each "
        "`ai_agent_steps` entry against the union of "
        "`recommended_improved_process`. Requires matching word order, so "
        "paraphrased-but-correct references score near zero. Reported alongside "
        "the recall variant precisely because the two disagree."
    ),
    "length_ratio_vs_reference": (
        "Total characters across all list fields, divided by the same for the "
        "reference. 1.0 = reference length. Detects under-generation, the "
        "dominant base-model failure."
    ),
}


def _systems_text(obj: dict[str, Any]) -> list[str]:
    v = obj.get("systems_involved")
    return [s for s in v if isinstance(s, str)] if isinstance(v, list) else []


def _joined(obj: dict[str, Any], field: str) -> str:
    v = obj.get(field)
    return " ".join(x for x in v if isinstance(x, str)) if isinstance(v, list) else ""


def grounding_systems(obj: dict[str, Any], input_text: str) -> dict[str, float]:
    """Systems grounding, scoped by field.

    The scoping is the whole point. A system named in `current_process` that is
    absent from the input is a hallucination - the model invented software the
    business does not run. The same system named in
    `recommended_improved_process` is a RECOMMENDATION and is legitimate. A
    naive "output systems not in input" check conflates the two and would
    punish exactly the outputs that do the task well.
    """
    systems = _systems_text(obj)
    # >= 0.5 of a system name's content words must appear in the input. A bare
    # >0 threshold fires on any shared word ("system", "online"); requiring all
    # words fails on trivial variants ("Xero" vs "Xero accounting").
    grounded = [s for s in systems if content_recall(s, input_text) >= 0.5]

    # Vocabulary in the recommendation that the input never used. A proxy for
    # "proposed something new", reported as information only.
    novel_terms = content_words(
        _joined(obj, "recommended_improved_process")
    ) - content_words(input_text)

    return {
        # No systems named is vacuously grounded, not a failure: 19 reference
        # records legitimately have an empty systems_involved.
        "systems_grounded": len(grounded) / len(systems) if systems else 1.0,
        "systems_count": float(len(systems)),
        "systems_novel_in_recommendation": float(len(novel_terms)),
    }


def score_output(
    obj: dict[str, Any], input_text: str, reference: dict[str, Any]
) -> dict[str, float]:
    """All layer-2 metrics for one parsed output. Never raises: input may be
    arbitrarily malformed model output."""
    if not isinstance(obj, dict):
        return {k: 0.0 for k in METRIC_DEFS}

    out: dict[str, float] = {}
    out.update(grounding_systems(obj, input_text))

    cur = obj.get("current_process")
    cur = [s for s in cur if isinstance(s, str)] if isinstance(cur, list) else []
    out["current_process_grounded"] = (
        sum(content_recall(s, input_text) for s in cur) / len(cur) if cur else 0.0
    )

    ref_cur = reference.get("current_process", [])
    out["step_coverage_vs_reference"] = (
        sum(best_match(r, cur) for r in ref_cur) / len(ref_cur) if ref_cur and cur else 0.0
    )

    ai = obj.get("ai_agent_steps")
    ai = [s for s in ai if isinstance(s, str)] if isinstance(ai, list) else []
    rec = _joined(obj, "recommended_improved_process")
    out["ai_steps_grounded_recall"] = (
        sum(content_recall(s, rec) for s in ai) / len(ai) if ai and rec else 0.0
    )
    out["ai_steps_grounded_ngram"] = (
        sum(ngram_jaccard(s, rec) for s in ai) / len(ai) if ai and rec else 0.0
    )

    cand_len = sum(len(_joined(obj, f)) for f in LIST_FIELDS)
    ref_len = sum(
        len(" ".join(x for x in reference.get(f, []) if isinstance(x, str)))
        for f in LIST_FIELDS
    )
    out["length_ratio_vs_reference"] = cand_len / ref_len if ref_len else 0.0

    return out
