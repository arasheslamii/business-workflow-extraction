#!/usr/bin/env python3
"""Publish the dataset and the LoRA adapter to the Hugging Face Hub.

Idempotent: re-running uploads only what changed and rewrites the cards. Safe to
run repeatedly.

Authentication (either):
    huggingface-cli login          # interactive, stores a token
    export HF_TOKEN=hf_...         # non-interactive

Usage:
    python scripts/10_publish_hf.py --dry-run        # render cards locally, no upload
    python scripts/10_publish_hf.py --dataset
    python scripts/10_publish_hf.py --model
    python scripts/10_publish_hf.py --dataset --model
    python scripts/10_publish_hf.py --dataset --private
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nextverse.config import Config  # noqa: E402
from nextverse.hf_cards import dataset_card, model_card  # noqa: E402

HF_USER = "ArashEslam"
DATASET_REPO = f"{HF_USER}/business-workflow-extraction"
MODEL_REPO = f"{HF_USER}/qwen2.5-1.5b-workflow-lora"

DATASET_FILES = [
    "train.jsonl",
    "dev.jsonl",
    "eval_synthetic.jsonl",
    "eval_pet.jsonl",
    "data_manifest.json",
]
# Adapter weights + tokenizer. Explicit allow-list rather than uploading the
# directory wholesale, so training logs and any stray checkpoint dir never leak
# into a published model repo.
MODEL_FILES = [
    "adapter_config.json",
    "adapter_model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.json",
    "merges.txt",
    "train_log.json",
    "train_meta.json",
]


def _api():
    from huggingface_hub import HfApi

    api = HfApi()
    try:
        who = api.whoami()
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            "Not authenticated with Hugging Face. Run `huggingface-cli login` "
            f"or export HF_TOKEN. ({e})"
        ) from e
    print(f"authenticated as: {who.get('name', '?')}")
    return api


def publish_dataset(cfg: Config, *, dry_run: bool, private: bool) -> None:
    raw = cfg.path("paths.raw")
    missing = [f for f in DATASET_FILES if not (raw / f).exists()]
    if missing:
        raise SystemExit(f"missing dataset files: {missing}")

    card = dataset_card(raw)
    out = ROOT / "results" / "hf_dataset_card.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(card)
    print(f"rendered dataset card -> {out} ({len(card.split())} words)")

    if dry_run:
        print("dry run: not uploading")
        return

    api = _api()
    api.create_repo(DATASET_REPO, repo_type="dataset", exist_ok=True, private=private)

    for f in DATASET_FILES:
        api.upload_file(
            path_or_fileobj=str(raw / f),
            path_in_repo=f"data/{f}",
            repo_id=DATASET_REPO,
            repo_type="dataset",
        )
        print(f"  uploaded data/{f}")

    api.upload_file(
        path_or_fileobj=card.encode(),
        path_in_repo="README.md",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    print(f"  uploaded README.md\nhttps://huggingface.co/datasets/{DATASET_REPO}")


def publish_model(cfg: Config, *, dry_run: bool, private: bool) -> None:
    adapter = cfg.path("train.adapter_dir")
    if not adapter.exists():
        raise SystemExit(f"adapter not found at {adapter} - run scripts/04_train.py")

    stray = [p.name for p in adapter.iterdir() if p.is_dir()]
    if stray:
        raise SystemExit(
            f"{adapter} contains subdirectories {stray}. Remove them before "
            "publishing so the model repo holds exactly one adapter."
        )
    present = [f for f in MODEL_FILES if (adapter / f).exists()]
    if "adapter_model.safetensors" not in present:
        raise SystemExit("adapter_model.safetensors missing - nothing to publish")

    card = model_card(ROOT, DATASET_REPO)
    out = ROOT / "results" / "hf_model_card.md"
    out.write_text(card)
    print(f"rendered model card -> {out} ({len(card.split())} words)")

    if dry_run:
        print(f"dry run: not uploading ({len(present)} files would go up)")
        return

    api = _api()
    api.create_repo(MODEL_REPO, repo_type="model", exist_ok=True, private=private)

    for f in present:
        api.upload_file(
            path_or_fileobj=str(adapter / f),
            path_in_repo=f,
            repo_id=MODEL_REPO,
            repo_type="model",
        )
        print(f"  uploaded {f}")

    api.upload_file(
        path_or_fileobj=card.encode(),
        path_in_repo="README.md",
        repo_id=MODEL_REPO,
        repo_type="model",
    )
    print(f"  uploaded README.md\nhttps://huggingface.co/{MODEL_REPO}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", action="store_true")
    ap.add_argument("--model", action="store_true")
    ap.add_argument("--private", action="store_true", help="create repos private")
    ap.add_argument("--dry-run", action="store_true", help="render cards, upload nothing")
    args = ap.parse_args()
    if not (args.dataset or args.model):
        raise SystemExit("choose --dataset and/or --model")

    cfg = Config.load()
    if args.dataset:
        print("== dataset ==")
        publish_dataset(cfg, dry_run=args.dry_run, private=args.private)
    if args.model:
        print("\n== model ==")
        publish_model(cfg, dry_run=args.dry_run, private=args.private)
    return 0


if __name__ == "__main__":
    sys.exit(main())
