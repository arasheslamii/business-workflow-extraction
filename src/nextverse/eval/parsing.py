"""JSON extraction from raw model output.

CRITICAL FAIRNESS PROPERTY: every evaluation arm (base zero-shot, base few-shot,
tuned) goes through this exact function. Applying repair selectively to one arm
would manufacture the result we are trying to measure.

We report two parse rates:
  strict  - json.loads on the raw string succeeds (model emitted clean JSON)
  lenient - succeeds after fence-stripping and balanced-brace extraction
The gap between them is itself a finding: it is the share of the fine-tuning
effect that is purely formatting discipline rather than content quality.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class ParseResult:
    ok: bool
    strict_ok: bool
    obj: Any | None
    method: str  # how it parsed: strict | fenced | braces | failed
    error: str | None = None


def _balanced_object(text: str) -> str | None:
    """Extract the first brace-balanced object, ignoring braces inside strings.

    A regex cannot do this correctly for nested objects, and our schema has a
    nested object (owner_and_participants), so we scan properly.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse(raw: str) -> ParseResult:
    if raw is None:
        return ParseResult(False, False, None, "failed", "output was None")

    stripped = raw.strip()

    # 1. Strict: the model emitted nothing but JSON.
    try:
        return ParseResult(True, True, json.loads(stripped), "strict")
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. A fenced code block, the most common instruct-model wrapper.
    m = _FENCE.search(stripped)
    if m:
        try:
            return ParseResult(True, False, json.loads(m.group(1).strip()), "fenced")
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. Prose preamble/postamble around a JSON object.
    cand = _balanced_object(stripped)
    if cand is not None:
        try:
            return ParseResult(True, False, json.loads(cand), "braces")
        except (json.JSONDecodeError, ValueError) as e:
            return ParseResult(False, False, None, "failed", f"braces: {e}")

    return ParseResult(False, False, None, "failed", "no JSON object found")
