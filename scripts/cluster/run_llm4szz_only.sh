#!/bin/bash
#SBATCH -p gpu_short
#SBATCH --gres=gpu:1
#SBATCH --time=2:00:00
#SBATCH --mem=200G
#SBATCH --cpus-per-task=32
#SBATCH --job-name=llm4szz_analysis
#SBATCH --output=logs/llm4szz_analysis_%j.out
#SBATCH --error=logs/llm4szz_analysis_%j.err

# LLM4SZZ Analysis Only
# For when bug-fixing commits are already extracted
# This script expects dataset/ directory in the working directory

set -e

SCRIPT_PATH="$(realpath "$0")"
MIN_RUNTIME_SEC=600

BASE_DIR="${HOME}/bug-analysis-for-satd"
LLM4SZZ_DIR="${HOME}/LLM4SZZ"
WORK_DIR="${WORK_DIR:-${BASE_DIR}}"
MODEL="${MODEL:-Qwen/Qwen2.5-Coder-3B-Instruct}"
PARALLEL="${PARALLEL:-5}"
START_IDX="${START_IDX:-0}"
END_IDX="${END_IDX:-}"

mkdir -p logs

# Initialize module system
source /etc/profile.d/modules.sh
module load singularity

cd "${WORK_DIR}" || exit 1

echo "==========================================="
echo "LLM4SZZ Analysis"
echo "==========================================="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Work directory: ${WORK_DIR}"
echo "Model: ${MODEL}"
echo "Parallel: ${PARALLEL}"
echo "Start index: ${START_IDX}"
echo "End index: ${END_IDX:-end}"
echo "==========================================="
echo ""

START_TIME=$(date +%s)

# Build command with optional start/end
END_ARG=""
if [ -n "${END_IDX}" ]; then
    END_ARG="--end ${END_IDX}"
fi

# Run actual LLM4SZZ tool
singularity exec --nv \
  --bind ${WORK_DIR}:/workspace:rw \
  --bind ${WORK_DIR}:/app:rw \
  --bind ${LLM4SZZ_DIR}:/llm4szz:ro \
  --pwd /workspace \
  --env TMPDIR=/workspace \
  --env HOME=/workspace \
  ~/singularity_images/llm4szz.sif \
  python3.12 /llm4szz/llm4szz.py \
    --model "${MODEL}" \
    --parallel "${PARALLEL}" \
    --start "${START_IDX}" \
    ${END_ARG}

EXIT_CODE=$?
END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))

echo "=== Job finished at $(date) ==="
echo "Runtime: $((RUNTIME / 60)) minutes $((RUNTIME % 60)) seconds"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Job failed. Not resubmitting."
  exit $EXIT_CODE
fi

if [ $RUNTIME -lt $MIN_RUNTIME_SEC ]; then
  echo "Processing complete."
else
  echo "Resubmitting..."
  sbatch "$SCRIPT_PATH"
fi
