#!/usr/bin/env python3
"""
Aggregate LLM4SZZ results from save_logs directories.

This script collects all LLM4SZZ analysis results and produces:
1. Aggregated results per bug-fixing commit
2. Summary statistics
3. CSV export for further analysis

Usage:
    # Single project
    python scripts/aggregate_llm4szz_results.py \
        --project jfreechart \
        --output results/jfreechart_results.json

    # All projects
    python scripts/aggregate_llm4szz_results.py \
        --all \
        --output results/all_results.json
"""

import argparse
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
import csv


def extract_bug_inducing_info(llm_result: Any) -> Dict[str, Any]:
    """
    Extract bug-inducing commit information from LLM4SZZ result file.

    Args:
        llm_result: Parsed JSON from llm4szz*.json file (can be dict or list)

    Returns:
        Dictionary with bug-inducing commit info
    """
    # Initialize default values
    info = {
        'llm_patch_file_names': [],
        'can_determine': False,
        'criterion': '',
        's2_cand_stmts': [],   # Strategy 2: SZZ+LLM candidates
        's2_cand_cids': [],    # Strategy 2: bug-inducing commits
        's1_ranked_stmts_infos': [],  # Strategy 1: direct LLM
        's1_llm_file_final_cids': [], # Strategy 1: bug-inducing commits
        'token_cost': 0,
        'call_llm_times': 0,
        'elapsed_time': 0
    }

    # Handle list format (conversation history)
    if isinstance(llm_result, list):
        for item in llm_result:
            if isinstance(item, dict):
                if 'llm_patch_file_names' in item:
                    info['llm_patch_file_names'] = item.get('llm_patch_file_names', [])
                if 'can_determine' in item:
                    info['can_determine'] = item.get('can_determine', False)
                if 'criterion' in item:
                    info['criterion'] = item.get('criterion', '')
                if 's2_cand_stmts' in item:
                    info['s2_cand_stmts'] = item.get('s2_cand_stmts', [])
                if 's2_cand_cids' in item:
                    info['s2_cand_cids'] = item.get('s2_cand_cids', [])
                if 's1_ranked_stmts_infos' in item:
                    info['s1_ranked_stmts_infos'] = item.get('s1_ranked_stmts_infos', [])
                if 's1_llm_file_final_cids' in item:
                    info['s1_llm_file_final_cids'] = item.get('s1_llm_file_final_cids', [])
                if 'token_cost' in item:
                    info['token_cost'] = item.get('token_cost', 0)
                if 'call_llm_times' in item:
                    info['call_llm_times'] = item.get('call_llm_times', 0)
                if 'elapsed_time' in item:
                    info['elapsed_time'] = item.get('elapsed_time', 0)
    # Handle dict format
    elif isinstance(llm_result, dict):
        info = {k: llm_result.get(k, info[k]) for k in info}

    return info


