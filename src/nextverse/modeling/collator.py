"""Completion-only tokenisation and collation.

The model must learn to WRITE the JSON, not to reproduce the instructions. So
loss is computed on the assistant turn only; every prompt token is masked to
-100.

This is the single most dangerous piece of code in the project: if the mask is
off by even a few tokens the run still trains, still reports a falling loss, and
still saves an adapter - it just learns the wrong objective. There is no runtime
symptom. Hence the prefix assertion below and tests/test_collator.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch

from ..prompts.task import build_messages, target_json

IGNORE_INDEX = -100


class MaskingError(RuntimeError):
    pass


def encode_example(
    record: dict[str, Any], tok, max_len: int
) -> dict[str, list[int]]:
    """Tokenise one record into input_ids + labels with the prompt masked.

    Strategy: render the prompt (with generation prefix) and the full sequence
    separately, then assert the prompt tokens are a genuine PREFIX of the full
    sequence. Slicing on a character offset or a token count alone would be
    silently wrong whenever the chat template merges tokens across the boundary.
    """
    msgs = build_messages(record["input"])
    prompt_text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    full_text = prompt_text + target_json(record["gold"]) + tok.eos_token

    # add_special_tokens=False: the chat template already inserted them.
    prompt_ids = tok(prompt_text, add_special_tokens=False).input_ids
    full_ids = tok(full_text, add_special_tokens=False).input_ids

    if full_ids[: len(prompt_ids)] != prompt_ids:
        raise MaskingError(
            f"{record.get('id')}: prompt tokens are not a prefix of the full sequence "
            "- the completion boundary cannot be located safely."
        )
    if len(full_ids) <= len(prompt_ids):
        raise MaskingError(f"{record.get('id')}: empty completion after tokenisation")

    # Truncating here would cut the tail of the JSON target - the model would
    # learn never to close its output, with no symptom in any log. Refuse
    # instead. Current data peaks at 1857 tokens against a 2560 limit, so this
    # never fires today; it exists so that longer future data fails loudly.
    if len(full_ids) > max_len:
        raise MaskingError(
            f"{record.get('id')}: sequence {len(full_ids)} exceeds max_seq_len_train "
            f"{max_len}. Raise it rather than truncating - truncation removes the "
            "end of the JSON target."
        )

    labels = [IGNORE_INDEX] * len(prompt_ids) + full_ids[len(prompt_ids) :]
    return {"input_ids": full_ids, "labels": labels}


@dataclass
class PadCollator:
    """Right-pads a batch. Labels pad with IGNORE_INDEX so padding never
    contributes to the loss."""

    pad_token_id: int

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, torch.Tensor]:
        n = max(len(f["input_ids"]) for f in features)
        input_ids, labels, attn = [], [], []
        for f in features:
            k = n - len(f["input_ids"])
            input_ids.append(f["input_ids"] + [self.pad_token_id] * k)
            labels.append(f["labels"] + [IGNORE_INDEX] * k)
            attn.append([1] * len(f["input_ids"]) + [0] * k)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(attn, dtype=torch.long),
        }
