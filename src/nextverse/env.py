"""Environment defaults applied by every entrypoint script.

The scripts must run standalone with a plain `python scripts/NN_*.py` on any
machine with a GPU. Previously the only place these were set was the SLURM
wrapper, which made the wrapper load-bearing rather than a convenience.

Nothing here is forced: every value defers to what the caller already exported.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def apply_defaults(*, offline: bool | None = None) -> None:
    """Set env defaults if the caller has not already chosen them.

    offline=None (default) means "leave HF online behaviour alone": on a fresh
    machine the model must be downloadable. Cluster users who need offline mode
    export HF_HUB_OFFLINE=1 themselves, or use slurm/run_gpu.sh which does.
    """
    # Project-local HF cache, so weights land next to the repo rather than in
    # the user's home. Respect an existing HF_HOME.
    os.environ.setdefault("HF_HOME", str(ROOT / ".hf_cache"))

    # Silences a tokenizers fork warning; harmless everywhere.
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    # Required for deterministic cuBLAS reductions; must be set before torch
    # initialises CUDA, which is why this runs at import time in the scripts.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

    if offline:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def local_files_only() -> bool:
    """Whether model loading should refuse network access.

    True only when the caller asked for offline mode. Defaulting to True (as an
    earlier version did) breaks a first run on a fresh machine, where the
    weights legitimately need downloading.
    """
    return os.environ.get("HF_HUB_OFFLINE") == "1" or os.environ.get(
        "TRANSFORMERS_OFFLINE"
    ) == "1"
