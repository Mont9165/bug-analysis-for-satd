#!/bin/bash
#SBATCH -p isgpu2h200_long
#SBATCH --gres=gpu:1
#SBATCH --time=4-00:00:00
#SBATCH --mem=200G
#SBATCH --cpus-per-task=32
#SBATCH --job-name=llm4szz_analysis
#SBATCH --output=logs/llm4szz_analysis_%j.out
#SBATCH --error=logs/llm4szz_analysis_%j.err

# LLM4SZZ Analysis Only
# For when bug-fixing commits are already extracted

SCRIPT_PATH="$(realpath "$0")"
MIN_RUNTIME_SEC=600

INPUT_FILE="${INPUT_FILE:-output/bug_fixing_commits.json}"
LLM4SZZ_PATH="${LLM4SZZ_PATH:-${HOME}/LLM4SZZ}"
OUTPUT_DIR="${OUTPUT_DIR:-output}"
MODEL="${MODEL:-Qwen/Qwen3-8B}"
PARALLEL="${PARALLEL:-5}"
START_IDX="${START_IDX:-0}"
END_IDX="${END_IDX:-}"

mkdir -p logs

module load singularity

cd ~/bug-analysis-for-satd || exit 1

echo "=== LLM4SZZ Analysis started at $(date) ==="
echo "Input: $INPUT_FILE"
echo "Model: $MODEL"
echo "Index range: $START_IDX to ${END_IDX:-end}"

START_TIME=$(date +%s)

# Build command with optional start/end
CMD="python3.12 scripts/run_llm4szz_analysis.py \
  --input $INPUT_FILE \
  --llm4szz-path /llm4szz \
  --output-dir $OUTPUT_DIR \
  --model $MODEL \
  --parallel $PARALLEL"

if [ -n "$START_IDX" ]; then
  CMD="$CMD --start $START_IDX"
fi
if [ -n "$END_IDX" ]; then
  CMD="$CMD --end $END_IDX"
fi

singularity exec --nv \
  --bind ${HOME}/bug-analysis-for-satd:/app \
  --bind ${HOME}/LLM4SZZ:/llm4szz \
  --bind ${HOME}/bug-analysis-for-satd/repos:/app/repos \
  --pwd /app \
  ~/singularity_images/llm4szz.sif \
  $CMD

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
