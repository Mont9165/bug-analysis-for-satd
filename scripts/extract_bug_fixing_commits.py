#!/usr/bin/env python3
"""
Extract bug-fixing commits from a Git repository.

This script analyzes commit messages to identify bug-fixing commits using
configurable regex patterns and outputs them in a format compatible with LLM4SZZ.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None


def load_bug_fix_patterns(config_file: Optional[str] = None) -> List[str]:
    """
    Load bug-fix detection patterns from config file or use defaults.
    
    Args:
        config_file: Path to YAML config file with patterns
        
    Returns:
        List of regex patterns for detecting bug-fix commits
    """
    default_patterns = [
        r'\bfix\b',
        r'\bfixed\b',
        r'\bfixes\b',
        r'\bbug\b',
        r'\berror\b',
        r'\bpatch\b',
        r'\brepair\b',
        r'\bresolve\b',
        r'\bresolved\b',
        r'\bcorrect\b',
        r'\bdefect\b',
    ]
    
    if config_file and yaml:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                patterns = config.get('bug_fix_patterns', {}).get('commit_messages', [])
                if patterns:
                    return patterns
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}", file=sys.stderr)
            print("Using default patterns.", file=sys.stderr)
    
    return default_patterns


def clone_repository(repo_url: str, target_dir: str) -> bool:
    """
    Clone a Git repository if it doesn't already exist.
    
    Args:
        repo_url: URL of the Git repository
        target_dir: Target directory for cloning
        
    Returns:
        True if successful, False otherwise
    """
    if os.path.exists(target_dir):
        print(f"Repository already exists at {target_dir}")
        return True
    
    print(f"Cloning repository from {repo_url}...")
    try:
        result = subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Successfully cloned repository to {target_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}", file=sys.stderr)
        return False


def get_default_branch(repo_path: str) -> Optional[str]:
    """
    Detect the default branch of a repository.
    
    Args:
        repo_path: Path to the Git repository
        
    Returns:
        Default branch name, or None if it cannot be determined
    """
    # Try symbolic-ref for the remote HEAD
    try:
        result = subprocess.run(
            ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        # Output is like "refs/remotes/origin/master"
        return result.stdout.strip().split('/')[-1]
    except subprocess.CalledProcessError:
        pass

    # Fallback: try 'git remote show origin' and parse the HEAD branch
    try:
        result = subprocess.run(
            ['git', 'remote', 'show', 'origin'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if 'HEAD branch' in line:
                return line.split(':')[-1].strip()
    except subprocess.CalledProcessError:
        pass

    return None


def get_commits(repo_path: str, branch: str = 'main') -> List[Dict[str, str]]:
    """
    Get all commits from a repository branch.
    
    Args:
        repo_path: Path to the Git repository
        branch: Branch name to analyze
        
    Returns:
        List of commit dictionaries with hash, message, author, and date
    """
    try:
        # First, try to checkout the specified branch
        checkout_result = subprocess.run(
            ['git', 'checkout', branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if checkout_result.returncode != 0:
            # Branch not found, try to detect the default branch
            default_branch = get_default_branch(repo_path)
            if default_branch and default_branch != branch:
                print(f"Warning: Branch '{branch}' not found. "
                      f"Falling back to default branch '{default_branch}'.",
                      file=sys.stderr)
                subprocess.run(
                    ['git', 'checkout', default_branch],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:
                print(f"Error: Branch '{branch}' not found and could not "
                      f"determine default branch.", file=sys.stderr)
                return []
        
        # Get commit log with specific format
        result = subprocess.run(
            ['git', 'log', '--all', '--format=%H%n%an%n%ae%n%aI%n%s%n%b%n---END---'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        lines = result.stdout.split('\n')
        i = 0
        
        while i < len(lines):
            if i + 4 < len(lines):
                commit_hash = lines[i].strip()
                author_name = lines[i + 1].strip()
                author_email = lines[i + 2].strip()
                date = lines[i + 3].strip()
                
                # Collect message lines until we hit ---END---
                message_lines = []
                i += 4
                while i < len(lines) and lines[i].strip() != '---END---':
                    message_lines.append(lines[i])
                    i += 1
                
                message = '\n'.join(message_lines).strip()
                
                if commit_hash:
                    commits.append({
                        'hash': commit_hash,
                        'author': f"{author_name} <{author_email}>",
                        'date': date,
                        'message': message
                    })
                
                i += 1  # Skip the ---END--- line
            else:
                i += 1
        
        return commits
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e.stderr}", file=sys.stderr)
        return []


def is_bug_fixing_commit(message: str, patterns: List[str]) -> bool:
    """
    Check if a commit message indicates a bug fix.
    
    Args:
        message: Commit message to analyze
        patterns: List of regex patterns to match
        
    Returns:
        True if message matches any bug-fix pattern
    """
    message_lower = message.lower()
    for pattern in patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return True
    return False


def extract_bug_fixing_commits(
    repo_url: str,
    branch: str,
    output_dir: str,
    config_file: Optional[str] = None,
    custom_patterns: Optional[List[str]] = None
) -> str:
    """
    Main function to extract bug-fixing commits from a repository.
    
    Args:
        repo_url: URL of the Git repository
        branch: Branch name to analyze
        output_dir: Directory to save output files
        config_file: Path to config file with patterns
        custom_patterns: Custom patterns to use instead of defaults
        
    Returns:
        Path to the output JSON file
    """
    # Load patterns
    if custom_patterns:
        patterns = custom_patterns
    else:
        patterns = load_bug_fix_patterns(config_file)
    
    print(f"Using {len(patterns)} bug-fix patterns for detection")
    
    # Extract repository name from URL
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    if '/' in repo_url:
        # Try to get owner/repo format
        parts = repo_url.rstrip('/').replace('.git', '').split('/')
        if len(parts) >= 2:
            repo_name = f"{parts[-2]}/{parts[-1]}"
    
    # Setup repository path
    repos_dir = os.path.join(os.path.dirname(output_dir), 'repos')
    os.makedirs(repos_dir, exist_ok=True)
    repo_path = os.path.join(repos_dir, repo_name.split('/')[-1])
    
    # Clone repository if needed
    if not clone_repository(repo_url, repo_path):
        print(f"Failed to clone repository", file=sys.stderr)
        return None
    
    # Get all commits
    print(f"Analyzing commits on branch '{branch}'...")
    commits = get_commits(repo_path, branch)
    print(f"Found {len(commits)} total commits")
    
    # Filter bug-fixing commits
    bug_fixing_commits = []
    for commit in commits:
        if is_bug_fixing_commit(commit['message'], patterns):
            bug_fixing_commits.append({
                'repo_name': repo_name,
                'bug_fixing_commit': commit['hash'],
                'commit_message': commit['message'],
                'author': commit['author'],
                'date': commit['date']
            })
    
    print(f"Identified {len(bug_fixing_commits)} bug-fixing commits")
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'bug_fixing_commits.json')
    
    with open(output_file, 'w') as f:
        json.dump(bug_fixing_commits, f, indent=2)
    
    print(f"Results saved to {output_file}")
    return output_file


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract bug-fixing commits from a Git repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --output-dir ./output

  # With custom config file
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --output-dir ./output \\
      --config configs/bug_fix_patterns.yaml

  # With custom patterns
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --output-dir ./output \\
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
        '--output-dir',
        default='./output',
        help='Output directory for results (default: ./output)'
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
    
    args = parser.parse_args()
    
    # Check if git is available
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: git is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)
    
    # Warn if PyYAML is not available but config is requested
    if args.config and not yaml:
        print("Warning: PyYAML not installed. Cannot load config file.", file=sys.stderr)
        print("Install with: pip install PyYAML", file=sys.stderr)
        sys.exit(1)
    
    # Extract bug-fixing commits
    output_file = extract_bug_fixing_commits(
        repo_url=args.repo_url,
        branch=args.branch,
        output_dir=args.output_dir,
        config_file=args.config,
        custom_patterns=args.patterns
    )
    
    if output_file:
        print(f"\nSuccess! Bug-fixing commits extracted to: {output_file}")
        sys.exit(0)
    else:
        print("\nFailed to extract bug-fixing commits", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
