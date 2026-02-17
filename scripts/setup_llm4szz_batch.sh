#!/bin/bash
# Setup LLM4SZZ datasets for all 8 projects

set -e

BASE_DIR="/work/kosei-ho/bug-analysis-for-satd"
LLM4SZZ_DIR="/work/kosei-ho/LLM4SZZ"
BATCH_RESULTS="$BASE_DIR/batch_results"
LLM4SZZ_DATASETS="$BASE_DIR/llm4szz_datasets"

# Agent release date for LLM4SZZ
# Use "1970-01-01" to search all history (no date filtering)
# Use "2025-01-01" to use LLM4SZZ default (model knowledge cutoff)
AGENT_RELEASE_DATE="${AGENT_RELEASE_DATE:-1970-01-01}"

# Project list
PROJECTS=(
    "commons-lang"
    "commons-io"
    "hibernate-orm"
    "dubbo"
    "spoon"
    "maven"
    "storm"
    "jfreechart"
)

echo "=========================================="
echo "Setting up LLM4SZZ datasets"
echo "=========================================="
echo ""

# Create base directory
mkdir -p "$LLM4SZZ_DATASETS"

# Process each project
for project in "${PROJECTS[@]}"; do
    echo "--- Processing: $project ---"

    # Create dataset directory for this project
    PROJECT_DIR="$LLM4SZZ_DATASETS/$project"
    DATASET_DIR="$PROJECT_DIR/dataset"
    REPOS_DIR="$PROJECT_DIR/repos"
    OUTPUT_DIR="$PROJECT_DIR/output"

    mkdir -p "$DATASET_DIR"
    mkdir -p "$REPOS_DIR"
    mkdir -p "$OUTPUT_DIR"

    # Convert bug_fixing_commits.json to issue_list.json
    INPUT_FILE="$BATCH_RESULTS/$project/bug_fixing_commits.json"
    OUTPUT_FILE="$DATASET_DIR/issue_list.json"

    if [ -f "$INPUT_FILE" ]; then
        python3 "$BASE_DIR/scripts/convert_to_llm4szz.py" \
            --input "$INPUT_FILE" \
            --output "$OUTPUT_FILE" \
            --agent-release-date "$AGENT_RELEASE_DATE"
    else
        echo "❌ Input file not found: $INPUT_FILE"
        continue
    fi

    # Create symlink to repository
    REPO_SOURCE="$BATCH_RESULTS/repos/$project"
    REPO_TARGET="$REPOS_DIR/$project"

    if [ -d "$REPO_SOURCE" ]; then
        if [ ! -L "$REPO_TARGET" ]; then
            ln -s "$REPO_SOURCE" "$REPO_TARGET"
            echo "✅ Symlinked repository: $REPO_TARGET"
        fi
    else
        echo "⚠️  Repository not found: $REPO_SOURCE"
    fi

    echo ""
done

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review datasets in: $LLM4SZZ_DATASETS"
echo "2. Run LLM4SZZ for each project"
echo ""
echo "Example command for commons-lang:"
echo "  cd $LLM4SZZ_DATASETS/commons-lang"
echo "  python $LLM4SZZ_DIR/llm4szz.py \\"
echo "    --model Qwen/Qwen2.5-Coder-3B-Instruct \\"
echo "    --parallel 5"
