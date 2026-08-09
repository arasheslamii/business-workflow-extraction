#!/usr/bin/env python3
"""Verify the sequence-length budget with the REAL tokenizer. Login node (CPU).

scripts/02_verify_data.py can only estimate token counts from character length.
This confirms them, because getting max_seq_len_train wrong silently truncates
the JSON target off the end of training examples - which would produce a model
that never learns to close its output, with no error anywhere in the logs.

Exits 1 if the configured lengths would truncate anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.data.loading import load_split, pick_shots  # noqa: E402
from nextverse.prompts.task import build_messages, target_json  # noqa: E402


def main() -> int:
    cfg = Config.load()
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(cfg.get("model.name"), local_files_only=True)
    raw = cfg.path("paths.raw")

    def ntok(s: str) -> int:
        return len(tok(s, add_special_tokens=False).input_ids)

    train = load_split(raw, "train")
    shots = pick_shots(train, cfg.get("fewshot.n_shots"))
    print(f"few-shot exemplars: {[s['id'] for s in shots]}")

    max_train = cfg.get("model.max_seq_len_train")
    max_infer = cfg.get("model.max_seq_len_infer")
    max_new = cfg.get("inference.max_new_tokens")
    bad = 0

    # --- training sequences (prompt + target must both fit) ---
    print(f"\n== train (max_seq_len_train = {max_train}) ==")
    lens = []
    for r in train + load_split(raw, "dev"):
        p = tok.apply_chat_template(
            build_messages(r["input"]), tokenize=False, add_generation_prompt=True
        )
        total = ntok(p) + ntok(target_json(r["gold"]))
        lens.append((total, r["id"]))
    lens.sort()
    over = [i for t, i in lens if t > max_train]
    print(f"  median {lens[len(lens) // 2][0]}  max {lens[-1][0]} ({lens[-1][1]})")
    print(f"  would truncate: {len(over)}/{len(lens)}")
    if over:
        bad = 1
        print(f"  FAIL - raise model.max_seq_len_train above {lens[-1][0]}: {over[:5]}")

    # --- inference prompts (prompt + max_new_tokens must fit) ---
    for arm, sh in (("zeroshot", None), ("fewshot", shots)):
        print(f"\n== infer/{arm} (max_seq_len_infer = {max_infer}, max_new = {max_new}) ==")
        for split in cfg.get("eval.splits"):
            ps = []
            for r in load_split(raw, split):
                p = tok.apply_chat_template(
                    build_messages(r["input"], sh), tokenize=False, add_generation_prompt=True
                )
                ps.append((ntok(p), r["id"]))
            ps.sort()
            worst, wid = ps[-1]
            need = worst + max_new
            flag = "OK" if need <= max_infer else "FAIL"
            if need > max_infer:
                bad = 1
            print(
                f"  {split:16s} max prompt {worst:5d} ({wid})  + {max_new} = {need:5d}  {flag}"
            )

    print("\nRESULT:", "FAIL" if bad else "PASS")
    return bad


if __name__ == "__main__":
    sys.exit(main())
