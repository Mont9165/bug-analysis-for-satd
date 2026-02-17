#!/bin/bash
# Test script for LLM4SZZ with jfreechart (74 commits)
# Usage: ./scripts/cluster/test_llm4szz.sh

set -e

BASE_DIR="/work/kosei-ho/bug-analysis-for-satd"

echo "=========================================="
echo "LLM4SZZ Test Execution"
echo "=========================================="
echo "Project: jfreechart (74 commits)"
echo "Partition: gpu_short"
echo "Time limit: 1 hour"
echo "Model: Qwen/Qwen2.5-Coder-3B-Instruct"
echo "Parallel: 5"
echo "=========================================="
echo ""

# Submit test job
JOB_ID=$(sbatch \
  -p gpu_long \
  --time=20:00:00 \
  --export=PROJECT=jfreechart,START=0,END=74,MODEL=Qwen/Qwen2.5-Coder-3B-Instruct,PARALLEL=5 \
  --job-name=llm4szz_test \
  "${BASE_DIR}/scripts/cluster/run_llm4szz.sh" | grep -oP '\d+')

echo "✅ Test job submitted: ${JOB_ID}"
echo ""
echo "Monitor with:"
echo "  squeue -j ${JOB_ID}"
echo ""
echo "Check logs:"
echo "  tail -f logs/llm4szz_llm4szz_test_${JOB_ID}.out"
echo "  tail -f logs/llm4szz_llm4szz_test_${JOB_ID}.err"
echo ""
echo "Expected output:"
echo "  ${BASE_DIR}/llm4szz_datasets/jfreechart/output/*.json"
echo ""
