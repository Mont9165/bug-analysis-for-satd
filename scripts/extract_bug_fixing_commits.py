#!/usr/bin/env python3
"""
Extract bug-fixing commits from a Git repository.

This script analyzes commit messages to identify bug-fixing commits using
multiple detection strategies based on literature:
- Rosa et al. (2023): Strict fix+bug word matching
- Pantiuchina et al. (2020): (fix|solve|close) AND (bug|defect|...)
- Casalnuovo et al. (2017): Simple keyword matching
- Borg et al. (2019): Issue ID-based detection (JIRA/GitHub)

Output is compatible with LLM4SZZ and includes detection metadata.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


class BugFixDetectionStrategy(Enum):
    """Bug-fix detection strategies based on literature."""
    SIMPLE = "simple"           # Casalnuovo et al. - any keyword
    STRICT = "strict"           # Rosa et al. - fix AND bug words
    PANTIUCHINA = "pantiuchina" # Pantiuchina et al. - (fix|solve|close) AND (bug|...)
    ISSUE_ID = "issue_id"       # JIRA/GitHub issue ID based
    COMBINED = "combined"       # All strategies combined


def load_config(config_file: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_file: Path to YAML config file
        
    Returns:
        Configuration dictionary
    """
    if not yaml:
        raise ImportError("PyYAML is required for config file loading")
    
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}", file=sys.stderr)
        return {}


def detect_bug_fix_rosa(message: str) -> Tuple[bool, Optional[str]]:
    """
    Rosa et al. (2023) - requires fix AND bug words, excludes merge.
    
    Args:
        message: Commit message to analyze
        
    Returns:
        Tuple of (is_bug_fix, matched_pattern)
    """
    fix_words = re.compile(r'\b(fix|solve)\b', re.I)
    bug_words = re.compile(r'\b(bug|issue|problem|error|misfeature)\b', re.I)
    merge = re.compile(r'\bmerge\b', re.I)
    
    if merge.search(message):
        return False, None
    
    fix_match = fix_words.search(message)
    bug_match = bug_words.search(message)
    
    if fix_match and bug_match:
        return True, f"{fix_match.group()} + {bug_match.group()}"
    
    return False, None


def detect_bug_fix_pantiuchina(message: str) -> Tuple[bool, Optional[str]]:
    """
    Pantiuchina et al. (2020) - (fix|solve|close) AND (bug|defect|crash|fail|error).
    
    Args:
        message: Commit message to analyze
        
    Returns:
        Tuple of (is_bug_fix, matched_pattern)
    """
    fix_words = re.compile(r'\b(fix|solve|close)\b', re.I)
    bug_words = re.compile(r'\b(bug|defect|crash|fail|error)\b', re.I)
    
    fix_match = fix_words.search(message)
    bug_match = bug_words.search(message)
    
    if fix_match and bug_match:
        return True, f"{fix_match.group()} + {bug_match.group()}"
    
    return False, None


def detect_bug_fix_casalnuovo(message: str) -> Tuple[bool, Optional[str]]:
    """
    Casalnuovo et al. (2017) - simple keyword match.
    
    Args:
        message: Commit message to analyze
        
    Returns:
        Tuple of (is_bug_fix, matched_pattern)
    """
    keywords = re.compile(
        r'\b(error|defect|flaw|bug|fix|issue|mistake|fault|incorrect)\b', 
        re.I
    )
    match = keywords.search(message)
    if match:
        return True, match.group()
    return False, None


def detect_bug_fix_issue_id(message: str, repo_name: str, config: Dict) -> Tuple[bool, Optional[str]]:
    """
    Issue ID based detection (SZZ Unleashed - Borg et al., 2019).
    
    Args:
        message: Commit message to analyze
        repo_name: Repository name (e.g., 'apache/commons-lang')
        config: Configuration dictionary with patterns
        
    Returns:
        Tuple of (is_bug_fix, matched_pattern)
    """
    # Check exclusion patterns first
    exclusion_patterns = config.get('exclusion_patterns', [])
    for pattern in exclusion_patterns:
        if re.search(pattern, message):
            return False, None
    
    # Check JIRA pattern for known projects
    jira_patterns = config.get('jira_patterns', {})
    if repo_name in jira_patterns:
        jira_pattern = jira_patterns[repo_name]
        match = re.search(jira_pattern, message)
        if match:
            return True, match.group()
    
    # Check GitHub issue pattern (requires "fix" word)
    github_match = re.search(r'#\d+', message)
    if github_match:
        if re.search(r'\bfix', message, re.I):
            return True, github_match.group()
    
    return False, None


