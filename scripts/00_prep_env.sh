#!/usr/bin/env bash
# Builds the venv, downloads model weights into a project-local HF cache, and
# freezes an exact lock file.
#
# Run this on a machine WITH internet. It is separated from the GPU steps so that
# a training/inference machine without network access can still run the pipeline
# from the pre-populated cache.
#
#   bash scripts/00_prep_env.sh              # exact pins
#   bash scripts/00_prep_env.sh --flexible   # drop pins if a pin is unavailable
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"

FLEXIBLE=0
[[ "${1:-}" == "--flexible" ]] && FLEXIBLE=1

# Project-local HF cache. On a cluster, make sure this lives on a filesystem
# shared with the compute node - node-local scratch will not be visible there.
export HF_HOME="$ROOT/.hf_cache"
mkdir -p "$HF_HOME"

echo "== 1/5 venv =="
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --quiet --upgrade pip setuptools wheel

echo "== 2/5 torch =="
# CUDA 13.2 drivers run cu12x wheels (drivers are backward compatible with older
# CUDA runtimes). Override if this cluster needs a different build:
#   TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126 bash scripts/00_prep_env.sh
if [[ -n "${TORCH_INDEX_URL:-}" ]]; then
  python -m pip install torch --index-url "$TORCH_INDEX_URL"
else
  python -m pip install torch
fi

echo "== 3/5 python deps =="
if [[ $FLEXIBLE -eq 1 ]]; then
  sed 's/==.*//' requirements.txt     | grep -vE '^\s*(#|$)' > /tmp/req.cpu.txt
  sed 's/==.*//' requirements-gpu.txt | grep -vE '^\s*(#|$)' > /tmp/req.gpu.txt
  python -m pip install -r /tmp/req.cpu.txt -r /tmp/req.gpu.txt
else
  python -m pip install -r requirements.txt -r requirements-gpu.txt
fi

echo "== 4/5 model weights -> $HF_HOME =="
MODEL=$(python - <<'PY'
import yaml; print(yaml.safe_load(open("config.yaml"))["model"]["name"])
PY
)
python - <<PY
import os
from huggingface_hub import snapshot_download
p = snapshot_download("$MODEL", allow_patterns=[
    "*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*"])
print("cached at:", p)
PY

echo "== 5/5 lock file + token-length verification =="
python -m pip freeze > requirements.lock.txt
echo "wrote requirements.lock.txt"

# Re-checks with the REAL tokenizer the length budget that scripts/02 could only
# estimate from character counts. This is what justifies max_seq_len_train.
python scripts/01_check_lengths.py

echo
echo "Prep complete. Activate with:  source .venv/bin/activate"
echo "HF_HOME defaults to $ROOT/.hf_cache; scripts set it themselves."
