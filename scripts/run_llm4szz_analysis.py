#!/usr/bin/env python3
"""
Run LLM4SZZ analysis on bug-fixing commits.

This script takes bug-fixing commits as input, validates LLM4SZZ installation,
prepares the dataset, runs the analysis, and exports the results.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional


def validate_llm4szz(llm4szz_path: str) -> bool:
    """
    Validate that LLM4SZZ is properly installed.
    
    Args:
        llm4szz_path: Path to LLM4SZZ installation
        
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(llm4szz_path):
        print(f"Error: LLM4SZZ path does not exist: {llm4szz_path}", file=sys.stderr)
        return False
    
    # Check for expected files/directories in LLM4SZZ
    expected_items = ['README.md', 'requirements.txt']  # Adjust based on actual LLM4SZZ structure
    
    found_items = os.listdir(llm4szz_path)
    has_expected = any(item in found_items for item in expected_items)
    
    if not has_expected:
        print(f"Warning: LLM4SZZ directory structure may be incomplete at {llm4szz_path}", file=sys.stderr)
        print(f"Expected to find one of: {expected_items}", file=sys.stderr)
        print(f"Found: {found_items[:5]}", file=sys.stderr)
    
    return True


def load_bug_fixing_commits(input_file: str) -> List[Dict]:
    """
    Load bug-fixing commits from JSON file.
    
    Args:
        input_file: Path to bug-fixing commits JSON file
        
    Returns:
        List of bug-fixing commit dictionaries
    """
    try:
        with open(input_file, 'r') as f:
            commits = json.load(f)
        
        print(f"Loaded {len(commits)} bug-fixing commits from {input_file}")
        return commits
    except Exception as e:
        print(f"Error loading bug-fixing commits: {e}", file=sys.stderr)
        return []


def prepare_llm4szz_dataset(commits: List[Dict], output_path: str) -> str:
    """
    Prepare dataset in LLM4SZZ format.
    
    Args:
        commits: List of bug-fixing commits
        output_path: Path to save the dataset
        
    Returns:
        Path to the prepared dataset file
    """
    # Transform to LLM4SZZ format
    # Based on LLM4SZZ's expected input format from final_all_dataset.json
    llm4szz_data = []
    
    for commit in commits:
        llm4szz_data.append({
            'repo_name': commit['repo_name'],
            'fix_commit_hash': commit['bug_fixing_commit'],
            'commit_message': commit['commit_message'],
            'author': commit.get('author', 'Unknown'),
            'date': commit.get('date', '')
        })
    
    # Save in LLM4SZZ format
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(llm4szz_data, f, indent=2)
    
    print(f"Prepared LLM4SZZ dataset: {output_path}")
    return output_path


def run_llm4szz_analysis(
    llm4szz_path: str,
    dataset_file: str,
    model: str = "Qwen/Qwen3-8B",
    output_dir: str = "./output"
) -> Optional[str]:
    """
    Run LLM4SZZ analysis on the prepared dataset.
    
    Args:
        llm4szz_path: Path to LLM4SZZ installation
        dataset_file: Path to prepared dataset
        model: LLM model to use for analysis
        output_dir: Directory to save results
        
    Returns:
        Path to results file if successful, None otherwise
    """
    print(f"Running LLM4SZZ analysis with model: {model}")
    print(f"This may take a while depending on the number of commits and model size...")
    
    # Note: This is a placeholder for actual LLM4SZZ execution
    # The actual command would depend on LLM4SZZ's CLI interface
    # This script provides a framework that users can adapt
    
    print("\n" + "="*60)
    print("IMPORTANT: LLM4SZZ Integration Instructions")
    print("="*60)
    print(f"\nTo run LLM4SZZ analysis, you need to:")
    print(f"1. Navigate to the LLM4SZZ directory: cd {llm4szz_path}")
    print(f"2. Activate the appropriate Python environment")
    print(f"3. Run the LLM4SZZ analysis script with the prepared dataset:")
    print(f"   python <llm4szz_main_script> \\")
    print(f"       --input {dataset_file} \\")
    print(f"       --model {model} \\")
    print(f"       --output {output_dir}")
    print(f"\nThe exact command depends on LLM4SZZ's implementation.")
    print(f"Refer to LLM4SZZ documentation at: https://github.com/Mont9165/LLM4SZZ")
    print("="*60 + "\n")
    
    # Create a placeholder results file for demonstration
    results = []
    commits_data = json.load(open(dataset_file, 'r'))
    
    for commit in commits_data:
        results.append({
            'repo_name': commit['repo_name'],
            'bug_fixing_commit': commit['fix_commit_hash'],
            'bug_inducing_commits': [],  # Would be populated by actual LLM4SZZ
            'strategy_used': 'pending',
            'can_determine': False,
            'note': 'Placeholder - Run actual LLM4SZZ analysis'
        })
    
    # Save placeholder results
    os.makedirs(output_dir, exist_ok=True)
    results_file = os.path.join(output_dir, 'bug_inducing_commits.json')
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Placeholder results saved to: {results_file}")
    print("Note: These are placeholder results. Run actual LLM4SZZ for real analysis.")
    
    return results_file


