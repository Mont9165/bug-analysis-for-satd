#!/bin/bash
#SBATCH -p isgpu2h200_long
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
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

# Load Singularity module
module load singularity

# Change to project directory (LLM4SZZ expects dataset/ subdirectory)
cd "${PROJECT_DIR}"

# Run LLM4SZZ with Singularity
START_TIME=$(date +%s)

END_ARG=""
if [ -n "${END}" ]; then
    END_ARG="--end ${END}"
fi

singularity exec --nv \
  --bind ${PROJECT_DIR}:/workspace \
  --bind ${LLM4SZZ_DIR}:/llm4szz \
  --pwd /workspace \
  ~/singularity_images/llm4szz.sif \
  python3.12 /llm4szz/llm4szz.py \
    --model "${MODEL}" \
    --parallel "${PARALLEL}" \
    --start "${START}" \
    ${END_ARG}

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))

echo ""
echo "=========================================="
echo "Job completed"
echo "=========================================="
echo "Runtime: $((RUNTIME / 60)) minutes $((RUNTIME % 60)) seconds"
echo "Output directory: ${PROJECT_DIR}/output"
echo "=========================================="
