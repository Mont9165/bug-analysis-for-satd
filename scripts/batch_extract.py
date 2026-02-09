#!/usr/bin/env python3
"""
Batch extraction of bug-fixing commits from multiple repositories.

This script processes multiple repositories defined in a configuration file
and extracts bug-fixing commits from each using the specified detection strategy.

Usage:
    python scripts/batch_extract.py --config configs/bug_fix_patterns.yaml
    python scripts/batch_extract.py --config configs/bug_fix_patterns.yaml --strategy issue_id
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required for batch processing", file=sys.stderr)
    print("Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


def load_config(config_file: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for batch extraction."""
    parser = argparse.ArgumentParser(
        description='Batch extract bug-fixing commits from multiple repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all repositories with combined strategy
  python scripts/batch_extract.py --config configs/bug_fix_patterns.yaml

  # Use specific strategy for all repositories
  python scripts/batch_extract.py \\
      --config configs/bug_fix_patterns.yaml \\
      --strategy issue_id

  # Custom output directory
  python scripts/batch_extract.py \\
      --config configs/bug_fix_patterns.yaml \\
      --output-dir ./batch_results
        """
    )
    
    parser.add_argument(
        '--config',
        default='configs/bug_fix_patterns.yaml',
        help='Configuration file with repository list and patterns (default: configs/bug_fix_patterns.yaml)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Base output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--strategy',
        default='combined',
        choices=['simple', 'strict', 'pantiuchina', 'issue_id', 'combined'],
        help='Bug-fix detection strategy (default: combined)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    print(f"Loading configuration from {args.config}...")
    config = load_config(args.config)
    
    # Get target repositories
    repos = config.get('target_repositories', [])
    if not repos:
        print("Error: No target repositories defined in config file", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(repos)} repositories to process")
    print(f"Using detection strategy: {args.strategy}")
    print()
    
    # Process each repository
    successful = 0
    failed = 0
    
    for i, repo in enumerate(repos, 1):
        url = repo.get('url')
        branch = repo.get('branch', 'main')
        
        if not url:
            print(f"Warning: Repository {i} has no URL, skipping", file=sys.stderr)
            continue
        
        # Extract repo name for output directory
        repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
        output_subdir = f"{args.output_dir}/{repo_name}"
        
        print(f"\n{'='*70}")
        print(f"[{i}/{len(repos)}] Processing: {url}")
        print(f"Branch: {branch}")
        print(f"Output: {output_subdir}")
        print('='*70)
        
        # Run extraction script
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    'scripts/extract_bug_fixing_commits.py',
                    '--repo-url', url,
                    '--branch', branch,
                    '--output-dir', output_subdir,
                    '--strategy', args.strategy,
                    '--config', args.config,
                ],
                check=True
            )
            successful += 1
            print(f"✓ Successfully processed {url}")
        except subprocess.CalledProcessError as e:
            failed += 1
            print(f"✗ Failed to process {url}: {e}", file=sys.stderr)
        except Exception as e:
            failed += 1
            print(f"✗ Unexpected error processing {url}: {e}", file=sys.stderr)
    
    # Print summary
    print(f"\n{'='*70}")
    print("BATCH PROCESSING SUMMARY")
    print('='*70)
    print(f"Total repositories: {len(repos)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print()
    
    if failed > 0:
        sys.exit(1)
    else:
        print("All repositories processed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()
