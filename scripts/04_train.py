#!/usr/bin/env python3
"""LoRA fine-tune on the workflow-extraction task (bf16 by default;
4-bit QLoRA path available via model.load_in_4bit). Requires a CUDA GPU.

Trains on train.jsonl, evaluates dev.jsonl each epoch. Loss is computed on the
assistant turn only (see modeling/collator.py).

Usage:  python scripts/04_train.py
        python scripts/04_train.py --dry-run   # tokenise + mask check, no GPU
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Applied before torch/transformers import so HF_HOME and the cuBLAS
# determinism flag take effect. Makes the scripts runnable standalone.
from nextverse.env import apply_defaults, local_files_only  # noqa: E402

apply_defaults()

from nextverse.config import Config  # noqa: E402
from nextverse.data.loading import load_split  # noqa: E402
from nextverse.seeding import set_seed  # noqa: E402


class ListDataset:
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dry-run", action="store_true", help="tokenise only, no training")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    set_seed(cfg.get("seed"))

    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        cfg.get("model.name"), local_files_only=local_files_only()
    )
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"  # training pads right; only generation needs left

    from nextverse.modeling.collator import PadCollator, encode_example

    raw = cfg.path("paths.raw")
    max_len = cfg.get("model.max_seq_len_train")

    # Encoding raises on any masking or length problem, so a bad example stops
    # the run here rather than quietly degrading it.
    train_rows = [encode_example(r, tok, max_len) for r in load_split(raw, "train")]
    dev_rows = [encode_example(r, tok, max_len) for r in load_split(raw, "dev")]

    lens = sorted(len(r["input_ids"]) for r in train_rows)
    sup = sorted(sum(1 for x in r["labels"] if x != -100) for r in train_rows)
    print(f"train {len(train_rows)} | dev {len(dev_rows)}")
    print(f"  seq len   median {lens[len(lens) // 2]}  max {lens[-1]}  (limit {max_len})")
    print(f"  supervised tokens median {sup[len(sup) // 2]}  min {sup[0]}  max {sup[-1]}")

    bs = cfg.get("train.per_device_batch_size")
    ga = cfg.get("train.grad_accum")
    ep = cfg.get("train.epochs")
    steps_per_epoch = len(train_rows) // (bs * ga)
    print(f"  optimizer steps: {steps_per_epoch}/epoch x {ep} epochs = {steps_per_epoch * ep}")

    if args.dry_run:
        print("\ndry run OK - masking and lengths verified, no training performed")
        return 0

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import Trainer, TrainingArguments

    from nextverse.modeling.loader import load_model_and_tokenizer

    if not torch.cuda.is_available():
        raise SystemExit(
            "no CUDA device visible. This script needs a CUDA GPU "
            "(>=8GB VRAM for the default bf16 1.5B + LoRA configuration)."
        )

    model, _ = load_model_and_tokenizer(
        cfg.get("model.name"),
        dtype=cfg.get("model.dtype"),
        load_in_4bit=cfg.get("model.load_in_4bit"),
    )
    model.train()
    model.config.use_cache = False  # incompatible with gradient checkpointing

    if cfg.get("model.load_in_4bit"):
        from peft import prepare_model_for_kbit_training

        model = prepare_model_for_kbit_training(model)

    lora = LoraConfig(
        r=cfg.get("train.lora_r"),
        lora_alpha=cfg.get("train.lora_alpha"),
        lora_dropout=cfg.get("train.lora_dropout"),
        target_modules=list(cfg.get("train.target_modules")),
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    if cfg.get("train.gradient_checkpointing"):
        # Required with PEFT + checkpointing, otherwise no grad reaches the
        # adapters through the frozen embedding layer.
        model.enable_input_require_grads()

    out_dir = cfg.path("train.adapter_dir")
    targs = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=ep,
        per_device_train_batch_size=bs,
        per_device_eval_batch_size=bs,
        gradient_accumulation_steps=ga,
        learning_rate=float(cfg.get("train.lr")),
        lr_scheduler_type=cfg.get("train.scheduler"),
        warmup_ratio=cfg.get("train.warmup_ratio"),
        gradient_checkpointing=cfg.get("train.gradient_checkpointing"),
        bf16=cfg.get("model.dtype") == "bfloat16",
        logging_steps=cfg.get("train.logging_steps"),
        eval_strategy=cfg.get("train.eval_strategy"),
        save_strategy=cfg.get("train.save_strategy"),
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to=[],
        seed=cfg.get("seed"),
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=ListDataset(train_rows),
        eval_dataset=ListDataset(dev_rows),
        data_collator=PadCollator(tok.pad_token_id),
    )
    trainer.train()

    model.save_pretrained(str(out_dir))
    tok.save_pretrained(str(out_dir))

    hist = [h for h in trainer.state.log_history]
    (out_dir / "train_log.json").write_text(json.dumps(hist, indent=2))
    (out_dir / "train_meta.json").write_text(
        json.dumps(
            {
                "model": cfg.get("model.name"),
                "load_in_4bit": cfg.get("model.load_in_4bit"),
                "seed": cfg.get("seed"),
                "n_train": len(train_rows),
                "n_dev": len(dev_rows),
                "optimizer_steps": steps_per_epoch * ep,
                "config": cfg.get("train"),
            },
            indent=2,
            default=str,
        )
    )

    print("\n=== dev loss by epoch ===")
    for h in hist:
        if "eval_loss" in h:
            print(f"  epoch {h.get('epoch'):.2f}  eval_loss {h['eval_loss']:.4f}")
    print(f"\nadapter saved to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
