#!/usr/bin/env python3
"""
Unified bug analysis pipeline.

This script combines bug-fixing commit extraction and LLM4SZZ analysis
into a single, streamlined workflow.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import functions from other scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from extract_bug_fixing_commits import extract_bug_fixing_commits, load_bug_fix_patterns
    from run_llm4szz_analysis import (
        validate_llm4szz,
        prepare_llm4szz_dataset,
        run_llm4szz_analysis,
        export_results,
        load_bug_fixing_commits
    )
except ImportError as e:
    print(f"Error importing required modules: {e}", file=sys.stderr)
    print("Make sure all scripts are in the same directory.", file=sys.stderr)
    sys.exit(1)


def run_full_pipeline(
    repo_url: str,
    branch: str,
    llm4szz_path: str,
    output_dir: str = "./output",
    config_file: str = None,
    custom_patterns: list = None,
    model: str = "Qwen/Qwen3-8B",
    strategy: str = "combined"
) -> bool:
    """
    Run the complete bug analysis pipeline.
    
    Args:
        repo_url: Git repository URL to analyze
        branch: Branch name to analyze
        llm4szz_path: Path to LLM4SZZ installation
        output_dir: Output directory for all results
        config_file: Path to config file with bug-fix patterns
        custom_patterns: Custom patterns for bug-fix detection
        model: LLM model to use for analysis
        strategy: Bug-fix detection strategy
        
    Returns:
        True if successful, False otherwise
    """
    print("="*70)
    print("UNIFIED BUG ANALYSIS PIPELINE")
    print("="*70)
    print(f"Repository: {repo_url}")
    print(f"Branch: {branch}")
    print(f"Strategy: {strategy}")
    print(f"Model: {model}")
    print(f"Output: {output_dir}")
    print("="*70 + "\n")
    
    # Phase 1: Extract bug-fixing commits
    print("\n" + "="*70)
    print("PHASE 1: Extracting Bug-Fixing Commits")
    print("="*70 + "\n")
    
    bug_fix_file = extract_bug_fixing_commits(
        repo_url=repo_url,
        branch=branch,
        output_dir=output_dir,
        config_file=config_file,
        custom_patterns=custom_patterns,
        strategy=strategy
    )
    
    if not bug_fix_file or not os.path.exists(bug_fix_file):
        print("\nPhase 1 failed: Could not extract bug-fixing commits", file=sys.stderr)
        return False
    
    # Check if we have any bug-fixing commits
    commits = load_bug_fixing_commits(bug_fix_file)
    if not commits:
        print("\nNo bug-fixing commits found. Pipeline complete.", file=sys.stderr)
        return True
    
    print(f"\nPhase 1 complete: Found {len(commits)} bug-fixing commits")
    
    # Phase 2: Run LLM4SZZ analysis
    print("\n" + "="*70)
    print("PHASE 2: Running LLM4SZZ Analysis")
    print("="*70 + "\n")
    
    # Validate LLM4SZZ
    if not validate_llm4szz(llm4szz_path):
        print("Warning: LLM4SZZ validation failed. Proceeding anyway...", file=sys.stderr)
    
    # Prepare dataset
    dataset_file = os.path.join(output_dir, 'llm4szz_dataset.json')
    prepare_llm4szz_dataset(commits, dataset_file)
    
    # Run analysis
    results_file = run_llm4szz_analysis(
        llm4szz_path=llm4szz_path,
        dataset_file=dataset_file,
        model=model,
        output_dir=output_dir
    )
    
    if not results_file:
        print("\nPhase 2 failed: LLM4SZZ analysis did not complete", file=sys.stderr)
        return False
    
    # Export results
    export_results(results_file, output_dir)
    
    print(f"\nPhase 2 complete: Results saved to {output_dir}")
    
    # Final summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    print(f"\nAll results saved to: {output_dir}")
    print(f"  - Bug-fixing commits: {bug_fix_file}")
    print(f"  - LLM4SZZ dataset: {dataset_file}")
    print(f"  - Bug-inducing commits: {results_file}")
    print(f"  - Summary: {os.path.join(output_dir, 'analysis_summary.json')}")
    print("="*70 + "\n")
    
    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Unified bug analysis pipeline combining commit extraction and LLM4SZZ analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python full_pipeline.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --llm4szz-path /path/to/LLM4SZZ

  # With custom output directory and model
  python full_pipeline.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --llm4szz-path /path/to/LLM4SZZ \\
      --output-dir ./results \\
      --model Qwen/Qwen3-8B

  # With custom config file
  python full_pipeline.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --llm4szz-path /path/to/LLM4SZZ \\
      --config configs/bug_fix_patterns.yaml

  # With custom patterns
  python full_pipeline.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --llm4szz-path /path/to/LLM4SZZ \\
      --patterns "\\bfix\\b" "\\bbug\\b" "\\bpatch\\b"
        """
    )
    
    parser.add_argument(
        '--repo-url',
        required=True,
        help='Git repository URL to analyze'
    )
    
    parser.add_argument(
        '--branch',
        default='main',
        help='Branch name to analyze (default: main)'
    )
    
    parser.add_argument(
        '--llm4szz-path',
        required=True,
        help='Path to LLM4SZZ installation directory'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for all results (default: ./output)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to YAML config file with bug-fix patterns'
    )
    
    parser.add_argument(
        '--patterns',
        nargs='+',
        help='Custom regex patterns for bug-fix detection'
    )
    
    parser.add_argument(
        '--model',
        default='Qwen/Qwen3-8B',
        help='LLM model to use for analysis (default: Qwen/Qwen3-8B)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['simple', 'strict', 'pantiuchina', 'issue_id', 'combined'],
        default='combined',
        help='Bug-fix detection strategy (default: combined)'
    )
    
    args = parser.parse_args()
    
    # Run the full pipeline
    success = run_full_pipeline(
        repo_url=args.repo_url,
        branch=args.branch,
        llm4szz_path=args.llm4szz_path,
        output_dir=args.output_dir,
        config_file=args.config,
        custom_patterns=args.patterns,
        model=args.model,
        strategy=args.strategy
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
