#!/usr/bin/env bash
# Runs a project command inside a GPU allocation on saxa.
#
# Used both by `srun ... bash slurm/run_gpu.sh <cmd>` (interactive) and by
# sbatch (see header below). Centralising the environment setup means the
# interactive and batch paths cannot drift apart.
#
#SBATCH --job-name=nextverse
#SBATCH --partition=Teaching
#SBATCH --nodelist=saxa
#SBATCH --gres=gpu:h200_1g.18gb:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=03:00:00
# 3h not 2h: a 1g.18gb slice has ~1/7 of the H200's SMs, and the zero-shot base
# model is the arm most likely to ramble to the 2048-token cap on every example.
#SBATCH --output=results/slurm-%j.out
set -euo pipefail

# Resolve the project root robustly. Three cases must all work:
#
#   1. srun / plain bash: BASH_SOURCE points at slurm/run_gpu.sh, so the parent
#      directory is the root.
#   2. sbatch: Slurm executes a *copy* of this script from its spool directory,
#      so BASH_SOURCE is useless and SLURM_SUBMIT_DIR is the right answer.
#   3. Either of the above with a STALE inherited SLURM_SUBMIT_DIR - an
#      interactive `srun --pty bash` started from $HOME exports
#      SLURM_SUBMIT_DIR=$HOME into that shell, where it then outlives any later
#      cd. Trusting it unconditionally was the original bug.
#
# So: try candidates in priority order and accept the first that actually looks
# like this project, rather than assuming any single one is correct.
_find_root() {
  local c
  for c in "$@"; do
    if [[ -n "$c" && -f "$c/config.yaml" && -d "$c/src/nextverse" ]]; then
      (cd "$c" && pwd)   # normalise ../ and symlinks
      return 0
    fi
  done
  return 1
}

_self="${BASH_SOURCE[0]:-$0}"
_selfdir="$(cd "$(dirname "$_self")" 2>/dev/null && pwd || true)"

# NEXTVERSE_ROOT first so an explicit override always wins.
ROOT="$(_find_root "${NEXTVERSE_ROOT:-}" "$_selfdir/.." "${SLURM_SUBMIT_DIR:-}" "$PWD")" || {
  echo "ERROR: cannot locate the project root." >&2
  echo "  A valid root contains both config.yaml and src/nextverse/. Tried:" >&2
  echo "    NEXTVERSE_ROOT    = '${NEXTVERSE_ROOT:-<unset>}'" >&2
  echo "    script dir parent = '$_selfdir/..'" >&2
  echo "    SLURM_SUBMIT_DIR  = '${SLURM_SUBMIT_DIR:-<unset>}'" >&2
  echo "    PWD               = '$PWD'" >&2
  echo "  Fix: export NEXTVERSE_ROOT=/home/s2806882/projects/nextVerse" >&2
  exit 2
}
cd "$ROOT"

if [[ ! -f "$ROOT/.venv/bin/activate" ]]; then
  echo "ERROR: no venv at $ROOT/.venv - run 'bash scripts/00_prep_env.sh' on the login node first." >&2
  exit 2
fi

# Project-local cache, and offline mode: the GPU node may have no internet, and
# we want a clear immediate error rather than a silent hang if weights are
# missing from the cache that prep was supposed to fill.
export HF_HOME="$ROOT/.hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8   # determinism, see src/nextverse/seeding.py

source "$ROOT/.venv/bin/activate"

echo "host: $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader || true
echo "cmd: $*"
echo "---"

exec "$@"
