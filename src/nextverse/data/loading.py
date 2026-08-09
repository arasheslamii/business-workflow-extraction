"""Dataset loading and deterministic few-shot exemplar selection.

Shared by the verification script, the baseline runner and (later) training, so
that "which 2 examples are the few-shot exemplars" has exactly one answer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_split(raw_dir: Path, split: str) -> list[dict[str, Any]]:
    p = Path(raw_dir) / f"{split}.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"split file missing: {p}")
    recs = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not recs:
        raise ValueError(f"split {split} is empty")
    return recs


def pick_shots(train: list[dict[str, Any]], k: int = 2) -> list[dict[str, Any]]:
    """Deterministic few-shot exemplars: shortest total length, distinct verticals.

    Drawn from TRAIN ONLY - using an eval record here would be leakage.
    Shortest-first keeps the 2-shot prompt inside context for the 696-word PET
    inputs; distinct verticals avoid teaching a single domain's vocabulary.
    Fixed across all eval items rather than retrieved per item, so the arm is
    deterministic and there is no retrieval quality confound to explain.
    """
    ranked = sorted(
        train, key=lambda r: (len(r["input"]) + len(json.dumps(r["gold"])), r["id"])
    )
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for r in ranked:
        if r["vertical"] in seen:
            continue
        out.append(r)
        seen.add(r["vertical"])
        if len(out) == k:
            break
    if len(out) < k:
        raise ValueError(f"could not select {k} exemplars from {len(train)} train records")
    return out
