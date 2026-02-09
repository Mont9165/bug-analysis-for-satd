# Enhanced Bug-Fixing Commit Detection - Quick Start Guide

## Overview

This guide helps you get started with the new enhanced bug-fixing commit detection features based on research literature.

## What's New?

### Multiple Detection Strategies

The tool now supports 5 detection strategies based on research:

1. **Simple (Casalnuovo et al., 2017)** - Highest recall
   - Matches any keyword: error, defect, flaw, bug, fix, issue, mistake, fault, incorrect
   - Best for: Initial exploration, maximizing bug-fix detection

2. **Strict (Rosa et al., 2023)** - Balanced precision/recall
   - Requires BOTH fix words (fix, solve) AND bug words (bug, issue, problem, error, misfeature)
   - Excludes: merge commits
   - Best for: Research requiring validated bug-fixes

3. **Pantiuchina (Pantiuchina et al., 2020)** - Extended keywords
   - Pattern: (fix|solve|close) AND (bug|defect|crash|fail|error)
   - Best for: Balanced detection with crash/failure emphasis

4. **Issue ID (Borg et al., 2019)** - Highest precision
   - Detects JIRA patterns (LANG-123, IO-456) and GitHub issues (#123 with "fix")
   - Best for: Projects with disciplined issue tracking

5. **Combined (Default)** - Best of all worlds
   - Uses all strategies in priority order
   - Returns detection method and matched pattern
   - Best for: Most use cases

## Quick Start Examples

### Example 1: Simple Detection
```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy simple
```

### Example 2: Issue ID Detection (JIRA Projects)
```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy issue_id \
    --config configs/bug_fix_patterns.yaml
```

### Example 3: Combined Strategy (Recommended)
```bash
python scripts/extract_bug_fixing_commits.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy combined \
    --config configs/bug_fix_patterns.yaml
```

### Example 4: Batch Processing
```bash
python scripts/batch_extract.py \
    --config configs/bug_fix_patterns.yaml \
    --strategy combined \
    --output-dir ./batch_results
```

### Example 5: Full Pipeline with Strategy
```bash
python scripts/full_pipeline.py \
    --repo-url https://github.com/apache/commons-lang \
    --branch master \
    --strategy combined \
    --llm4szz-path /path/to/LLM4SZZ
```

## Output Format

The enhanced output includes detection metadata:

```json
{
  "repo_name": "apache/commons-lang",
  "bug_fixing_commit": "abc123def456",
  "commit_message": "LANG-1234: Fix null pointer exception",
  "author": "Developer <dev@example.com>",
  "date": "2024-01-15T14:30:00Z",
  "detection_method": "issue_id",
  "matched_pattern": "LANG-1234"
}
```

## Supported Projects

Pre-configured JIRA patterns for:
- apache/commons-lang (LANG-*)
- apache/commons-io (IO-*)
- hibernate/hibernate-orm (HHH-*)
- apache/dubbo (DUBBO-*)
- apache/maven (MNG-*)
- apache/storm (STORM-*)

GitHub issue patterns (#*) for:
- INRIA/spoon
- jfree/jfreechart

## Strategy Selection Guide

| Use Case | Recommended Strategy | Rationale |
|----------|---------------------|-----------|
| Research requiring precision | `strict` or `issue_id` | Lower false positives |
| Exploratory analysis | `simple` or `combined` | Higher recall |
| JIRA-based projects | `issue_id` | Most accurate for tracked issues |
| General purpose | `combined` | Balances all strategies |
| Maximum bug-fix detection | `simple` | Highest recall |

## Customization

### Add Your Own JIRA Pattern

Edit `configs/bug_fix_patterns.yaml`:

```yaml
jira_patterns:
  your-org/your-repo: "PROJ-\\d+"
```

### Add Target Repository for Batch Processing

Edit `configs/bug_fix_patterns.yaml`:

```yaml
target_repositories:
  - url: https://github.com/your-org/your-repo
    branch: main
```

## Testing Your Setup

Run the test suite:
```bash
python test_detection_strategies.py
```

Run the demo:
```bash
python demo_detection.py
```

## Backward Compatibility

All existing scripts continue to work with default behavior:
- `extract_bug_fixing_commits.py` defaults to `combined` strategy
- `full_pipeline.py` supports the new `--strategy` parameter
- Legacy pattern mode still available via `--patterns` argument

## Literature References

1. Rosa et al. (2023) - Strict fix+bug matching
2. Pantiuchina et al. (2020) - OR+AND keyword logic
3. Casalnuovo et al. (2017) - Simple keyword matching
4. Borg et al. (2019) - SZZ Unleashed (Issue ID-based)

## Support

For issues or questions:
- GitHub Issues: https://github.com/Mont9165/bug-analysis-for-satd/issues
- Documentation: See README.md for full details
