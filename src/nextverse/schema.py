"""The single definition of the 10-field workflow schema.

Used by data QC, training, inference and evaluation so that the target format
can never drift between stages.

Deliberately pure-stdlib (no pydantic/jsonschema): this module must import on
the login node before any venv exists, and on the GPU node where we want the
dependency surface as small as possible.
"""

from __future__ import annotations

from typing import Any

# Field order is fixed and is the order fields are presented in the prompt and
# in every report table. Changing it changes the prompt, so treat as frozen.
FIELDS: tuple[str, ...] = (
    "objective",
    "trigger",
    "owner_and_participants",
    "inputs_data_required",
    "systems_involved",
    "current_process",
    "bottlenecks_and_risks",
    "recommended_improved_process",
    "ai_agent_steps",
    "human_approvals_controls",
)

# Types are derived from the delivered gold data, not invented here.
STR_FIELDS: tuple[str, ...] = ("objective", "trigger")
LIST_FIELDS: tuple[str, ...] = (
    "inputs_data_required",
    "systems_involved",
    "current_process",
    "bottlenecks_and_risks",
    "recommended_improved_process",
    "ai_agent_steps",
    "human_approvals_controls",
)
OBJ_FIELDS: tuple[str, ...] = ("owner_and_participants",)

# Fields where an empty list is a legitimate answer rather than a defect.
# A business genuinely may use no software at all; it always has *some* process.
EMPTY_ALLOWED: frozenset[str] = frozenset({"systems_involved"})

# Human-readable spec injected into the prompt. Kept in this module so the
# prompt and the validator can never disagree about the contract.
FIELD_SPEC: dict[str, str] = {
    "objective": "string - the business objective this workflow exists to achieve",
    "trigger": "string - the specific event that initiates the workflow",
    "owner_and_participants": (
        'object with "owner" (string) and "participants" (array of strings)'
    ),
    "inputs_data_required": "array of strings - inputs and data the process consumes",
    "systems_involved": (
        "array of strings - software, tools or physical systems used today "
        "(may be empty if genuinely none)"
    ),
    "current_process": "array of strings - the process as it runs today, in order",
    "bottlenecks_and_risks": "array of strings - delays, failure modes and risks",
    "recommended_improved_process": "array of strings - the improved process, in order",
    "ai_agent_steps": (
        "array of strings - steps of the improved process an AI agent could carry out"
    ),
    "human_approvals_controls": (
        "array of strings - approvals and controls that must stay with a human"
    ),
}


class SchemaError(ValueError):
    """Raised when an object does not satisfy the workflow schema."""


def validate(obj: Any, *, strict_nonempty: bool = True) -> list[str]:
    """Return a list of human-readable violations. Empty list means valid.

    Returns rather than raises so callers can aggregate across a dataset;
    `validate_or_raise` is the fail-loudly wrapper used in pipeline code.
    """
    errs: list[str] = []

    if not isinstance(obj, dict):
        return [f"top level is {type(obj).__name__}, expected object"]

    missing = [f for f in FIELDS if f not in obj]
    if missing:
        errs.append(f"missing fields: {sorted(missing)}")
    extra = [k for k in obj if k not in FIELDS]
    if extra:
        errs.append(f"unexpected fields: {sorted(extra)}")

    for f in STR_FIELDS:
        v = obj.get(f)
        if f in obj and not isinstance(v, str):
            errs.append(f"{f}: expected string, got {type(v).__name__}")
        elif strict_nonempty and isinstance(v, str) and not v.strip():
            errs.append(f"{f}: empty string")

    for f in OBJ_FIELDS:
        if f not in obj:
            continue
        v = obj[f]
        if not isinstance(v, dict):
            errs.append(f"{f}: expected object, got {type(v).__name__}")
            continue
        if not isinstance(v.get("owner"), str):
            errs.append(f"{f}.owner: expected string")
        elif strict_nonempty and not v["owner"].strip():
            errs.append(f"{f}.owner: empty string")
        parts = v.get("participants")
        if not isinstance(parts, list) or not all(isinstance(p, str) for p in parts):
            errs.append(f"{f}.participants: expected array of strings")
        for k in v:
            if k not in ("owner", "participants"):
                errs.append(f"{f}: unexpected key {k!r}")

    for f in LIST_FIELDS:
        if f not in obj:
            continue
        v = obj[f]
        if not isinstance(v, list):
            errs.append(f"{f}: expected array, got {type(v).__name__}")
            continue
        if not all(isinstance(x, str) for x in v):
            errs.append(f"{f}: expected array of strings")
            continue
        if any(not x.strip() for x in v):
            errs.append(f"{f}: contains empty string item")
        if strict_nonempty and not v and f not in EMPTY_ALLOWED:
            errs.append(f"{f}: empty array")

    return errs


def validate_or_raise(obj: Any, *, where: str = "", strict_nonempty: bool = True) -> None:
    errs = validate(obj, strict_nonempty=strict_nonempty)
    if errs:
        prefix = f"{where}: " if where else ""
        raise SchemaError(prefix + "; ".join(errs))


def field_presence(obj: Any) -> dict[str, bool]:
    """Per-field 'present and non-empty' flags, for the structural eval layer.

    Tolerant of malformed objects by design: this scores model output, which
    may be arbitrarily broken, and must never raise.
    """
    out: dict[str, bool] = {}
    for f in FIELDS:
        v = obj.get(f) if isinstance(obj, dict) else None
        if f in STR_FIELDS:
            out[f] = isinstance(v, str) and bool(v.strip())
        elif f in OBJ_FIELDS:
            out[f] = (
                isinstance(v, dict)
                and isinstance(v.get("owner"), str)
                and bool(v["owner"].strip())
            )
        else:
            ok = isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)
            out[f] = ok and (bool(v) or f in EMPTY_ALLOWED)
    return out


def schema_block() -> str:
    """The schema as presented inside the prompt."""
    lines = [f'  "{f}": {FIELD_SPEC[f]}' for f in FIELDS]
    return "{\n" + ",\n".join(lines) + "\n}"
