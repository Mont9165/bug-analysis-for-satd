#!/bin/bash
#SBATCH -p isgpu2h200_long
#SBATCH --gres=gpu:1
#SBATCH --time=4-00:00:00
#SBATCH --mem=200G
#SBATCH --cpus-per-task=32
#SBATCH --job-name=bug_analysis
#SBATCH --output=logs/bug_analysis_%j.out
#SBATCH --error=logs/bug_analysis_%j.err

# Bug Analysis Pipeline for SATD Research
# GPU cluster execution script with auto-resubmit

SCRIPT_PATH="$(realpath "$0")"
MIN_RUNTIME_SEC=600  # If runtime < 10 minutes, assume processing is complete

# Configuration - modify these as needed
REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"
LLM4SZZ_PATH="${LLM4SZZ_PATH:-${HOME}/LLM4SZZ}"
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/bug-analysis-for-satd/output}"
MODEL="${MODEL:-Qwen/Qwen3-8B}"
PARALLEL="${PARALLEL:-5}"

mkdir -p logs

module load singularity

cd ~/bug-analysis-for-satd || {
  echo "ERROR: Failed to change directory"
  exit 1
}

echo "=== Job started at $(date) ==="
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo "Model: $MODEL"

START_TIME=$(date +%s)

# Run the pipeline using Singularity
singularity exec --nv \
  --bind ${HOME}/bug-analysis-for-satd:/app \
  --bind ${HOME}/LLM4SZZ:/llm4szz \
  --bind ${OUTPUT_DIR}:/app/output \
  --pwd /app \
  ~/singularity_images/llm4szz.sif \
  python3.12 scripts/full_pipeline.py \
    --repo-url "$REPO_URL" \
    --branch "$BRANCH" \
    --llm4szz-path /llm4szz \
    --output-dir /app/output \
    --model "$MODEL" \
    --parallel "$PARALLEL"

EXIT_CODE=$?
END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))

echo "=== Job finished at $(date) ==="
echo "Runtime: $((RUNTIME / 60)) minutes $((RUNTIME % 60)) seconds"
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "Job failed with exit code $EXIT_CODE. Not resubmitting."
  exit $EXIT_CODE
fi

if [ $RUNTIME -lt $MIN_RUNTIME_SEC ]; then
  echo "Runtime < $MIN_RUNTIME_SEC seconds. Processing appears complete."
  echo "No resubmit needed."
else
  echo "Runtime >= $MIN_RUNTIME_SEC seconds. More work may remain."
  echo "Resubmitting job..."
  sbatch "$SCRIPT_PATH"
fi
