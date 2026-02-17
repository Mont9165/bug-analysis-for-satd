#!/bin/bash
# Quick progress check for LLM4SZZ analysis
# Usage: ./scripts/check_progress.sh [project_name]

BASE_DIR="/work/kosei-ho/bug-analysis-for-satd"
LLM4SZZ_DATASETS="$BASE_DIR/llm4szz_datasets"

# Project configurations (name:expected_count)
declare -A EXPECTED
EXPECTED[commons-lang]=424
EXPECTED[commons-io]=232
EXPECTED[hibernate-orm]=3199
EXPECTED[dubbo]=1503
EXPECTED[spoon]=1152
EXPECTED[maven]=1030
EXPECTED[storm]=717
EXPECTED[jfreechart]=74

if [ -n "$1" ]; then
    # Single project
    PROJECTS=("$1")
else
    # All projects
    PROJECTS=(commons-lang commons-io hibernate-orm dubbo spoon maven storm jfreechart)
fi

echo "=========================================="
echo "LLM4SZZ Progress Check"
echo "=========================================="
echo ""

TOTAL_EXPECTED=0
TOTAL_PROCESSED=0

for project in "${PROJECTS[@]}"; do
    PROJECT_DIR="$LLM4SZZ_DATASETS/$project"
    SAVE_LOGS="$PROJECT_DIR/save_logs"

    if [ ! -d "$PROJECT_DIR" ]; then
        echo "⚠️  $project: Directory not found"
        continue
    fi

    EXPECTED_COUNT=${EXPECTED[$project]:-0}

    if [ -d "$SAVE_LOGS" ]; then
        # Count unique commit directories
        PROCESSED=$(find "$SAVE_LOGS" -mindepth 3 -maxdepth 3 -type d 2>/dev/null | wc -l)

        # Count total JSON files
        JSON_COUNT=$(find "$SAVE_LOGS" -name "*.json" 2>/dev/null | wc -l)

        PERCENT=$(awk "BEGIN {printf \"%.1f\", ($PROCESSED/$EXPECTED_COUNT)*100}")

        echo "📊 $project"
        echo "   Expected: $EXPECTED_COUNT commits"
        echo "   Processed: $PROCESSED commits ($PERCENT%)"
        echo "   JSON files: $JSON_COUNT"

        if [ $PROCESSED -eq $EXPECTED_COUNT ]; then
            echo "   ✅ COMPLETE"
        elif [ $PROCESSED -gt 0 ]; then
            echo "   🔄 IN PROGRESS"
        else
            echo "   ⏸️  NOT STARTED"
        fi

        TOTAL_EXPECTED=$((TOTAL_EXPECTED + EXPECTED_COUNT))
        TOTAL_PROCESSED=$((TOTAL_PROCESSED + PROCESSED))
    else
        echo "⚠️  $project: No save_logs directory"
    fi

    echo ""
done

if [ ${#PROJECTS[@]} -gt 1 ]; then
    OVERALL_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_PROCESSED/$TOTAL_EXPECTED)*100}")
    echo "=========================================="
    echo "Overall Progress: $TOTAL_PROCESSED / $TOTAL_EXPECTED ($OVERALL_PERCENT%)"
    echo "=========================================="
fi

# Check running jobs
echo ""
echo "Running Jobs:"
squeue -u $USER -o "%.18i %.12P %.20j %.8T %.10M %.6D" | grep llm4szz || echo "  No LLM4SZZ jobs running"
