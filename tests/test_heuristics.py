"""Tests for the deterministic metrics.

The field-scoping test is the important one: a naive grounding check that
flags every output system absent from the input would penalise
`recommended_improved_process` for doing exactly what the task asks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nextverse.eval.heuristics import grounding_systems, score_output  # noqa: E402
from nextverse.eval.judge import aggregate_pairwise, bootstrap_ci  # noqa: E402
from nextverse.eval.text import content_recall, content_words, ngram_jaccard  # noqa: E402

INPUT = "We track invoices in a Xero spreadsheet and chase customers by phone."


def test_content_words_drops_stopwords_and_boilerplate():
    cw = content_words("The process step involves the invoice system")
    assert "invoice" in cw
    for w in ("the", "process", "step", "system"):
        assert w not in cw


def test_content_recall_is_directional():
    assert content_recall("Xero", INPUT) == 1.0
    assert content_recall("Salesforce", INPUT) == 0.0
    # Asymmetric: the long text is not "recalled by" the short one.
    assert content_recall(INPUT, "Xero") < 1.0


def test_ngram_jaccard_requires_word_order():
    a = "the agent drafts the invoice"
    assert ngram_jaccard(a, a) == 1.0
    # Same content words, different order -> near zero. This is why it is
    # reported alongside, not instead of, content recall.
    assert ngram_jaccard(a, "invoice the drafts agent the") < 0.2


def test_hallucinated_system_is_penalised():
    obj = {"systems_involved": ["Xero", "Salesforce CRM"]}
    assert grounding_systems(obj, INPUT)["systems_grounded"] == 0.5


def test_no_systems_is_vacuously_grounded():
    """19 reference records legitimately have an empty systems_involved."""
    assert grounding_systems({"systems_involved": []}, INPUT)["systems_grounded"] == 1.0


def test_new_tools_in_recommendation_are_not_penalised():
    """THE scoping test. Proposing Zapier is good output, not hallucination."""
    obj = {
        "systems_involved": ["Xero"],
        "recommended_improved_process": ["Adopt Zapier to automate the chase emails"],
    }
    g = grounding_systems(obj, INPUT)
    assert g["systems_grounded"] == 1.0          # unaffected by the proposal
    assert g["systems_novel_in_recommendation"] > 0  # counted, but as information


def test_score_output_never_raises_on_malformed():
    for bad in [{}, {"current_process": "not a list"}, {"ai_agent_steps": [1, 2]}]:
        assert isinstance(score_output(bad, INPUT, {"current_process": ["x"]}), dict)


def test_length_ratio_detects_under_generation():
    ref = {"current_process": ["a" * 100], "recommended_improved_process": ["b" * 100]}
    short = {"current_process": ["a" * 10], "recommended_improved_process": ["b" * 10]}
    assert score_output(short, INPUT, ref)["length_ratio_vs_reference"] < 0.2


def test_pairwise_position_disagreement_becomes_tie():
    rows = [
        {"verdict": "X", "position_consistent": True},
        {"verdict": "tie", "position_consistent": False},
        {"verdict": "Y", "position_consistent": True},
    ]
    a = aggregate_pairwise(rows)
    assert (a["x_wins"], a["ties"], a["y_wins"]) == (1, 1, 1)
    assert a["position_inconsistency_rate"] == 1 / 3
    assert a["win_rate_excl_ties"] == 0.5


def test_bootstrap_ci_brackets_a_clear_win():
    rows = [{"verdict": "X", "position_consistent": True}] * 40
    lo, hi = bootstrap_ci(rows, n_boot=2000, seed=1)
    assert lo == hi == 1.0


def test_bootstrap_ci_spans_zero_when_split():
    rows = ([{"verdict": "X", "position_consistent": True}] * 20 +
            [{"verdict": "Y", "position_consistent": True}] * 20)
    lo, hi = bootstrap_ci(rows, n_boot=4000, seed=1)
    assert lo < 0 < hi, "an even split must not look significant"
