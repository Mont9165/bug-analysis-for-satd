# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bug analysis pipeline for Self-Admitted Technical Debt (SATD) research. This project combines bug-fixing commit extraction with LLM4SZZ analysis to identify bug-inducing commits. The pipeline can run locally or on HPC clusters (SLURM) with GPU support.

## Architecture

**Two-Phase Pipeline:**

1. **Phase 1: Bug-Fixing Commit Extraction** (`extract_bug_fixing_commits.py`)
   - Clones target repository into `repos/` directory
   - Supports 5 detection strategies based on literature:
     - **Simple** (Casalnuovo 2017): Any keyword match - highest recall
     - **Strict** (Rosa 2023): Fix AND bug words, excludes merges - balanced precision/recall
     - **Pantiuchina** (Pantiuchina 2020): `(fix|solve|close) AND (bug|defect|crash|fail|error)`
     - **Issue ID** (Borg 2019): JIRA/GitHub patterns - highest precision
     - **Combined** (default): Cascading strategy with priority ordering
   - Uses patterns from `configs/bug_fix_patterns.yaml`
   - Outputs `bug_fixing_commits.json` with detection metadata (method, matched pattern)

2. **Phase 2: LLM4SZZ Analysis** (`run_llm4szz_analysis.py`)
   - Takes bug-fixing commits as input
   - Transforms to LLM4SZZ dataset format (`llm4szz_dataset.json`)
   - Integrates with external LLM4SZZ tool (separate repository)
   - Outputs `bug_inducing_commits.json` and `analysis_summary.json`

**Unified Entry Point:**
- `full_pipeline.py` orchestrates both phases sequentially
- Imports functions from individual phase scripts
- Handles data flow between phases

**Cluster Execution:**
- `scripts/cluster/submit_job.sh` - Job submission wrapper with argument parsing
- `scripts/cluster/run_pipeline_gpu.sh` - SLURM batch script for full pipeline
- `scripts/cluster/run_llm4szz_only.sh` - SLURM batch script for LLM4SZZ-only jobs
- Uses Singularity containers (`~/singularity_images/llm4szz.sif`) for reproducibility
- Auto-resubmit feature: jobs resubmit if runtime exceeds 10 minutes

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Local Execution

**Run full pipeline:**
```bash
python scripts/full_pipeline.py \
  --repo-url https://github.com/owner/repo \
  --branch main \
  --llm4szz-path /path/to/LLM4SZZ \
  --output-dir ./output \
  --model Qwen/Qwen3-8B \
  --strategy combined
```

**Run Phase 1 only:**
```bash
python scripts/extract_bug_fixing_commits.py \
  --repo-url https://github.com/owner/repo \
  --branch main \
  --output-dir ./output \
  --config configs/bug_fix_patterns.yaml \
  --strategy combined
```

**Run with specific strategy:**
```bash
# Issue ID based (JIRA/GitHub)
python scripts/extract_bug_fixing_commits.py \
  --repo-url https://github.com/apache/commons-lang \
  --branch master \
  --strategy issue_id

# Strict detection (Rosa 2023)
python scripts/extract_bug_fixing_commits.py \
  --repo-url https://github.com/owner/repo \
  --strategy strict
```

**Batch processing:**
```bash
python scripts/batch_extract.py \
  --config configs/bug_fix_patterns.yaml \
  --strategy combined \
  --output-dir ./batch_results
```

**Run Phase 2 only:**
```bash
python scripts/run_llm4szz_analysis.py \
  --input ./output/bug_fixing_commits.json \
  --llm4szz-path /path/to/LLM4SZZ \
  --model Qwen/Qwen3-8B \
  --output-dir ./output
```

### HPC Cluster Execution

**Submit full pipeline job:**
```bash
./scripts/cluster/submit_job.sh \
  --repo-url https://github.com/owner/repo \
  --branch main \
  --model Qwen/Qwen3-8B \
  --parallel 5
```

**Submit LLM4SZZ-only job:**
```bash
./scripts/cluster/submit_job.sh \
  --llm4szz-only \
  --input output/bug_fixing_commits.json \
  --start 0 \
  --end 1000
```

**Direct SLURM submission:**
```bash
export REPO_URL="https://github.com/owner/repo"
export BRANCH="main"
export MODEL="Qwen/Qwen3-8B"
sbatch scripts/cluster/run_pipeline_gpu.sh
```

**Monitor jobs:**
```bash
squeue -u $USER
tail -f logs/bug_analysis_*.out
```

## Key Configuration

