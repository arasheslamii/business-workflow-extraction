"""Global seed control.

Note the honest limit: seeding makes sampling and data order reproducible, but
greedy decoding on GPU is still not bitwise reproducible across different batch
sizes, kernel selections or driver versions. We fix batch_size=1 and greedy
decoding for eval, and describe determinism as best-effort in the README rather
than claiming more than we can deliver.
"""

from __future__ import annotations

import os
import random


def set_seed(seed: int, *, deterministic_torch: bool = True) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic_torch:
            # Trades some throughput for run-to-run stability.
            os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
