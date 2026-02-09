# bug-analysis-for-satd

Bug analysis pipeline for Self-Admitted Technical Debt (SATD) research.

## HPC Cluster Usage (SLURM)

### Prerequisites
- Singularity/Apptainer installed
- LLM4SZZ Singularity image at `~/singularity_images/llm4szz.sif`
- LLM4SZZ repository cloned at `~/LLM4SZZ`

### Submit Full Pipeline Job
```bash
./scripts/cluster/submit_job.sh \
  --repo-url https://github.com/owner/repo \
  --branch main \
  --model Qwen/Qwen3-8B \
  --parallel 5
```

### Submit LLM4SZZ-Only Job
```bash
./scripts/cluster/submit_job.sh \
  --llm4szz-only \
  --input output/bug_fixing_commits.json \
  --start 0 \
  --end 1000
```

### Direct SLURM Submission
```bash
# Set environment variables and submit
export REPO_URL="https://github.com/owner/repo"
export BRANCH="main"
sbatch scripts/cluster/run_pipeline_gpu.sh
```

### Monitor Jobs
```bash
squeue -u $USER
tail -f logs/bug_analysis_*.out
```

## Directory Structure

```
bug-analysis-for-satd/
├── scripts/
│   ├── extract_bug_fixing_commits.py
│   ├── run_llm4szz_analysis.py
│   ├── full_pipeline.py
│   └── cluster/
│       ├── run_pipeline_gpu.sh      # Full pipeline SLURM script
│       ├── run_llm4szz_only.sh      # LLM4SZZ-only SLURM script
│       └── submit_job.sh            # Job submission helper
├── logs/                             # SLURM log files (gitignored)
└── ...
```

## Features

### HPC Cluster Scripts
- **Auto-resubmit**: Jobs automatically resubmit if they exceed the minimum runtime threshold
- **GPU Support**: SLURM scripts configured for GPU-enabled nodes (isgpu2h200_long partition)
- **Singularity/Apptainer**: Containerized execution for reproducibility
- **Flexible Configuration**: Environment variables for easy customization
- **Job Management**: Helper scripts for easy job submission and monitoring

### Based On
- [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ) - Bug-introducing commit identification using LLMs
- Original reference: https://github.com/Mont9165/LLM4SZZ/blob/main/run_isgpu.sh
# Bug Analysis for SATD

A unified bug analysis pipeline that combines functionality from two existing projects to enable automatic extraction of bug-fixing commits from Git repositories and analysis using LLM4SZZ to identify bug-inducing commits.

## Overview

This project integrates:
- **Bug-fixing commit extraction**: Analyzes commit messages to identify bug fixes
- **LLM4SZZ analysis**: Uses Large Language Models to identify bug-inducing commits

The pipeline automates the entire workflow from repository analysis to bug-inducing commit identification.

## Features

