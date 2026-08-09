"""Layer 1: structural metrics. Fully deterministic, no API, no model."""

from __future__ import annotations

from typing import Any

from ..schema import FIELDS, field_presence, validate


def score_row(row: dict[str, Any]) -> dict[str, float]:
    """Structural metrics for one inference row from results/<arm>/<split>.jsonl."""
    obj = None
    if row.get("parse_ok"):
        from .parsing import parse

        obj = parse(row["raw_output"]).obj

    presence = field_presence(obj if isinstance(obj, dict) else {})
    out: dict[str, float] = {
        # strict = model emitted bare JSON; lenient = parsed after repair.
        # The gap is formatting discipline alone, so both are always reported.
        "strict_json": float(row.get("parse_strict_ok", False)),
        "lenient_json": float(row.get("parse_ok", False)),
        "schema_valid": float(row.get("parse_ok", False) and not validate(obj)),
    }
    for f in FIELDS:
        out[f"present.{f}"] = float(presence[f])
    out["fields_present"] = sum(presence.values()) / len(FIELDS)
    return out