def export_results(results_file: str, output_dir: str) -> None:
    """
    Export and summarize LLM4SZZ results.
    
    Args:
        results_file: Path to LLM4SZZ results file
        output_dir: Directory to save exported results
    """
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Generate summary
        total = len(results)
        determined = sum(1 for r in results if r.get('can_determine', False))
        
        summary = {
            'total_bug_fixes': total,
            'bug_inducing_identified': determined,
            'identification_rate': f"{(determined/total*100):.1f}%" if total > 0 else "0%",
            'results_file': results_file
        }
        
        summary_file = os.path.join(output_dir, 'analysis_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print("Analysis Summary")
        print('='*60)
        print(f"Total bug-fixing commits: {total}")
        print(f"Bug-inducing commits identified: {determined}")
        print(f"Identification rate: {summary['identification_rate']}")
        print(f"\nDetailed results: {results_file}")
        print(f"Summary: {summary_file}")
        print('='*60)
        
    except Exception as e:
        print(f"Error exporting results: {e}", file=sys.stderr)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Run LLM4SZZ analysis on bug-fixing commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python run_llm4szz_analysis.py \\
      --input ./output/bug_fixing_commits.json \\
      --llm4szz-path /path/to/LLM4SZZ \\
      --model Qwen/Qwen3-8B

  # With custom output directory
  python run_llm4szz_analysis.py \\
      --input ./output/bug_fixing_commits.json \\
      --llm4szz-path /path/to/LLM4SZZ \\
      --model Qwen/Qwen3-8B \\
      --output-dir ./results
        """
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Path to bug-fixing commits JSON file'
    )
    
    parser.add_argument(
        '--llm4szz-path',
        required=True,
        help='Path to LLM4SZZ installation directory'
    )
    
    parser.add_argument(
        '--model',
        default='Qwen/Qwen3-8B',
        help='LLM model to use for analysis (default: Qwen/Qwen3-8B)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for results (default: ./output)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    if not validate_llm4szz(args.llm4szz_path):
        print("Warning: LLM4SZZ validation failed. Proceeding anyway...", file=sys.stderr)
    
    # Load bug-fixing commits
    commits = load_bug_fixing_commits(args.input)
    if not commits:
        print("Error: No bug-fixing commits to analyze", file=sys.stderr)
        sys.exit(1)
    
    # Prepare dataset for LLM4SZZ
    dataset_file = os.path.join(args.output_dir, 'llm4szz_dataset.json')
    prepare_llm4szz_dataset(commits, dataset_file)
    
    # Run LLM4SZZ analysis
    results_file = run_llm4szz_analysis(
        llm4szz_path=args.llm4szz_path,
        dataset_file=dataset_file,
        model=args.model,
        output_dir=args.output_dir
    )
    
    if results_file:
        # Export and summarize results
        export_results(results_file, args.output_dir)
        print(f"\nSuccess! Analysis complete.")
        sys.exit(0)
    else:
        print("\nFailed to complete analysis", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
