#!/usr/bin/env python3
"""
Demo script showing the enhanced bug-fixing commit detection capabilities.

This script demonstrates:
1. Different detection strategies
2. Detection metadata
3. Strategy comparison
"""

import sys
sys.path.insert(0, 'scripts')

from extract_bug_fixing_commits import (
    detect_bug_fix_rosa,
    detect_bug_fix_pantiuchina,
    detect_bug_fix_casalnuovo,
    detect_bug_fix_issue_id,
    detect_bug_fix_combined,
    load_config
)


def demo_strategies():
    """Demonstrate different detection strategies."""
    
    print("="*70)
    print("Enhanced Bug-Fixing Commit Detection Demo")
    print("="*70)
    print()
    
    # Sample commit messages
    test_messages = [
        "LANG-1234: Fix null pointer exception in StringUtils",
        "Fix bug in user authentication module",
        "Solve crash on application startup",
        "Error in database connection handling",
        "Add new feature for user profiles",
        "Merge pull request #456 from feature-branch",
    ]
    
    # Load configuration
    config = load_config('configs/bug_fix_patterns.yaml')
    repo_name = "apache/commons-lang"
    
    print("Sample Commit Messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"{i}. {msg}")
    print()
    
    # Test each strategy
    print("\n" + "="*70)
    print("Strategy Comparison")
    print("="*70)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i}: \"{message[:50]}...\"")
        
        # Test each individual strategy
        is_fix_rosa, pattern_rosa = detect_bug_fix_rosa(message)
        is_fix_pant, pattern_pant = detect_bug_fix_pantiuchina(message)
        is_fix_casal, pattern_casal = detect_bug_fix_casalnuovo(message)
        is_fix_issue, pattern_issue = detect_bug_fix_issue_id(message, repo_name, config)
        is_fix_comb, method_comb, pattern_comb = detect_bug_fix_combined(message, repo_name, config)
        
        print(f"  Rosa (strict):      {'✓' if is_fix_rosa else '✗'}  {pattern_rosa or ''}")
        print(f"  Pantiuchina:        {'✓' if is_fix_pant else '✗'}  {pattern_pant or ''}")
        print(f"  Casalnuovo (simple):{'✓' if is_fix_casal else '✗'}  {pattern_casal or ''}")
        print(f"  Issue ID:           {'✓' if is_fix_issue else '✗'}  {pattern_issue or ''}")
        print(f"  Combined:           {'✓' if is_fix_comb else '✗'}  [{method_comb}] {pattern_comb or ''}")
    
    # Strategy statistics
    print("\n" + "="*70)
    print("Detection Statistics")
    print("="*70)
    
    strategies = {
        "Rosa (strict)": [detect_bug_fix_rosa(msg)[0] for msg in test_messages],
        "Pantiuchina": [detect_bug_fix_pantiuchina(msg)[0] for msg in test_messages],
        "Casalnuovo (simple)": [detect_bug_fix_casalnuovo(msg)[0] for msg in test_messages],
        "Issue ID": [detect_bug_fix_issue_id(msg, repo_name, config)[0] for msg in test_messages],
        "Combined": [detect_bug_fix_combined(msg, repo_name, config)[0] for msg in test_messages],
    }
    
    for strategy, results in strategies.items():
        detected = sum(results)
        print(f"{strategy:25s}: {detected}/{len(test_messages)} commits detected ({detected/len(test_messages)*100:.1f}%)")
    
    print("\n" + "="*70)
    print("Key Observations:")
    print("="*70)
    print("1. Issue ID strategy: Most precise, requires issue tracker ID")
    print("2. Rosa (strict): Balance between precision and recall")
    print("3. Pantiuchina: Similar to Rosa with expanded keywords")
    print("4. Casalnuovo (simple): Highest recall, may have false positives")
    print("5. Combined: Provides best of all strategies with metadata")
    print()


if __name__ == '__main__':
    demo_strategies()
