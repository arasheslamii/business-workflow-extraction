#!/usr/bin/env python3
"""Run an inference arm over the eval splits. Requires a CUDA GPU.

Arms:
  zeroshot  - base model, schema in prompt, no examples
  fewshot   - base model, same prompt + 2 in-context examples from TRAIN
  tuned     - base model + LoRA adapter (Stage 3), same prompt as zeroshot

The fewshot arm exists because a zero-shot 1.5B will fail mostly on JSON
formatting; without it, the headline before/after result is "fine-tuning taught
the model to stop writing markdown fences", which is true but uninteresting.
The fewshot arm closes most of the formatting gap, so any remaining tuned
advantage is a claim about content.

Usage:
  python scripts/03_run_base.py --arm zeroshot
  python scripts/03_run_base.py --arm fewshot
  python scripts/03_run_base.py --arm tuned --adapter results/adapter
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Applied before torch/transformers import so HF_HOME and the cuBLAS
# determinism flag take effect. Makes the scripts runnable standalone.
from nextverse.env import apply_defaults  # noqa: E402

apply_defaults()

from nextverse.config import Config  # noqa: E402
from nextverse.data.loading import load_split, pick_shots  # noqa: E402
from nextverse.eval.parsing import parse  # noqa: E402
from nextverse.prompts.task import build_messages  # noqa: E402
from nextverse.schema import validate  # noqa: E402
from nextverse.seeding import set_seed  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["zeroshot", "fewshot", "tuned"])
    ap.add_argument("--adapter", default=None, help="LoRA adapter dir (tuned arm)")
    ap.add_argument("--config", default=None)
    ap.add_argument("--limit", type=int, default=None, help="smoke-test on N records")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = Config.load(args.config)
    set_seed(cfg.get("seed"))

    if args.arm == "tuned" and not args.adapter:
        raise SystemExit("--adapter is required for the tuned arm")

    raw = cfg.path("paths.raw")
    out_dir = Path(args.out) if args.out else cfg.path("paths.results") / f"base_{args.arm}"
    if args.arm == "tuned":
        out_dir = Path(args.out) if args.out else cfg.path("paths.results") / "tuned"
    out_dir.mkdir(parents=True, exist_ok=True)

    shots = pick_shots(load_split(raw, "train"), cfg.get("fewshot.n_shots")) \
        if args.arm == "fewshot" else None
    if shots:
        print(f"few-shot exemplars: {[s['id'] for s in shots]}", flush=True)

    # Imported late so --help works on a machine without torch installed.
    import torch
    from nextverse.modeling.loader import load_model_and_tokenizer

    if not torch.cuda.is_available():
        raise SystemExit(
            "no CUDA device visible. This script needs a CUDA GPU "
            "(>=8GB VRAM for the default bf16 1.5B + LoRA configuration)."
        )
    print(f"device: {torch.cuda.get_device_name(0)}", flush=True)

    model, tok = load_model_and_tokenizer(
        cfg.get("model.name"),
        dtype=cfg.get("model.dtype"),
        load_in_4bit=cfg.get("model.load_in_4bit"),
        adapter_path=args.adapter,
    )

    max_ctx = cfg.get("model.max_seq_len_infer")
    max_new = cfg.get("inference.max_new_tokens")
    summary: dict[str, dict] = {}

    for split in cfg.get("eval.splits"):
        recs = load_split(raw, split)
        if args.limit:
            recs = recs[: args.limit]
        rows, t0 = [], time.time()

        for i, r in enumerate(recs, 1):
            msgs = build_messages(r["input"], shots)
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            # add_special_tokens=False: the chat template has already inserted
            # every control token. Letting the tokenizer add its own on top
            # would prepend a spurious token and shift the whole sequence.
            enc = tok(text, return_tensors="pt", add_special_tokens=False)
            n_in = enc.input_ids.shape[1]

            # Fail loudly rather than silently truncating a prompt: a truncated
            # prompt would quietly corrupt this arm's results.
            if n_in + max_new > max_ctx:
                raise SystemExit(
                    f"{r['id']}: prompt {n_in} + max_new {max_new} exceeds context "
                    f"{max_ctx}. Raise model.max_seq_len_infer in config.yaml."
                )

            enc = {k: v.to(model.device) for k, v in enc.items()}
            with torch.no_grad():
                out = model.generate(
                    **enc,
                    max_new_tokens=max_new,
                    do_sample=cfg.get("inference.do_sample"),
                    pad_token_id=tok.pad_token_id,
                )
            gen = tok.decode(out[0][n_in:], skip_special_tokens=True)

            pr = parse(gen)
            rows.append(
                {
                    "id": r["id"],
                    "split": split,
                    "arm": args.arm,
                    "vertical": r["vertical"],
                    "difficulty": r["difficulty"],
                    "ood_vertical": r["ood_vertical"],
                    "source": r["source"],
                    "prompt_tokens": n_in,
                    "gen_tokens": int(out.shape[1] - n_in),
                    "raw_output": gen,
                    "parse_ok": pr.ok,
                    "parse_strict_ok": pr.strict_ok,
                    "parse_method": pr.method,
                    "parse_error": pr.error,
                    "schema_errors": validate(pr.obj) if pr.ok else ["unparseable"],
                }
            )
            if i % 5 == 0 or i == len(recs):
                el = time.time() - t0
                print(
                    f"  {split} {i}/{len(recs)}  {el:.0f}s  ({el / i:.1f}s/ex)", flush=True
                )

        path = out_dir / f"{split}.jsonl"
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        n = len(rows)
        summary[split] = {
            "n": n,
            "strict_json_rate": sum(r["parse_strict_ok"] for r in rows) / n,
            "lenient_json_rate": sum(r["parse_ok"] for r in rows) / n,
            "schema_valid_rate": sum(not r["schema_errors"] for r in rows) / n,
            "mean_prompt_tokens": sum(r["prompt_tokens"] for r in rows) / n,
            "mean_gen_tokens": sum(r["gen_tokens"] for r in rows) / n,
            "seconds": round(time.time() - t0, 1),
        }
        print(f"  -> {path}", flush=True)

    meta = {
        "arm": args.arm,
        "model": cfg.get("model.name"),
        "adapter": args.adapter,
        "load_in_4bit": cfg.get("model.load_in_4bit"),
        "seed": cfg.get("seed"),
        "greedy": not cfg.get("inference.do_sample"),
        "shots": [s["id"] for s in shots] if shots else [],
        "summary": summary,
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== " + args.arm + " ===")
    for split, s in summary.items():
        print(
            f"{split:16s} n={s['n']:3d}  strict={s['strict_json_rate']:.0%}  "
            f"lenient={s['lenient_json_rate']:.0%}  schema={s['schema_valid_rate']:.0%}  "
            f"{s['seconds']:.0f}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
