"""THE task prompt. One definition, used by baseline inference, training and
tuned inference alike.

Duplicating this string anywhere else is the most likely way to accidentally
train and evaluate on different formats, so every caller imports from here.
"""

from __future__ import annotations

import json
from typing import Any

from ..schema import FIELDS, schema_block

SYSTEM = (
    "You are an operations analyst. You read descriptions of how a small "
    "business currently runs a process and turn them into a structured "
    "workflow analysis."
)

_INSTRUCTIONS = """\
Analyse the business process description below and return a workflow analysis.

Return ONLY a single JSON object with exactly these {n} keys, in this order:

{schema}

Rules:
- Ground every field in the description. Do not invent systems, people or \
volumes that are not stated or clearly implied.
- "current_process" describes only what happens today, including any manual or \
inefficient steps.
- "recommended_improved_process" may propose new tools and steps; this is where \
improvements belong, not in "current_process".
- "ai_agent_steps" must refer to steps of the recommended improved process.
- Where the description is vague or contradictory, choose the most reasonable \
reading rather than leaving a field empty.
- Output raw JSON only. No markdown fences, no commentary.

### BUSINESS PROCESS DESCRIPTION
{description}
### END DESCRIPTION"""


def _instructions(description: str) -> str:
    return _INSTRUCTIONS.format(
        n=len(FIELDS), schema=schema_block(), description=description.strip()
    )


def target_json(gold: dict[str, Any]) -> str:
    """Canonical serialisation of a gold answer.

    Key order is forced to schema order and separators are compact-but-readable.
    Used as the training target and as the few-shot exemplar answer, so the
    model sees exactly one JSON style throughout.
    """
    ordered = {f: gold[f] for f in FIELDS}
    return json.dumps(ordered, ensure_ascii=False, indent=2)


def build_messages(
    description: str, shots: list[dict[str, Any]] | None = None
) -> list[dict[str, str]]:
    """Chat messages for one example.

    `shots` are full records (with 'input' and 'gold') rendered as prior turns.
    Few-shot exemplars are presented as real conversation turns rather than
    pasted into the system prompt, which matches how the model was instruction
    tuned and keeps the zero-shot and few-shot arms textually identical apart
    from the extra turns.
    """
    msgs: list[dict[str, str]] = [{"role": "system", "content": SYSTEM}]
    for s in shots or []:
        msgs.append({"role": "user", "content": _instructions(s["input"])})
        msgs.append({"role": "assistant", "content": target_json(s["gold"])})
    msgs.append({"role": "user", "content": _instructions(description)})
    return msgs
