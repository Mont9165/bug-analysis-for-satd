#!/usr/bin/env python3
"""
Update agent_release_date in existing issue_list.json files.

Usage:
    # Update single file
    python scripts/update_agent_date.py \
        --file llm4szz_datasets/jfreechart/dataset/issue_list.json \
        --date 1970-01-01

    # Update all projects
    python scripts/update_agent_date.py --all --date 1970-01-01
"""

import argparse
import json
import os
from pathlib import Path


def update_agent_date(file_path: str, agent_release_date: str, dry_run: bool = False):
    """
    Update agent_release_date in an issue_list.json file.

    Args:
        file_path: Path to issue_list.json
        agent_release_date: New agent release date (ISO format: YYYY-MM-DD)
        dry_run: If True, show changes without saving
    """
    # Load file
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Update each entry
    updated_count = 0
    for entry in data:
        old_date = entry.get('agent_release_date')
        entry['agent_release_date'] = agent_release_date
        if old_date != agent_release_date:
            updated_count += 1

    print(f"{'[DRY RUN] ' if dry_run else ''}Updated {updated_count}/{len(data)} entries in {file_path}")
    print(f"  agent_release_date: {agent_release_date}")

    # Save if not dry run
    if not dry_run:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ Saved: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Update agent_release_date in LLM4SZZ dataset files'
    )

    parser.add_argument(
        '--file',
        help='Path to single issue_list.json file to update'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Update all projects in llm4szz_datasets/'
    )

    parser.add_argument(
        '--date',
        required=True,
        help='New agent release date (ISO format: YYYY-MM-DD). '
             'Use "1970-01-01" to disable date filtering.'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually saving'
    )

    args = parser.parse_args()

    if not args.file and not args.all:
        parser.error('Must specify either --file or --all')

    if args.file:
        # Update single file
        update_agent_date(args.file, args.date, args.dry_run)
    elif args.all:
        # Update all projects
        base_dir = Path('llm4szz_datasets')
        if not base_dir.exists():
            print(f"❌ Directory not found: {base_dir}")
            return

        projects = [
            'commons-lang', 'commons-io', 'hibernate-orm', 'dubbo',
            'spoon', 'maven', 'storm', 'jfreechart'
        ]

        for project in projects:
            issue_list = base_dir / project / 'dataset' / 'issue_list.json'
            if issue_list.exists():
                print(f"\n--- {project} ---")
                update_agent_date(str(issue_list), args.date, args.dry_run)
            else:
                print(f"⚠️  Not found: {issue_list}")


if __name__ == '__main__':
    main()
