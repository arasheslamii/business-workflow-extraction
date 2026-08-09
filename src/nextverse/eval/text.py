"""Shared text primitives for the deterministic metrics.

Every heuristic in heuristics.py is defined in terms of these, and the exact
definitions are reproduced in results/report.md. A grounding number is
meaningless without its definition attached - our own QC produced 0.23, 0.51
and 0.83 for "the same" metric under three different definitions.
"""

from __future__ import annotations

import re

# Domain-neutral stopwords plus process-vocabulary that appears in essentially
# every record ("step", "process", "system"). Including the latter matters: it
# is shared boilerplate, so leaving it in inflates every overlap score towards
# a common baseline and compresses the differences we are trying to measure.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the of to in for and or is are was were be been being by with on at from
    that this it as which can could should would will shall may might must do does
    did done has have had not no if when then than into via each any all more most
    other new use used using their there they them we our you your his her its
    who whom what where how why so such but also them these those i he she
    step steps process processes system systems workflow business
    """.split()
)


def tokens(text: str) -> list[str]:
    """Lowercased alphanumeric tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def content_words(text: str) -> set[str]:
    """Tokens that are not stopwords and are longer than 2 characters.

    The length filter drops residual noise ("uk", "cc", "ok") that survives the
    stopword list without carrying domain meaning.
    """
    return {t for t in tokens(text) if t not in STOPWORDS and len(t) > 2}


def ngrams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    """Word n-grams over raw tokens (stopwords retained).

    Stopwords are kept here deliberately: n-grams measure phrasing overlap, and
    removing function words would let differently-worded phrases collide.
    """
    t = tokens(text)
    return {tuple(t[i : i + n]) for i in range(max(0, len(t) - n + 1))}


def content_recall(candidate: str, reference: str) -> float:
    """Fraction of the CANDIDATE's content words that also appear in REFERENCE.

    Directional and asymmetric. Reads as: "how much of what this text says is
    supported by that text". Returns 0.0 for an empty candidate.
    """
    c = content_words(candidate)
    if not c:
        return 0.0
    return len(c & content_words(reference)) / len(c)


def ngram_jaccard(a: str, b: str, n: int = 3) -> float:
    """Symmetric n-gram overlap. Stricter than content_recall: it requires
    matching word ORDER, so paraphrase scores near zero."""
    ga, gb = ngrams(a, n), ngrams(b, n)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def best_match(candidate: str, references: list[str]) -> float:
    """Highest content_recall of `candidate` against any single reference."""
    return max((content_recall(candidate, r) for r in references), default=0.0)