- 🔍 **Automated Bug-Fix Detection**: Identifies bug-fixing commits using configurable regex patterns
- 🤖 **LLM-Enhanced Analysis**: Leverages LLM4SZZ for accurate bug-inducing commit detection
- 🔧 **Flexible Configuration**: Support for custom patterns via config files or command line
- 📊 **Structured Output**: JSON format compatible with LLM4SZZ and other analysis tools
- 🚀 **Unified Pipeline**: Single command to run the complete analysis workflow

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- LLM4SZZ (clone from https://github.com/Mont9165/LLM4SZZ)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/Mont9165/bug-analysis-for-satd.git
cd bug-analysis-for-satd
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Clone and set up LLM4SZZ (follow instructions at https://github.com/Mont9165/LLM4SZZ)

## Usage

### Option 1: Full Pipeline (Recommended)

Run the complete analysis with a single command:

```bash
python scripts/full_pipeline.py \
    --repo-url https://github.com/owner/repo \
    --branch main \
    --llm4szz-path /path/to/LLM4SZZ
```

### Option 2: Step-by-Step

#### Step 1: Extract Bug-Fixing Commits

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --branch main \
    --output-dir ./output
```

#### Step 2: Run LLM4SZZ Analysis

```bash
python scripts/run_llm4szz_analysis.py \
    --input ./output/bug_fixing_commits.json \
    --llm4szz-path /path/to/LLM4SZZ \
    --model Qwen/Qwen3-8B
```

## Configuration

### Bug-Fix Detection Strategies

The tool supports multiple detection strategies based on literature:

#### 1. **Combined Strategy (Default)**
Uses all detection methods in priority order:
1. Issue ID-based (JIRA/GitHub)
2. Strict (Rosa et al.)
3. Pantiuchina et al.
4. Simple (Casalnuovo et al.)

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy combined
```

#### 2. **Issue ID Strategy**
Detects bug-fixing commits based on issue tracker IDs:
- **JIRA patterns**: `LANG-123`, `IO-456`, `HHH-789`, etc.
- **GitHub issues**: `#123` (with "fix" keyword)

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy issue_id \
    --config configs/bug_fix_patterns.yaml
```

#### 3. **Strict Strategy (Rosa et al., 2023)**
Requires BOTH fix-related AND bug-related words:
- **Fix words**: fix, solve
- **Bug words**: bug, issue, problem, error, misfeature
- **Excludes**: merge

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --strategy strict
```

#### 4. **Pantiuchina Strategy (Pantiuchina et al., 2020)**
Requires: `(fix|solve|close)` AND `(bug|defect|crash|fail|error)`

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --strategy pantiuchina
```

#### 5. **Simple Strategy (Casalnuovo et al., 2017)**
Matches any keyword: error, defect, flaw, bug, fix, issue, mistake, fault, incorrect

```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --strategy simple
```

### Batch Processing

Process multiple repositories from a configuration file:

```bash
# Process all repositories with combined strategy
python scripts/batch_extract.py

# Use specific strategy for all repositories
python scripts/batch_extract.py --strategy issue_id

# Custom output directory
python scripts/batch_extract.py --output-dir ./batch_results
```

The configuration file `configs/bug_fix_patterns.yaml` includes:

```yaml
# Detection strategy configuration
detection_strategy: combined

# Rosa et al. (2023) patterns
rosa_2023:
  fix_words: [fix, solve]
  bug_words: [bug, issue, problem, error, misfeature]

# Pantiuchina et al. (2020) patterns
pantiuchina_2020:
  fix_words: [fix, solve, close]
  bug_words: [bug, defect, crash, fail, error]

# Casalnuovo et al. (2017) patterns
casalnuovo_2017:
  keywords: [error, defect, flaw, bug, fix, issue, mistake, fault, incorrect]

# Project-specific JIRA patterns
jira_patterns:
  apache/commons-lang: "LANG-\\d+"
  apache/commons-io: "IO-\\d+"
  hibernate/hibernate-orm: "HHH-\\d+"
  apache/dubbo: "DUBBO-\\d+"
  apache/maven: "MNG-\\d+"
  apache/storm: "STORM-\\d+"

# Target repositories for batch processing
target_repositories:
  - url: https://github.com/apache/commons-lang
    branch: master
  - url: https://github.com/apache/commons-io
    branch: master
  # ... more repositories
```

You can customize patterns by:

1. **Using a custom config file**:
```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --config configs/custom_patterns.yaml
```

2. **Specifying patterns on command line** (legacy mode):
```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/owner/repo \
    --patterns "\bfix\b" "\bbug\b" "\bpatch\b"
```

## Output Formats

### Bug-Fixing Commits (`bug_fixing_commits.json`)

With detection metadata:

```json
[
  {
    "repo_name": "apache/commons-lang",
    "bug_fixing_commit": "abc123def456...",
    "commit_message": "LANG-1234: Fix null pointer exception in StringUtils",
    "author": "Developer Name <dev@example.com>",
    "date": "2024-01-15T14:30:00Z",
    "detection_method": "issue_id",
    "matched_pattern": "LANG-1234"
  },
  {
    "repo_name": "apache/commons-lang",
    "bug_fixing_commit": "def789abc012...",
    "commit_message": "Fix bug in array handling",
    "author": "Another Dev <dev2@example.com>",
    "date": "2024-01-16T09:15:00Z",
    "detection_method": "strict",
    "matched_pattern": "Fix + bug"
  }
]
```

### Bug-Inducing Commits (`bug_inducing_commits.json`)

```json
[
  {
    "repo_name": "owner/repo",
    "bug_fixing_commit": "abc123def456...",
    "bug_inducing_commits": ["def456abc789..."],
    "strategy_used": "s2",
    "can_determine": true
  }
]
```

### Analysis Summary (`analysis_summary.json`)

```json
{
  "total_bug_fixes": 150,
  "bug_inducing_identified": 142,
  "identification_rate": "94.7%",
  "results_file": "./output/bug_inducing_commits.json"
}
```

## Project Structure

```
bug-analysis-for-satd/
├── README.md                           # This file
├── pyproject.toml                      # Project configuration
├── requirements.txt                    # Python dependencies
├── scripts/
│   ├── extract_bug_fixing_commits.py  # Phase 1: Extract bug-fixing commits
│   ├── run_llm4szz_analysis.py        # Phase 2: Run LLM4SZZ analysis
│   └── full_pipeline.py               # Unified pipeline
├── configs/
│   └── bug_fix_patterns.yaml          # Bug-fix detection patterns
├── repos/                              # Cloned repositories (gitignored)
└── output/                             # Analysis results (gitignored)
```

## Advanced Usage

### Custom Branch Analysis

```bash
python scripts/full_pipeline.py \
    --repo-url https://github.com/owner/repo \
    --branch develop \
    --llm4szz-path /path/to/LLM4SZZ
```

### Custom Output Directory

```bash
python scripts/full_pipeline.py \
    --repo-url https://github.com/owner/repo \
    --branch main \
    --llm4szz-path /path/to/LLM4SZZ \
    --output-dir ./my_analysis_results
```

### Using Different LLM Models

```bash
python scripts/full_pipeline.py \
    --repo-url https://github.com/owner/repo \
    --branch main \
    --llm4szz-path /path/to/LLM4SZZ \
    --model Qwen/Qwen3-8B
```

## Troubleshooting

### Git Not Found

If you get "git is not installed or not in PATH":
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

### PyYAML Import Error
If you get "PyYAML not installed":
```bash
pip install PyYAML
```

### LLM4SZZ Integration

The `run_llm4szz_analysis.py` script prepares data in LLM4SZZ format and provides instructions for running the actual analysis. Refer to the [LLM4SZZ documentation](https://github.com/Mont9165/LLM4SZZ) for specific execution commands.

## Related Projects

- **AI_Agent_Bug**: Bug-fixing commit collection and SZZ analysis  
  https://github.com/Mont9165/AI_Agent_Bug

- **LLM4SZZ**: LLM-enhanced bug-inducing commit detection  
  https://github.com/Mont9165/LLM4SZZ

## Literature References

This tool implements bug-fixing commit detection strategies from the following research:

1. **Rosa et al. (2023)** - "Strict Strategy"  
   Requires both fix-related words (fix, solve) AND bug-related words (bug, issue, problem, error, misfeature), while excluding merge commits.

2. **Pantiuchina et al. (2020)** - "OR+AND Strategy"  
   Uses the pattern: `(fix|solve|close) AND (bug|defect|crash|fail|error)`

3. **Casalnuovo et al. (2017)** - "Simple Keyword Strategy"  
   Matches any of: error, defect, flaw, bug, fix, issue, mistake, fault, incorrect

4. **Borg et al. (2019)** - "SZZ Unleashed: Issue ID-based Detection"  
   Identifies commits through JIRA patterns (e.g., `LANG-123`) and GitHub issue references (e.g., `#123`)

5. **Wattanakriengkrai et al.** - "LINE-DP"  
   Provides additional context for bug analysis methodologies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the LICENSE file for details (if applicable)

## Citation

If you use this tool in your research, please cite the related projects:

```bibtex

```

## Support

For issues, questions, or contributions, please use the [GitHub Issues](https://github.com/Mont9165/bug-analysis-for-satd/issues) page.
