# Bug Analysis for SATD

Bug-inducing commit identification pipeline for Self-Admitted Technical Debt (SATD) research.
Extracts bug-fixing commits from 8 open-source Java projects and identifies bug-inducing commits using [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ).

## Results

Analysis of **8,331 bug-fixing commits** across 8 projects:

| Project | Bug-Fixing Commits | Bug-Inducing Found | Rate | Bug-Inducing Commits | Buggy Statements |
|---|---|---|---|---|---|
| commons-lang | 424 | 263 | 62.0% | 381 | 5,156 |
| commons-io | 232 | 108 | 46.6% | 203 | 10,890 |
| hibernate-orm | 3,199 | 2,300 | 71.9% | 4,041 | 47,305 |
| dubbo | 1,503 | 1,074 | 71.5% | 1,966 | 20,206 |
| spoon | 1,152 | 977 | 84.8% | 1,732 | 16,879 |
| maven | 1,030 | 820 | 79.6% | 1,514 | 14,971 |
| storm | 717 | 590 | 82.3% | 1,022 | 16,499 |
| jfreechart | 74 | 46 | 62.2% | 74 | 666 |
| **Total** | **8,331** | **6,178 (74.2%)** | | **10,933** | **132,572** |

→ See [`results/README.md`](results/README.md) for detailed statistics and data format.

## Overview

This project implements a two-phase pipeline:

1. **Phase 1 — Bug-Fixing Commit Extraction**
   Identifies bug-fixing commits from Git history using issue tracker patterns (JIRA/GitHub) and keyword-based strategies.

2. **Phase 2 — Bug-Inducing Commit Identification**
   Runs [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ) on each bug-fixing commit to find which commit introduced the bug, and which specific lines of code are buggy.

## Target Projects

| Project | Repository | JIRA/Issue Pattern |
|---|---|---|
| commons-lang | [apache/commons-lang](https://github.com/apache/commons-lang) | `LANG-\d+` |
| commons-io | [apache/commons-io](https://github.com/apache/commons-io) | `IO-\d+` |
| hibernate-orm | [hibernate/hibernate-orm](https://github.com/hibernate/hibernate-orm) | `HHH-\d+` |
| dubbo | [apache/dubbo](https://github.com/apache/dubbo) | `DUBBO-\d+` |
| spoon | [INRIA/spoon](https://github.com/INRIA/spoon) | `#\d+` |
| maven | [apache/maven](https://github.com/apache/maven) | `MNG-\d+` |
| storm | [apache/storm](https://github.com/apache/storm) | `STORM-\d+` |
| jfreechart | [jfree/jfreechart](https://github.com/jfree/jfreechart) | `#\d+` |

## Repository Structure

```
bug-analysis-for-satd/
├── results/                              # Analysis results (this study)
│   ├── README.md                         # Results documentation
│   ├── all_results.json                  # Full results (all 8 projects)
│   └── all_results.csv                   # CSV format
├── configs/
│   └── bug_fix_patterns.yaml             # JIRA patterns & detection strategies
├── scripts/
│   ├── extract_bug_fixing_commits.py     # Phase 1: extract bug-fixing commits
│   ├── batch_extract.py                  # Phase 1: batch processing
│   ├── convert_to_llm4szz.py            # Convert to LLM4SZZ input format
│   ├── setup_llm4szz_batch.sh           # Set up dataset directories
│   ├── aggregate_llm4szz_results.py     # Aggregate LLM4SZZ output
│   ├── check_progress.sh                 # Monitor analysis progress
│   ├── update_agent_date.py              # Update agent_release_date in datasets
│   └── cluster/
│       ├── run_llm4szz.sh               # SLURM job script (Phase 2)
│       ├── submit_llm4szz_batch.sh      # Submit all 8 projects
│       └── test_llm4szz.sh              # Quick test with jfreechart
└── llm4szz_datasets/                    # LLM4SZZ input/output (gitignored, 2.4GB)
```

## Reproducing the Analysis

### Prerequisites

- Python 3.8+
- [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ) cloned at `~/LLM4SZZ`
- Singularity image at `~/singularity_images/llm4szz.sif`
- HPC cluster with SLURM + GPU

### Phase 1: Extract Bug-Fixing Commits

```bash
# Install dependencies
pip install -r requirements.txt

# Extract all 8 projects (issue_id strategy)
python scripts/batch_extract.py \
  --config configs/bug_fix_patterns.yaml \
  --strategy issue_id \
  --output-dir ./batch_results
```

### Phase 2: Identify Bug-Inducing Commits

```bash
# Set up LLM4SZZ datasets
python scripts/update_agent_date.py --all --date "1970-01-01"
./scripts/setup_llm4szz_batch.sh

# Submit all 8 projects to SLURM
./scripts/cluster/submit_llm4szz_batch.sh

# Monitor progress
./scripts/check_progress.sh
```

### Aggregate Results

```bash
python scripts/aggregate_llm4szz_results.py \
  --all \
  --output results/all_results.json \
  --export-csv
```

## Using the Results

```python
import json
from collections import defaultdict

with open("results/all_results.json") as f:
    data = json.load(f)

# Summary per project
for project, pdata in data.items():
    s = pdata["summary"]
    print(f"{project}: {s['commits_with_bug_inducing']}/{s['total_bug_fixing_commits']} ({s['bug_inducing_rate']})")

# Bug-inducing commits for a specific bug-fix
commit = data["commons-lang"]["commits"]["<commit_hash>"]
print("Bug-inducing commits:", commit["bug_inducing_commits"])

# Buggy statements grouped by bug-inducing commit
by_bic = defaultdict(list)
for stmt in commit["buggy_statements"]:
    by_bic[stmt["induce_cid"]].append(stmt)

for bic, stmts in by_bic.items():
    print(f"  {bic[:8]}: {stmts[0]['file']}:{stmts[0]['lineno']}")
    print(f"    {stmts[0]['statement'].strip()}")
```

## Bug-Fix Detection Strategies

Configured in `configs/bug_fix_patterns.yaml`:

| Strategy | Reference | Description |
|---|---|---|
| **issue_id** (used) | Borg et al. (2019) | JIRA/GitHub issue patterns — highest precision |
| strict | Rosa et al. (2023) | fix+bug keywords, excludes merges |
| pantiuchina | Pantiuchina et al. (2020) | `(fix\|solve\|close) AND (bug\|defect\|crash\|fail\|error)` |
| simple | Casalnuovo et al. (2017) | Any keyword match — highest recall |
| combined | — | Priority ordering of above strategies |

## Configuration

### SLURM (HPC Cluster)

| Parameter | Value |
|---|---|
| Partition | `gpu_short` |
| GPU | 1 × H200 |
| Memory | 100GB |
| CPUs | 16 |
| Time limit | 4 hours |

### LLM4SZZ

| Parameter | Value |
|---|---|
| Model | `Qwen/Qwen2.5-Coder-3B-Instruct` |
| Parallel workers | 5 |
| Agent release date | `1970-01-01` (full history search) |

## Related Projects

- **LLM4SZZ**: LLM-enhanced bug-inducing commit detection — https://github.com/Mont9165/LLM4SZZ
- **AI_Agent_Bug**: Bug-fixing commit collection and SZZ analysis — https://github.com/Mont9165/AI_Agent_Bug

## Literature References

1. **Borg et al. (2019)** — SZZ Unleashed: Issue ID-based detection
2. **Rosa et al. (2023)** — Strict keyword strategy
3. **Pantiuchina et al. (2020)** — OR+AND keyword strategy
4. **Casalnuovo et al. (2017)** — Simple keyword strategy