def detect_bug_fix_combined(message: str, repo_name: str, config: Dict) -> Tuple[bool, str, Optional[str]]:
    """
    Combined detection using all strategies.
    
    Args:
        message: Commit message to analyze
        repo_name: Repository name
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_bug_fix, detection_method, matched_pattern)
    """
    # Try issue ID based first (most specific)
    is_fix, pattern = detect_bug_fix_issue_id(message, repo_name, config)
    if is_fix:
        return True, "issue_id", pattern
    
    # Try Rosa et al. (strict)
    is_fix, pattern = detect_bug_fix_rosa(message)
    if is_fix:
        return True, "strict", pattern
    
    # Try Pantiuchina et al.
    is_fix, pattern = detect_bug_fix_pantiuchina(message)
    if is_fix:
        return True, "pantiuchina", pattern
    
    # Try Casalnuovo et al. (simple)
    is_fix, pattern = detect_bug_fix_casalnuovo(message)
    if is_fix:
        return True, "simple", pattern
    
    return False, None, None


def load_bug_fix_patterns(config_file: Optional[str] = None) -> List[str]:
    """
    Load bug-fix detection patterns from config file or use defaults.
    (Legacy function for backward compatibility)
    
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
            config = load_config(config_file)
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
        # First, checkout the branch
        subprocess.run(
            ['git', 'checkout', branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
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
    Check if a commit message indicates a bug fix (legacy method).
    
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
    custom_patterns: Optional[List[str]] = None,
    strategy: str = 'combined'
) -> str:
    """
    Main function to extract bug-fixing commits from a repository.
    
    Args:
        repo_url: URL of the Git repository
        branch: Branch name to analyze
        output_dir: Directory to save output files
        config_file: Path to config file with patterns
        custom_patterns: Custom patterns to use instead of defaults
        strategy: Detection strategy to use
        
    Returns:
        Path to the output JSON file
    """
    # Load configuration if using new strategies
    config = {}
    if config_file and yaml:
        try:
            config = load_config(config_file)
        except:
            pass
    
    # Load patterns for legacy mode
    if custom_patterns:
        patterns = custom_patterns
    else:
        patterns = load_bug_fix_patterns(config_file)
    
    print(f"Using detection strategy: {strategy}")
    
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
    
    # Filter bug-fixing commits based on strategy
    bug_fixing_commits = []
    
    for commit in commits:
        is_fix = False
        detection_method = None
        matched_pattern = None
        
        if strategy == 'simple':
            is_fix, matched_pattern = detect_bug_fix_casalnuovo(commit['message'])
            detection_method = 'simple'
        elif strategy == 'strict':
            is_fix, matched_pattern = detect_bug_fix_rosa(commit['message'])
            detection_method = 'strict'
        elif strategy == 'pantiuchina':
            is_fix, matched_pattern = detect_bug_fix_pantiuchina(commit['message'])
            detection_method = 'pantiuchina'
        elif strategy == 'issue_id':
            is_fix, matched_pattern = detect_bug_fix_issue_id(commit['message'], repo_name, config)
            detection_method = 'issue_id'
        elif strategy == 'combined':
            is_fix, detection_method, matched_pattern = detect_bug_fix_combined(
                commit['message'], repo_name, config
            )
        else:
            # Fallback to legacy pattern matching
            is_fix = is_bug_fixing_commit(commit['message'], patterns)
            detection_method = 'legacy'
        
        if is_fix:
            bug_fix_data = {
                'repo_name': repo_name,
                'bug_fixing_commit': commit['hash'],
                'commit_message': commit['message'],
                'author': commit['author'],
                'date': commit['date']
            }
            
            # Add detection metadata if available
            if detection_method:
                bug_fix_data['detection_method'] = detection_method
            if matched_pattern:
                bug_fix_data['matched_pattern'] = matched_pattern
            
            bug_fixing_commits.append(bug_fix_data)
    
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
  # Basic usage with combined strategy
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --output-dir ./output

  # With specific strategy
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/apache/commons-lang \\
      --branch master \\
      --strategy issue_id \\
      --config configs/bug_fix_patterns.yaml

  # With custom config file
  python extract_bug_fixing_commits.py \\
      --repo-url https://github.com/owner/repo \\
      --branch main \\
      --output-dir ./output \\
      --config configs/bug_fix_patterns.yaml

  # With custom patterns (legacy)
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
        help='Custom regex patterns for bug-fix detection (legacy mode)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['simple', 'strict', 'pantiuchina', 'issue_id', 'combined'],
        default='combined',
        help='Bug-fix detection strategy (default: combined)'
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
        custom_patterns=args.patterns,
        strategy=args.strategy
    )
    
    if output_file:
        print(f"\nSuccess! Bug-fixing commits extracted to: {output_file}")
        sys.exit(0)
    else:
        print("\nFailed to extract bug-fixing commits", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
