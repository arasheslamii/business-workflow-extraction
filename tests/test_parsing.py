import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nextverse.eval.parsing import parse  # noqa: E402
from nextverse.schema import FIELDS, validate  # noqa: E402

GOOD = {
    "objective": "o",
    "trigger": "t",
    "owner_and_participants": {"owner": "x", "participants": ["a"]},
    "inputs_data_required": ["a"],
    "systems_involved": ["s"],
    "current_process": ["a"],
    "bottlenecks_and_risks": ["a"],
    "recommended_improved_process": ["a"],
    "ai_agent_steps": ["a"],
    "human_approvals_controls": ["a"],
}


def test_strict_parse():
    r = parse(json.dumps(GOOD))
    assert r.ok and r.strict_ok and r.method == "strict"


def test_fenced_is_lenient_not_strict():
    r = parse("```json\n" + json.dumps(GOOD) + "\n```")
    assert r.ok and not r.strict_ok and r.method == "fenced"


def test_prose_preamble():
    r = parse("Sure! Here is the analysis:\n" + json.dumps(GOOD) + "\nHope that helps.")
    assert r.ok and not r.strict_ok and r.obj == GOOD


def test_nested_braces_not_truncated():
    """A regex-based extractor would stop at the first '}' inside the nested
    owner_and_participants object. Guards against that regression."""
    r = parse("text before " + json.dumps(GOOD) + " text after")
    assert r.ok and set(r.obj) == set(FIELDS)


def test_braces_inside_strings():
    d = dict(GOOD, objective="uses {curly} braces")
    r = parse("noise " + json.dumps(d))
    assert r.ok and r.obj["objective"] == "uses {curly} braces"


def test_unparseable():
    r = parse("I cannot help with that.")
    assert not r.ok and r.obj is None


def test_schema_accepts_gold():
    assert validate(GOOD) == []


def test_schema_rejects_missing_and_wrong_types():
    assert validate({k: v for k, v in GOOD.items() if k != "trigger"})
    assert validate(dict(GOOD, current_process="not a list"))
    assert validate(dict(GOOD, owner_and_participants={"owner": "x"}))


def test_empty_systems_allowed_but_empty_process_not():
    assert validate(dict(GOOD, systems_involved=[])) == []
    assert validate(dict(GOOD, current_process=[]))
