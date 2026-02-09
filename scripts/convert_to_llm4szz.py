#!/usr/bin/env python3
"""
Convert bug_fixing_commits.json to LLM4SZZ format (issue_list.json).

Usage:
    python scripts/convert_to_llm4szz.py \
        --input batch_results/commons-lang/bug_fixing_commits.json \
        --output llm4szz_datasets/commons-lang/dataset/issue_list.json
"""

import argparse
import json
import os
from pathlib import Path


def convert_to_llm4szz_format(input_file: str, output_file: str):
    """
    Convert bug-fixing commits to LLM4SZZ format.

    Args:
        input_file: Path to bug_fixing_commits.json
        output_file: Path to output issue_list.json
    """
    # Load input data
    with open(input_file, 'r') as f:
        commits = json.load(f)

    print(f"Loaded {len(commits)} bug-fixing commits from {input_file}")

    # Convert to LLM4SZZ format
    llm4szz_data = []
    for commit in commits:
        repo_name = commit['repo_name']
        bug_fixing_commit = commit['bug_fixing_commit']

        # Create GitHub commit URL
        commit_url = f"https://github.com/{repo_name}/commit/{bug_fixing_commit}"

        llm4szz_data.append({
            'repo_name': repo_name,
            'bug_fixing_commit': bug_fixing_commit,
            'commit_url': commit_url
        })

    # Create output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save output
    with open(output_file, 'w') as f:
        json.dump(llm4szz_data, f, indent=4)

    print(f"✅ Converted to LLM4SZZ format: {output_file}")
    print(f"   {len(llm4szz_data)} entries")


def main():
    parser = argparse.ArgumentParser(
        description='Convert bug-fixing commits to LLM4SZZ format'
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Input bug_fixing_commits.json file'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output issue_list.json file'
    )

    args = parser.parse_args()

    convert_to_llm4szz_format(args.input, args.output)


if __name__ == '__main__':
    main()
