"""Analysis slice axes.

The delivered `ood_vertical` flag marks only synthetic records designed as
out-of-domain; all 12 PET records carry False despite every one of their
verticals being unseen in training. Rather than mutate data/raw, we expose
THREE independent axes and every report states which one it used.
"""

from __future__ import annotations

from typing import Any, Callable

AXES: dict[str, str] = {
    "source": "synthetic vs pet_real (delivered field)",
    "ood_vertical": "the delivered flag: synthetic records authored as out-of-domain",
    "vertical_unseen_in_train": (
        "DERIVED at analysis time: record's vertical does not occur in "
        "train+dev. Differs from ood_vertical because all 12 PET verticals are "
        "unseen yet flagged False."
    ),
    "difficulty": "standard / vague / contradictory (delivered field)",
}


def build_axis_fns(train_verticals: set[str]) -> dict[str, Callable[[dict], str]]:
    return {
        "source": lambda r: str(r.get("source")),
        "ood_vertical": lambda r: str(bool(r.get("ood_vertical"))),
        "vertical_unseen_in_train": lambda r: str(r.get("vertical") not in train_verticals),
        "difficulty": lambda r: str(r.get("difficulty")),
    }


def train_vertical_set(train: list[dict[str, Any]], dev: list[dict[str, Any]]) -> set[str]:
    return {r["vertical"] for r in train} | {r["vertical"] for r in dev}
