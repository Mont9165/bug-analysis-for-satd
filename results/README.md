# LLM4SZZ Analysis Results

Bug-inducing commit identification results for 8 open-source Java projects using [LLM4SZZ](https://github.com/Mont9165/LLM4SZZ).

## Dataset Overview

| Project | Bug-Fixing Commits | With Bug-Inducing | Rate | Bug-Inducing Commits | Buggy Statements |
|---|---|---|---|---|---|
| commons-lang | 424 | 263 | 62.0% | 381 | 5,156 |
| commons-io | 232 | 108 | 46.6% | 203 | 10,890 |
| hibernate-orm | 3,199 | 2,300 | 71.9% | 4,041 | 47,305 |
| dubbo | 1,503 | 1,074 | 71.5% | 1,966 | 20,206 |
| spoon | 1,152 | 977 | 84.8% | 1,732 | 16,879 |
| maven | 1,030 | 820 | 79.6% | 1,514 | 14,971 |
| storm | 717 | 590 | 82.3% | 1,022 | 16,499 |
| jfreechart | 74 | 46 | 62.2% | 74 | 666 |
| **Total** | **8,331** | **6,178** | **74.2%** | **10,933** | **132,572** |

## Analysis Configuration

| Item | Value |
|---|---|
| Tool | LLM4SZZ |
| Model | Qwen/Qwen2.5-Coder-3B-Instruct |
| Agent release date | 1970-01-01 (full history search) |
| Parallel workers | 5 per GPU |
| Total files analyzed | 24,992 |

## Strategy Breakdown (file-level)

LLM4SZZ uses two strategies per changed file:

- **Strategy 1 (S1)**: Direct LLM analysis — the LLM identifies buggy statements directly from the patch
- **Strategy 2 (S2)**: SZZ + LLM — traditional SZZ finds candidate commits, then LLM validates and ranks them

| Strategy | Files | % of total files |
|---|---|---|
| S1 only succeeded | 3,017 | 12.1% |
| S2 only succeeded | 3,264 | 13.1% |
| Both S1 and S2 succeeded | 11,592 | 46.4% |
| Neither succeeded | 7,119 | 28.5% |
| **Error** | **0** | **0.0%** |
| Total | 24,992 | 100% |

S1 contributed to results in **58.5%** of files (14,609 files).
S2 contributed to results in **59.4%** of files (14,856 files).

## Error Summary

- **Processing errors**: 0 / 8,331 commits (0%)
- **Missing commits**: 0 / 8,331 commits (0%)
- All 8,331 bug-fixing commits were successfully processed.

## File Structure

```
results/
├── README.md                  # This file
├── all_results.json           # Full results (all projects, all commits)
├── all_results.csv            # CSV format (spreadsheet-compatible)
└── jfreechart_results.json    # Per-project example
```

### JSON Format

```json
{
  "<project>": {
    "summary": {
      "total_bug_fixing_commits": 424,
      "commits_with_bug_inducing": 263,
      "bug_inducing_rate": "62.0%",
      "total_bug_inducing_commits": 381,
      "total_buggy_statements": 5156
    },
    "commits": {
      "<bug_fixing_commit_hash>": {
        "repo_name": "apache/commons-lang",
        "bug_fixing_commit": "<hash>",
        "bug_inducing_commits": ["<hash1>", "<hash2>"],
        "buggy_statements": [
          {
            "file": "src/main/java/org/apache/commons/lang3/StringUtils.java",
            "lineno": 123,
            "statement": "if (str == null) return null;",
            "induce_cid": "<bug_inducing_commit_hash>"
          }
        ],
        "can_determine": true
      }
    }
  }
}
```

### Key Fields

| Field | Description |
|---|---|
| `bug_fixing_commit` | The commit that fixed the bug |
| `bug_inducing_commits` | Commits that introduced the bug |
| `buggy_statements` | Code lines identified as containing the bug |
| `buggy_statements[].induce_cid` | Links each buggy line to its bug-inducing commit |
| `can_determine` | Whether S1 (direct LLM) could determine the root cause |

## Usage Example

```python
import json
from collections import defaultdict

with open("results/all_results.json") as f:
    data = json.load(f)

# Get bug-inducing commits per project
for project, pdata in data.items():
    summary = pdata["summary"]
    print(f"{project}: {summary['commits_with_bug_inducing']}/{summary['total_bug_fixing_commits']} ({summary['bug_inducing_rate']})")

# Get buggy statements grouped by bug-inducing commit
commit = data["jfreechart"]["commits"]["<commit_hash>"]
by_bic = defaultdict(list)
for stmt in commit["buggy_statements"]:
    by_bic[stmt["induce_cid"]].append(stmt)

for bic, stmts in by_bic.items():
    print(f"Bug-inducing {bic[:8]}: {len(stmts)} buggy lines")
    for s in stmts:
        print(f"  {s['file']}:{s['lineno']}  {s['statement'].strip()}")
```

## Reproduction

```bash
# Clone repository
git clone https://github.com/kosei-ho/bug-analysis-for-satd
cd bug-analysis-for-satd

# Re-aggregate results from raw LLM4SZZ output
python scripts/aggregate_llm4szz_results.py \
  --all \
  --output results/all_results.json \
  --export-csv
```
