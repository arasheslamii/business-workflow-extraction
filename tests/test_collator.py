"""Guards the completion-only masking.

A masking bug produces a training run that looks completely healthy - loss
falls, adapter saves - while optimising the wrong objective. These tests are
the only thing standing between that and a wasted GPU run, so they use the REAL
tokenizer rather than a mock.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.modeling.collator import (  # noqa: E402
    IGNORE_INDEX,
    MaskingError,
    PadCollator,
    encode_example,
)
from nextverse.prompts.task import target_json  # noqa: E402

transformers = pytest.importorskip("transformers")


@pytest.fixture(scope="module")
def tok():
    cfg = Config.load()
    t = transformers.AutoTokenizer.from_pretrained(
        cfg.get("model.name"), local_files_only=False
    )
    if t.pad_token is None:
        t.pad_token = t.eos_token
    return t


@pytest.fixture(scope="module")
def record():
    cfg = Config.load()
    p = cfg.path("paths.raw") / "train.jsonl"
    return json.loads(p.read_text().splitlines()[0])


def test_supervised_span_decodes_to_exactly_the_target(tok, record):
    """The unmasked tokens must decode to the JSON target and nothing else.

    This is the assertion that actually proves the objective is right: not
    'some tokens are masked', but 'the supervised region IS the answer'.
    """
    ex = encode_example(record, tok, 4096)
    sup = [i for i, l in enumerate(ex["labels"]) if l != IGNORE_INDEX]
    text = tok.decode([ex["input_ids"][i] for i in sup], skip_special_tokens=True)
    assert text.strip() == target_json(record["gold"]).strip()


def test_mask_is_a_contiguous_prefix(tok, record):
    """Masked tokens must be exactly the leading prompt - no holes."""
    ex = encode_example(record, tok, 4096)
    labels = ex["labels"]
    first_sup = next(i for i, l in enumerate(labels) if l != IGNORE_INDEX)
    assert all(l == IGNORE_INDEX for l in labels[:first_sup])
    assert all(l != IGNORE_INDEX for l in labels[first_sup:])
    assert first_sup > 50, "prompt suspiciously short - template may not have applied"


def test_labels_align_with_input_ids(tok, record):
    ex = encode_example(record, tok, 4096)
    assert len(ex["labels"]) == len(ex["input_ids"])
    for i, l in enumerate(ex["labels"]):
        if l != IGNORE_INDEX:
            assert l == ex["input_ids"][i], "labels must not be shifted by hand"


def test_prompt_text_is_not_supervised(tok, record):
    """The business description must never appear in the supervised span."""
    ex = encode_example(record, tok, 4096)
    sup = [ex["input_ids"][i] for i, l in enumerate(ex["labels"]) if l != IGNORE_INDEX]
    text = tok.decode(sup, skip_special_tokens=True)
    probe = " ".join(record["input"].split()[:8])
    assert probe not in text


def test_eos_is_supervised(tok, record):
    """The model must learn to STOP; if EOS is masked it will ramble forever."""
    ex = encode_example(record, tok, 4096)
    assert ex["input_ids"][-1] == tok.eos_token_id
    assert ex["labels"][-1] != IGNORE_INDEX


def test_overlength_raises_rather_than_truncating(tok, record):
    with pytest.raises(MaskingError, match="exceeds max_seq_len_train"):
        encode_example(record, tok, 64)


def test_collator_pads_labels_with_ignore_index():
    coll = PadCollator(pad_token_id=0)
    batch = coll([
        {"input_ids": [1, 2, 3], "labels": [IGNORE_INDEX, 2, 3]},
        {"input_ids": [4, 5], "labels": [IGNORE_INDEX, 5]},
    ])
    assert batch["input_ids"].shape == (2, 3)
    assert batch["labels"][1].tolist() == [IGNORE_INDEX, 5, IGNORE_INDEX]
    assert batch["attention_mask"][1].tolist() == [1, 1, 0]


def test_every_train_record_encodes(tok):
    """Whole-corpus check: no record fails masking or exceeds the limit."""
    cfg = Config.load()
    max_len = cfg.get("model.max_seq_len_train")
    raw = cfg.path("paths.raw")
    n = 0
    for split in ("train", "dev"):
        for line in (raw / f"{split}.jsonl").read_text().splitlines():
            if line.strip():
                encode_example(json.loads(line), tok, max_len)
                n += 1
    assert n == 132
