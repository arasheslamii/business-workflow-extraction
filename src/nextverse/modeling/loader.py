"""Model + tokenizer loading, shared by baseline and tuned inference."""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model_and_tokenizer(
    name: str,
    *,
    dtype: str = "bfloat16",
    load_in_4bit: bool = False,
    adapter_path: str | Path | None = None,
    local_files_only: bool | None = None,
):
    """Load base model, optionally applying a LoRA adapter.

    local_files_only=None means "decide from the environment": offline only if
    the caller exported HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE. Defaulting to True
    would break a first run on a fresh machine, where the weights legitimately
    need downloading.
    """
    if local_files_only is None:
        from ..env import local_files_only as _lfo

        local_files_only = _lfo()
    torch_dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}.get(
        dtype, torch.float32
    )

    tok = AutoTokenizer.from_pretrained(name, local_files_only=local_files_only)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # Decoder-only generation requires left padding for correct positions.
    tok.padding_side = "left"

    kwargs = {"torch_dtype": torch_dtype, "local_files_only": local_files_only}
    if load_in_4bit:
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch_dtype,
            bnb_4bit_use_double_quant=True,
        )
        # Required: a quantized model cannot be moved with .to(), so placement
        # must happen at load time or the weights silently stay on CPU.
        kwargs["device_map"] = {"": 0}

    model = AutoModelForCausalLM.from_pretrained(name, **kwargs)
    if not load_in_4bit:
        model = model.to("cuda")

    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))

    model.eval()
    return model, tok
