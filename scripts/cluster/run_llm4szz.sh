#!/bin/bash
#SBATCH -p gpu_short
#SBATCH --gres=gpu:1
#SBATCH --time=4:00:00
#SBATCH --mem=100G
#SBATCH --cpus-per-task=16
#SBATCH --job-name=llm4szz
#SBATCH --output=logs/llm4szz_%x_%j.out
#SBATCH --error=logs/llm4szz_%x_%j.err

# LLM4SZZ execution script for HPC cluster
# Usage: sbatch --export=PROJECT=commons-lang,START=0,END=424 scripts/cluster/run_llm4szz.sh

set -e

# Configuration
PROJECT="${PROJECT:-commons-lang}"
START="${START:-0}"
END="${END:-}"
MODEL="${MODEL:-Qwen/Qwen2.5-Coder-3B-Instruct}"
PARALLEL="${PARALLEL:-5}"

BASE_DIR="${HOME}/bug-analysis-for-satd"
LLM4SZZ_DIR="${HOME}/LLM4SZZ"
PROJECT_DIR="${BASE_DIR}/llm4szz_datasets/${PROJECT}"
DATASET_DIR="${PROJECT_DIR}/dataset"

mkdir -p logs

echo "=========================================="
echo "LLM4SZZ Execution"
echo "=========================================="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Project: ${PROJECT}"
echo "Model: ${MODEL}"
echo "Start: ${START}"
echo "End: ${END}"
echo "Parallel: ${PARALLEL}"
echo "Dataset: ${DATASET_DIR}"
echo "=========================================="
echo ""

# Verify dataset exists
if [ ! -f "${DATASET_DIR}/issue_list.json" ]; then
    echo "❌ Error: Dataset not found at ${DATASET_DIR}/issue_list.json"
    exit 1
fi

COMMIT_COUNT=$(python3 -c "import json; print(len(json.load(open('${DATASET_DIR}/issue_list.json'))))")
echo "📋 Total commits in dataset: ${COMMIT_COUNT}"
echo ""

# Load Singularity module
source /etc/profile.d/modules.sh
module load singularity

# Change to project directory (LLM4SZZ expects dataset/ subdirectory)
cd "${PROJECT_DIR}"

# Run LLM4SZZ with Singularity
START_TIME=$(date +%s)

END_ARG=""
if [ -n "${END}" ]; then
    END_ARG="--end ${END}"
fi

# Set environment variable to change cache location
export TMPDIR="${PROJECT_DIR}"

singularity exec --nv \
  --bind ${PROJECT_DIR}:/workspace:rw \
  --bind ${PROJECT_DIR}:/app:rw \
  --bind ${LLM4SZZ_DIR}:/llm4szz:ro \
  --pwd /workspace \
  ~/singularity_images/llm4szz.sif \
  python3.12 /llm4szz/llm4szz.py \
    --model "${MODEL}" \
    --parallel "${PARALLEL}" \
    --start "${START}" \
    ${END_ARG}

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ LLM4SZZ failed with exit code: $EXIT_CODE"
    echo "Check error log: logs/llm4szz_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"
    exit $EXIT_CODE
fi

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))

# Count results
RESULT_DIRS=$(find "${PROJECT_DIR}/save_logs" -mindepth 3 -maxdepth 3 -type d 2>/dev/null | wc -l)
RESULT_FILES=$(find "${PROJECT_DIR}/save_logs" -name "*.json" 2>/dev/null | wc -l)

echo ""
echo "=========================================="
echo "Job completed"
echo "=========================================="
echo "Runtime: $((RUNTIME / 60)) minutes $((RUNTIME % 60)) seconds"
echo "Processed commits: ${RESULT_DIRS}"
echo "Result files: ${RESULT_FILES}"
echo "Output directory: ${PROJECT_DIR}/save_logs"
echo ""
echo "Next steps:"
echo "  1. Check results: ./scripts/check_progress.sh ${PROJECT}"
echo "  2. Aggregate: python scripts/aggregate_llm4szz_results.py --project ${PROJECT} --output results/${PROJECT}.json"
echo "=========================================="
