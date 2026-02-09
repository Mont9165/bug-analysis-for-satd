#!/bin/bash
# Submit LLM4SZZ jobs for all projects or specific projects
# Usage:
#   ./scripts/cluster/submit_llm4szz_batch.sh                    # Submit all projects
#   ./scripts/cluster/submit_llm4szz_batch.sh commons-lang maven # Submit specific projects

set -e

BASE_DIR="/work/kosei-ho/bug-analysis-for-satd"
SCRIPT_DIR="${BASE_DIR}/scripts/cluster"

# Project configurations (name:commit_count)
declare -A PROJECTS
PROJECTS[commons-lang]=424
PROJECTS[commons-io]=232
PROJECTS[hibernate-orm]=3199
PROJECTS[dubbo]=1503
PROJECTS[spoon]=1152
PROJECTS[maven]=1030
PROJECTS[storm]=717
PROJECTS[jfreechart]=74

# Model configuration
MODEL="Qwen/Qwen2.5-Coder-3B-Instruct"
PARALLEL=5

# Determine which projects to submit
if [ $# -eq 0 ]; then
    # No arguments - submit all projects
    TO_SUBMIT=(${!PROJECTS[@]})
    echo "Submitting all 8 projects..."
else
    # Specific projects provided
    TO_SUBMIT=("$@")
    echo "Submitting specific projects: ${TO_SUBMIT[@]}"
fi

echo "Model: ${MODEL}"
echo "Parallel workers: ${PARALLEL}"
echo ""

# Create logs directory
mkdir -p "${BASE_DIR}/logs"

# Submit jobs
TOTAL_COMMITS=0
SUBMITTED_JOBS=()

for project in "${TO_SUBMIT[@]}"; do
    if [ -z "${PROJECTS[$project]}" ]; then
        echo "❌ Unknown project: $project"
        echo "   Available: ${!PROJECTS[@]}"
        continue
    fi

    commit_count=${PROJECTS[$project]}
    TOTAL_COMMITS=$((TOTAL_COMMITS + commit_count))

    echo "--- Submitting: $project (${commit_count} commits) ---"

    JOB_ID=$(sbatch \
        --export=PROJECT=${project},START=0,END=${commit_count},MODEL=${MODEL},PARALLEL=${PARALLEL} \
        --job-name=llm4szz_${project} \
        "${SCRIPT_DIR}/run_llm4szz.sh" | grep -oP '\d+')

    echo "✅ Submitted job ${JOB_ID} for ${project}"
    SUBMITTED_JOBS+=("${JOB_ID}:${project}")
    echo ""
done

echo "=========================================="
echo "Submission Summary"
echo "=========================================="
echo "Total projects: ${#TO_SUBMIT[@]}"
echo "Total commits: ${TOTAL_COMMITS}"
echo "Submitted jobs: ${#SUBMITTED_JOBS[@]}"
echo ""

echo "Job IDs:"
for job in "${SUBMITTED_JOBS[@]}"; do
    echo "  ${job}"
done
echo ""

echo "Monitor jobs:"
echo "  squeue -u \$USER"
echo ""
echo "Check logs:"
echo "  tail -f logs/llm4szz_*.out"
echo ""

# Calculate estimated completion time
echo "=========================================="
echo "Estimated Completion Time"
echo "=========================================="

# Assume 5-10 seconds per commit with lightweight model
MIN_SECONDS=$((TOTAL_COMMITS * 5))
MAX_SECONDS=$((TOTAL_COMMITS * 10))

# With parallel workers (divide by number of parallel workers)
MIN_SECONDS_PARALLEL=$((MIN_SECONDS / PARALLEL))
MAX_SECONDS_PARALLEL=$((MAX_SECONDS / PARALLEL))

echo "Sequential (no parallelization):"
echo "  Min: $((MIN_SECONDS / 3600)) hours $((MIN_SECONDS % 3600 / 60)) minutes"
echo "  Max: $((MAX_SECONDS / 3600)) hours $((MAX_SECONDS % 3600 / 60)) minutes"
echo ""
echo "With ${PARALLEL} parallel workers (per GPU):"
echo "  Min: $((MIN_SECONDS_PARALLEL / 3600)) hours $((MIN_SECONDS_PARALLEL % 3600 / 60)) minutes"
echo "  Max: $((MAX_SECONDS_PARALLEL / 3600)) hours $((MAX_SECONDS_PARALLEL % 3600 / 60)) minutes"
echo ""
echo "With 8 GPUs (all projects in parallel):"
echo "  Min: $((MIN_SECONDS / PARALLEL / 8 / 3600)) hours $((MIN_SECONDS / PARALLEL / 8 % 3600 / 60)) minutes"
echo "  Max: $((MAX_SECONDS / PARALLEL / 8 / 3600)) hours $((MAX_SECONDS / PARALLEL / 8 % 3600 / 60)) minutes"
echo "=========================================="
