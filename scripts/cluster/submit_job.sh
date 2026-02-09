#!/bin/bash
# Helper script to submit bug analysis jobs

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --repo-url URL      Repository URL to analyze (required for full pipeline)"
  echo "  --branch BRANCH     Branch name (default: main)"
  echo "  --input FILE        Input file for LLM4SZZ-only mode"
  echo "  --model MODEL       LLM model (default: Qwen/Qwen3-8B)"
  echo "  --parallel N        Parallel workers (default: 5)"
  echo "  --start N           Start index"
  echo "  --end N             End index"
  echo "  --llm4szz-only      Run only LLM4SZZ analysis"
  echo "  -h, --help          Show this help"
}

# Defaults
BRANCH="main"
MODEL="Qwen/Qwen3-8B"
PARALLEL=5
LLM4SZZ_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo-url) REPO_URL="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --input) INPUT_FILE="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --start) START_IDX="$2"; shift 2 ;;
    --end) END_IDX="$2"; shift 2 ;;
    --llm4szz-only) LLM4SZZ_ONLY=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

SCRIPT_DIR="$(dirname "$(realpath "$0")")"

if [ "$LLM4SZZ_ONLY" = true ]; then
  export INPUT_FILE MODEL PARALLEL START_IDX END_IDX
  sbatch "$SCRIPT_DIR/run_llm4szz_only.sh"
else
  if [ -z "$REPO_URL" ]; then
    echo "Error: --repo-url is required for full pipeline"
    usage
    exit 1
  fi
  export REPO_URL BRANCH MODEL PARALLEL
  sbatch "$SCRIPT_DIR/run_pipeline_gpu.sh"
fi
