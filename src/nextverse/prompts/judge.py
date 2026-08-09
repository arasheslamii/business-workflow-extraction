"""Judge prompts: per-field rubric scoring and blinded pairwise comparison.

Bias controls built into the prompts themselves:
  - Length. Small models under-generate and judges reliably prefer longer
    answers, so the rubric explicitly instructs that length is not quality.
  - Position. Pairwise runs BOTH orders for every pair (see judge.py); the
    prompt additionally states that order carries no meaning.
  - Style. The gold answers were authored by a different frontier model, so a
    judge could reward house style over substance; the rubric anchors on
    grounding in the INPUT, not similarity to the reference.
"""

from __future__ import annotations

import json
from typing import Any

from ..schema import FIELDS, FIELD_SPEC

RUBRIC = """\
1 - absent, empty, or contradicts the description
2 - present but mostly wrong, vague or ungrounded
3 - broadly correct but incomplete or partly generic
4 - correct, grounded and reasonably complete
5 - correct, specific, complete, and clearly grounded in the description"""

_FIELD_PROMPT = """\
You are evaluating a structured workflow analysis produced from a description of \
how a small business runs a process.

Score EACH of the {n} fields from 1 to 5 using this rubric:
{rubric}

Scoring guidance:
- Judge grounding in the DESCRIPTION. Do not reward plausible-sounding detail \
that the description does not support.
- Longer is NOT better. Score a concise correct field the same as a verbose one.
- `recommended_improved_process` MAY propose tools and steps not in the \
description - that is the task, not a hallucination.
- `current_process` must describe only what happens TODAY.
- `ai_agent_steps` should refer to steps of the recommended improved process.

### DESCRIPTION
{description}

### ANALYSIS TO SCORE
{output}

Return ONLY a JSON object mapping each field name to an integer 1-5, plus a \
"notes" key with one sentence naming the weakest field:
{{{score_keys}, "notes": "..."}}"""

_PAIRWISE_PROMPT = """\
Two systems produced a structured workflow analysis from the same description \
of how a small business runs a process. Decide which analysis is better.

Judge on: grounding in the description, completeness across the 10 required \
fields, correctness of the as-is process, usefulness and specificity of the \
recommended improvements, and whether the AI-agent steps and human controls are \
sensible.

Important:
- Longer is NOT better. Do not prefer an analysis merely because it says more.
- The order of the two analyses is arbitrary and carries no information.
- Proposing new tools in `recommended_improved_process` is correct behaviour, \
not a fault.

### DESCRIPTION
{description}

### ANALYSIS 1
{a}

### ANALYSIS 2
{b}

Return ONLY a JSON object:
{{"winner": "1" | "2" | "tie", "reason": "one sentence"}}"""


def field_rubric_prompt(description: str, output: Any) -> str:
    keys = ", ".join(f'"{f}": <1-5>' for f in FIELDS)
    body = output if isinstance(output, str) else json.dumps(output, indent=2, ensure_ascii=False)
    return _FIELD_PROMPT.format(
        n=len(FIELDS),
        rubric=RUBRIC,
        description=description.strip(),
        output=body,
        score_keys=keys,
    )


def pairwise_prompt(description: str, a: Any, b: Any) -> str:
    def render(x):
        return x if isinstance(x, str) else json.dumps(x, indent=2, ensure_ascii=False)

    return _PAIRWISE_PROMPT.format(
        description=description.strip(), a=render(a), b=render(b)
    )


def field_spec_reference() -> str:
    return "\n".join(f"- {f}: {FIELD_SPEC[f]}" for f in FIELDS)
