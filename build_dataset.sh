#!/bin/bash
#SBATCH --job-name=sudoku-gen
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --output=logs/%x-%j.out
#SBATCH --partition=cpu-dense-preempt-q
#SBATCH --time=00:30:00
#SBATCH --requeue

set -euo pipefail

# --- environment (adjust to your cluster) ---
# module load miniconda            # or anaconda / python, check `module avail`
eval "$(conda shell.bash hook)"
conda activate cosc241_final

GRIDS=${GRIDS:-600}                # x4 stages -> ~2400 puzzles (paper had 2,293)
SEED=${SEED:-0}

python build_dataset.py \
  --grids "$GRIDS" \
  --workers "$SLURM_CPUS_PER_TASK" \
  --seed "$SEED" \
  --verify -1 \
  --out "data/puzzles_seed${SEED}.jsonl"