def aggregate_project_results(project_dir: Path) -> Dict[str, Any]:
    """
    Aggregate LLM4SZZ results for a single project.

    Args:
        project_dir: Path to project directory in llm4szz_datasets/

    Returns:
        Aggregated results dictionary
    """
    save_logs_dir = project_dir / 'save_logs'

    if not save_logs_dir.exists():
        print(f"⚠️  No save_logs directory found in {project_dir}")
        return {'commits': {}, 'summary': {}}

    # Find all result JSON files
    result_files = list(save_logs_dir.rglob('llm4szz*.json'))

    print(f"Found {len(result_files)} result files in {project_dir.name}")

    # Group by commit hash (directory name)
    commits_data = defaultdict(lambda: {
        'repo_name': '',
        'bug_fixing_commit': '',
        'changed_files': [],
        'bug_inducing_commits': [],
        'buggy_statements': [],
        'can_determine': False,
        'total_token_cost': 0,
        'total_llm_calls': 0,
        'total_elapsed_time': 0
    })

    for result_file in result_files:
        # Extract commit hash from path
        # Path structure: save_logs/owner/repo/commit_hash/llm4szz*.json
        parts = result_file.parts
        commit_hash = parts[-2]  # Parent directory name

        try:
            with open(result_file, 'r') as f:
                llm_result = json.load(f)

            # Extract info
            info = extract_bug_inducing_info(llm_result)

            commit_data = commits_data[commit_hash]

            # Update commit data
            if not commit_data['repo_name'] and len(parts) >= 4:
                commit_data['repo_name'] = f"{parts[-4]}/{parts[-3]}"

            commit_data['bug_fixing_commit'] = commit_hash

            # Add changed file
            if info['llm_patch_file_names']:
                commit_data['changed_files'].extend(info['llm_patch_file_names'])

            # Add bug-inducing commits (strategy 2: SZZ+LLM)
            if info['s2_cand_cids']:
                commit_data['bug_inducing_commits'].extend(info['s2_cand_cids'])

            # Add bug-inducing commits (strategy 1: direct LLM)
            if info['s1_llm_file_final_cids']:
                commit_data['bug_inducing_commits'].extend(info['s1_llm_file_final_cids'])

            # Add buggy statements from strategy 2 (with induce_cid linkage)
            if info['s2_cand_stmts']:
                for stmt in info['s2_cand_stmts']:
                    if stmt and isinstance(stmt, dict):
                        commit_data['buggy_statements'].append({
                            'file': stmt.get('file_name', ''),
                            'lineno': stmt.get('lineno', None),
                            'statement': stmt.get('buggy_stmt', ''),
                            'induce_cid': stmt.get('induce_cid', '')  # bug-inducing commitへの紐付け
                        })

            # Add buggy statements from strategy 1
            if info['s1_ranked_stmts_infos']:
                for stmt in info['s1_ranked_stmts_infos']:
                    if stmt and isinstance(stmt, dict):
                        commit_data['buggy_statements'].append({
                            'file': stmt.get('file_name', ''),
                            'lineno': stmt.get('lineno', None),
                            'statement': stmt.get('buggy_stmt', ''),
                            'induce_cid': stmt.get('induce_cid', '')
                        })

            # Update determination status
            if info['can_determine']:
                commit_data['can_determine'] = True

            # If bug-inducing commits found (either strategy), mark as having results
            if info['s2_cand_cids'] or info['s1_llm_file_final_cids']:
                commit_data['has_bug_inducing'] = True

            # Accumulate metrics
            commit_data['total_token_cost'] += info['token_cost']
            commit_data['total_llm_calls'] += info['call_llm_times']
            commit_data['total_elapsed_time'] += info['elapsed_time']

        except Exception as e:
            print(f"⚠️  Error processing {result_file}: {e}")
            continue

    # Convert to regular dict and deduplicate lists
    final_commits = {}
    for commit_hash, data in commits_data.items():
        data['changed_files'] = list(set(data['changed_files']))
        data['bug_inducing_commits'] = list(set(data['bug_inducing_commits']))
        final_commits[commit_hash] = data

    # Generate summary statistics
    total_commits = len(final_commits)
    determined_commits = sum(1 for c in final_commits.values() if c['can_determine'])
    commits_with_bic = sum(1 for c in final_commits.values() if c.get('has_bug_inducing') or len(c['bug_inducing_commits']) > 0)
    total_bug_inducing = sum(len(set(c['bug_inducing_commits'])) for c in final_commits.values())
    total_buggy_stmts = sum(len(c['buggy_statements']) for c in final_commits.values())

    summary = {
        'project': project_dir.name,
        'total_bug_fixing_commits': total_commits,
        'commits_with_bug_inducing': commits_with_bic,
        'bug_inducing_rate': f"{(commits_with_bic/total_commits*100):.1f}%" if total_commits > 0 else "0%",
        'can_determine_commits': determined_commits,
        'determination_rate': f"{(determined_commits/total_commits*100):.1f}%" if total_commits > 0 else "0%",
        'total_bug_inducing_commits': total_bug_inducing,
        'total_buggy_statements': total_buggy_stmts,
        'avg_bug_inducing_per_commit': f"{(total_bug_inducing/commits_with_bic):.2f}" if commits_with_bic > 0 else "0",
        'total_token_cost': sum(c['total_token_cost'] for c in final_commits.values()),
        'total_llm_calls': sum(c['total_llm_calls'] for c in final_commits.values()),
        'total_elapsed_time_sec': sum(c['total_elapsed_time'] for c in final_commits.values())
    }

    return {
        'commits': final_commits,
        'summary': summary
    }