### Bug-Fix Detection Strategies
- File: `configs/bug_fix_patterns.yaml`
- **Default strategy**: `combined` (uses all strategies in priority order)
- **Strategy patterns**:
  - Rosa 2023: fix_words + bug_words (fix, solve + bug, issue, problem, error, misfeature)
  - Pantiuchina 2020: (fix|solve|close) + (bug|defect|crash|fail|error)
  - Casalnuovo 2017: Any keyword (error, defect, flaw, bug, fix, issue, mistake, fault, incorrect)
  - Issue ID: JIRA patterns (LANG-\d+, IO-\d+, etc.) and GitHub patterns (#\d+ with "fix")
- **Pre-configured JIRA patterns** for 8 repositories (apache/commons-lang, hibernate/hibernate-orm, etc.)
- **Exclusion patterns**: [Mm]erge, [Cc]herry, [Rr]evert, [Nn]oting
- Can use legacy patterns via command-line `--patterns` argument for backward compatibility

### SLURM Configuration
- Partition: `isgpu2h200_long`
- GPU: 1 GPU (using `--gres=gpu:1`)
- Time limit: 4 days
- Memory: 200GB
- CPUs: 32
- Logs directory: `logs/` (gitignored)

### Environment Variables for Cluster
- `REPO_URL`: Git repository URL to analyze
- `BRANCH`: Branch name (default: main)
- `LLM4SZZ_PATH`: Path to LLM4SZZ installation (default: `~/LLM4SZZ`)
- `OUTPUT_DIR`: Output directory (default: `~/bug-analysis-for-satd/output`)
- `MODEL`: LLM model to use (default: `Qwen/Qwen3-8B`)
- `PARALLEL`: Number of parallel workers (default: 5)

## Important Dependencies

### Python Dependencies
- PyYAML>=6.0 - Config file parsing
- GitPython>=3.1.0 - Git repository operations (alternative to subprocess calls)

### External Dependencies
- Git - Required for repository cloning and analysis
- LLM4SZZ - Separate tool repository (https://github.com/Mont9165/LLM4SZZ)
- Singularity/Apptainer - Container runtime for HPC cluster execution

### LLM4SZZ Integration
- This project prepares data for LLM4SZZ but doesn't directly execute it
- `run_llm4szz_analysis.py` creates placeholder results and prints integration instructions
- Actual LLM4SZZ execution requires navigating to LLM4SZZ directory and running their scripts
- LLM4SZZ path must be provided via `--llm4szz-path` argument

## Output Structure

All outputs go to `output/` directory (gitignored):
- `bug_fixing_commits.json` - Phase 1 output: identified bug-fixing commits with metadata
  - Includes `detection_method` (which strategy detected it)
  - Includes `matched_pattern` (the specific pattern that matched)
- `llm4szz_dataset.json` - Phase 2 input: LLM4SZZ format dataset
- `bug_inducing_commits.json` - Phase 2 output: identified bug-inducing commits
- `analysis_summary.json` - Summary statistics

### Enhanced Output Format
```json
{
  "repo_name": "apache/commons-lang",
  "bug_fixing_commit": "abc123",
  "commit_message": "LANG-1234: Fix NPE",
  "author": "Developer <dev@example.com>",
  "date": "2024-01-15T14:30:00Z",
  "detection_method": "issue_id",
  "matched_pattern": "LANG-1234"
}
```

## Directory Structure Notes

- `repos/` - Cloned repositories (gitignored)
- `output/` - Analysis results (gitignored)
- `logs/` - SLURM job logs (gitignored)
- `scripts/` - Main Python scripts and cluster scripts
  - `extract_bug_fixing_commits.py` - Phase 1 with 5 detection strategies
  - `batch_extract.py` - Batch processing for multiple repositories
  - `run_llm4szz_analysis.py` - Phase 2 integration
  - `full_pipeline.py` - Unified pipeline
- `configs/` - Configuration files (bug-fix patterns, JIRA patterns, target repos)
- `tests/` - Unit tests (branch fallback tests)
- `test_detection_strategies.py` - Strategy validation tests
- `demo_detection.py` - Interactive strategy comparison demo
- `.venv/` - Virtual environment (gitignored)

## Testing

**Run all detection strategy tests:**
```bash
python test_detection_strategies.py
```

**Run demo comparing strategies:**
```bash
python demo_detection.py
```

**Run branch fallback tests:**
```bash
python -m pytest tests/test_branch_fallback.py
```

## Code Patterns

### Detection Strategies
- Each strategy implemented as separate function returning `(is_bug_fix, matched_pattern)`
- Combined strategy uses priority order: issue_id → strict → pantiuchina → simple
- Detection metadata added to output for analysis and debugging

### Script Imports
All main scripts (`full_pipeline.py`, `extract_bug_fixing_commits.py`, `run_llm4szz_analysis.py`) are designed as both:
- Importable modules (functions can be imported)
- Standalone executables (can be run via command line)

### Error Handling
- Scripts validate Git installation before execution
- PyYAML import is optional (graceful degradation if not installed)
- Repository cloning checks for existing directories
- LLM4SZZ validation provides warnings but continues execution
- Branch auto-detection: if specified branch doesn't exist, automatically detects and uses default branch (checks remote HEAD, then tries 'main', 'master', 'develop')

### Data Flow
1. User provides repository URL and branch
2. Repository cloned to `repos/{repo_name}/`
3. Commits extracted and filtered → `output/bug_fixing_commits.json`
4. Dataset transformed to LLM4SZZ format → `output/llm4szz_dataset.json`
5. LLM4SZZ analysis produces → `output/bug_inducing_commits.json`
6. Summary generated → `output/analysis_summary.json`
