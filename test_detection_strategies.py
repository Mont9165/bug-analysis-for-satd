#!/usr/bin/env python3
"""
Test script for bug-fixing commit detection strategies.

This script tests each detection strategy with sample commit messages
to ensure they work as expected.
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


def test_rosa_strategy():
    """Test Rosa et al. (2023) strategy."""
    print("\n=== Testing Rosa et al. (2023) Strategy ===")
    
    test_cases = [
        ("Fix bug in user authentication", True),
        ("Solve issue with database connection", True),
        ("Fix error in payment processing", True),
        ("Merge branch feature-123", False),
        ("Add new feature", False),
        ("Update documentation", False),
        ("Fix null pointer exception", False),  # Has 'fix' but 'exception' is not in Rosa's bug_words list
    ]
    
    passed = 0
    failed = 0
    
    for message, expected in test_cases:
        is_fix, pattern = detect_bug_fix_rosa(message)
        if is_fix == expected:
            print(f"✓ PASS: '{message[:50]}...' -> {is_fix} (pattern: {pattern})")
            passed += 1
        else:
            print(f"✗ FAIL: '{message[:50]}...' -> Expected {expected}, got {is_fix}")
            failed += 1
    
    print(f"\nRosa Strategy: {passed} passed, {failed} failed")
    return failed == 0


def test_pantiuchina_strategy():
    """Test Pantiuchina et al. (2020) strategy."""
    print("\n=== Testing Pantiuchina et al. (2020) Strategy ===")
    
    test_cases = [
        ("Fix bug in authentication", True),
        ("Close defect in payment module", True),
        ("Solve crash on startup", True),
        ("Fix error in database", True),
        ("Add new feature", False),
        ("Update documentation", False),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected in test_cases:
        is_fix, pattern = detect_bug_fix_pantiuchina(message)
        if is_fix == expected:
            print(f"✓ PASS: '{message[:50]}...' -> {is_fix} (pattern: {pattern})")
            passed += 1
        else:
            print(f"✗ FAIL: '{message[:50]}...' -> Expected {expected}, got {is_fix}")
            failed += 1
    
    print(f"\nPantiuchina Strategy: {passed} passed, {failed} failed")
    return failed == 0


def test_casalnuovo_strategy():
    """Test Casalnuovo et al. (2017) strategy."""
    print("\n=== Testing Casalnuovo et al. (2017) Strategy ===")
    
    test_cases = [
        ("Fix null pointer exception", True),
        ("Handle error in user input", True),
        ("Defect in payment processing", True),
        ("Bug in authentication", True),
        ("Add new feature", False),
        ("Update version to 2.0", False),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected in test_cases:
        is_fix, pattern = detect_bug_fix_casalnuovo(message)
        if is_fix == expected:
            print(f"✓ PASS: '{message[:50]}...' -> {is_fix} (pattern: {pattern})")
            passed += 1
        else:
            print(f"✗ FAIL: '{message[:50]}...' -> Expected {expected}, got {is_fix}")
            failed += 1
    
    print(f"\nCasalnuovo Strategy: {passed} passed, {failed} failed")
    return failed == 0


def test_issue_id_strategy():
    """Test Issue ID-based strategy."""
    print("\n=== Testing Issue ID Strategy ===")
    
    # Load config
    config = load_config('configs/bug_fix_patterns.yaml')
    
    test_cases = [
        ("LANG-1234: Fix null pointer exception", "apache/commons-lang", True),
        ("IO-567: Fix file reading issue", "apache/commons-io", True),
        ("HHH-890: Resolve database connection", "hibernate/hibernate-orm", True),
        ("Fix #123: Handle user input", "INRIA/spoon", True),
        ("Merge branch develop", "apache/commons-lang", False),
        ("Add feature for user management", "apache/commons-lang", False),
    ]
    
    passed = 0
    failed = 0
    
    for message, repo, expected in test_cases:
        is_fix, pattern = detect_bug_fix_issue_id(message, repo, config)
        if is_fix == expected:
            print(f"✓ PASS: '{message[:50]}...' [{repo}] -> {is_fix} (pattern: {pattern})")
            passed += 1
        else:
            print(f"✗ FAIL: '{message[:50]}...' [{repo}] -> Expected {expected}, got {is_fix}")
            failed += 1
    
    print(f"\nIssue ID Strategy: {passed} passed, {failed} failed")
    return failed == 0


def test_combined_strategy():
    """Test combined strategy."""
    print("\n=== Testing Combined Strategy ===")
    
    # Load config
    config = load_config('configs/bug_fix_patterns.yaml')
    
    test_cases = [
        ("LANG-1234: Fix null pointer", "apache/commons-lang", True, "issue_id"),
        ("Fix bug in authentication", "unknown/repo", True, "strict"),
        ("Solve crash on startup", "unknown/repo", True, "pantiuchina"),
        ("Error in database connection", "unknown/repo", True, "simple"),
        ("Add new feature", "unknown/repo", False, None),
    ]
    
    passed = 0
    failed = 0
    
    for message, repo, expected_fix, expected_method in test_cases:
        is_fix, method, pattern = detect_bug_fix_combined(message, repo, config)
        if is_fix == expected_fix:
            print(f"✓ PASS: '{message[:40]}...' -> {is_fix} (method: {method}, pattern: {pattern})")
            passed += 1
        else:
            print(f"✗ FAIL: '{message[:40]}...' -> Expected {expected_fix}, got {is_fix}")
            failed += 1
    
    print(f"\nCombined Strategy: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("="*70)
    print("Bug-Fixing Commit Detection Strategy Tests")
    print("="*70)
    
    all_passed = True
    
    all_passed &= test_rosa_strategy()
    all_passed &= test_pantiuchina_strategy()
    all_passed &= test_casalnuovo_strategy()
    all_passed &= test_issue_id_strategy()
    all_passed &= test_combined_strategy()
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*70)
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("="*70)
        sys.exit(1)


if __name__ == '__main__':
    main()