def export_to_csv(results: Dict[str, Any], output_file: str):
    """
    Export aggregated results to CSV format.

    Args:
        results: Aggregated results dictionary
        output_file: Path to output CSV file
    """
    csv_file = output_file.replace('.json', '.csv')

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Project', 'Repo', 'Bug-Fixing Commit', 'Changed Files',
            'Can Determine', 'Bug-Inducing Commits', 'Num Bug-Inducing',
            'Num Buggy Statements', 'Token Cost', 'LLM Calls', 'Elapsed Time (s)'
        ])

        # Data rows
        for project, data in results.items():
            for commit_hash, commit_data in data['commits'].items():
                writer.writerow([
                    project,
                    commit_data['repo_name'],
                    commit_hash,
                    ';'.join(commit_data['changed_files']),
                    commit_data['can_determine'],
                    ';'.join(commit_data['bug_inducing_commits']),
                    len(commit_data['bug_inducing_commits']),
                    len(commit_data['buggy_statements']),
                    commit_data['total_token_cost'],
                    commit_data['total_llm_calls'],
                    f"{commit_data['total_elapsed_time']:.2f}"
                ])

    print(f"✅ Exported CSV: {csv_file}")


def print_summary(results: Dict[str, Any]):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    for project, data in results.items():
        summary = data['summary']
        print(f"\n📊 {project}")
        print(f"   Total bug-fixing commits:    {summary['total_bug_fixing_commits']}")
        print(f"   Commits with bug-inducing:   {summary['commits_with_bug_inducing']} ({summary['bug_inducing_rate']})")
        print(f"   can_determine=True commits:  {summary['can_determine_commits']} ({summary['determination_rate']})")
        print(f"   Total bug-inducing commits:  {summary['total_bug_inducing_commits']}")
        print(f"   Avg bug-inducing per commit: {summary['avg_bug_inducing_per_commit']}")
        print(f"   Total buggy statements:      {summary['total_buggy_statements']}")
        print(f"   Total LLM calls:             {summary['total_llm_calls']}")
        print(f"   Total elapsed time:          {summary['total_elapsed_time_sec']:.1f}s ({summary['total_elapsed_time_sec']/60:.1f}m)")

    # Overall summary if multiple projects
    if len(results) > 1:
        total_fixes = sum(d['summary']['total_bug_fixing_commits'] for d in results.values())
        total_with_bic = sum(d['summary']['commits_with_bug_inducing'] for d in results.values())
        total_can_det = sum(d['summary']['can_determine_commits'] for d in results.values())
        total_inducing = sum(d['summary']['total_bug_inducing_commits'] for d in results.values())
        total_stmts = sum(d['summary']['total_buggy_statements'] for d in results.values())

        print(f"\n{'='*80}")
        print("🎯 OVERALL SUMMARY")
        print(f"   Projects:                    {len(results)}")
        print(f"   Total bug-fixing commits:    {total_fixes}")
        print(f"   Commits with bug-inducing:   {total_with_bic} ({total_with_bic/total_fixes*100:.1f}%)")
        print(f"   can_determine=True commits:  {total_can_det} ({total_can_det/total_fixes*100:.1f}%)")
        print(f"   Total bug-inducing commits:  {total_inducing}")
        print(f"   Total buggy statements:      {total_stmts}")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Aggregate LLM4SZZ analysis results'
    )

    parser.add_argument(
        '--project',
        help='Single project name (e.g., jfreechart)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Aggregate all projects'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file path'
    )

    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Also export results to CSV format'
    )

    args = parser.parse_args()

    if not args.project and not args.all:
        parser.error('Must specify either --project or --all')

    base_dir = Path('llm4szz_datasets')

    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        return

    # Determine which projects to process
    if args.project:
        projects = [args.project]
    else:
        projects = [
            'commons-lang', 'commons-io', 'hibernate-orm', 'dubbo',
            'spoon', 'maven', 'storm', 'jfreechart'
        ]

    # Aggregate results
    all_results = {}

    for project in projects:
        project_dir = base_dir / project
        if not project_dir.exists():
            print(f"⚠️  Project directory not found: {project_dir}")
            continue

        print(f"\n--- Processing {project} ---")
        results = aggregate_project_results(project_dir)
        all_results[project] = results

    # Save JSON output
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)

    with open(args.output, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✅ Aggregated results saved: {args.output}")

    # Export CSV if requested
    if args.export_csv:
        export_to_csv(all_results, args.output)

    # Print summary
    print_summary(all_results)


if __name__ == '__main__':
    main()
