"""Tests for branch fallback logic in extract_bug_fixing_commits."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from extract_bug_fixing_commits import get_commits, get_default_branch

GIT_ENV = {
    **os.environ,
    'GIT_AUTHOR_NAME': 'Test',
    'GIT_AUTHOR_EMAIL': 'test@test.com',
    'GIT_COMMITTER_NAME': 'Test',
    'GIT_COMMITTER_EMAIL': 'test@test.com',
}


class TestGetDefaultBranch(unittest.TestCase):
    """Tests for get_default_branch function."""

    def setUp(self):
        """Create a temporary git repo for testing."""
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(['git', 'init', '-b', 'master', self.test_dir],
                       capture_output=True, text=True, check=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'initial commit'],
                       cwd=self.test_dir, capture_output=True, text=True, check=True,
                       env=GIT_ENV)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_commits_with_correct_branch(self):
        """Test that get_commits works when the branch exists."""
        commits = get_commits(self.test_dir, 'master')
        self.assertGreater(len(commits), 0)
        self.assertEqual(commits[0]['message'], 'initial commit')

    def test_get_commits_wrong_branch_no_remote(self):
        """Test that get_commits with wrong branch and no remote returns empty list."""
        commits = get_commits(self.test_dir, 'nonexistent')
        self.assertEqual(commits, [])


class TestGetDefaultBranchWithRemote(unittest.TestCase):
    """Tests for default branch detection with a simulated remote."""

    def setUp(self):
        """Create a bare 'remote' repo and a clone to simulate realistic setup."""
        self.tmpdir = tempfile.mkdtemp()
        self.bare_dir = os.path.join(self.tmpdir, 'bare.git')
        self.clone_dir = os.path.join(self.tmpdir, 'clone')
        subprocess.run(['git', 'init', '--bare', '-b', 'master', self.bare_dir],
                       capture_output=True, text=True, check=True)
        subprocess.run(['git', 'clone', self.bare_dir, self.clone_dir],
                       capture_output=True, text=True, check=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'initial'],
                       cwd=self.clone_dir, capture_output=True, text=True, check=True,
                       env=GIT_ENV)
        subprocess.run(['git', 'push'],
                       cwd=self.clone_dir, capture_output=True, text=True, check=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_default_branch(self):
        """Test that get_default_branch detects 'master'."""
        default = get_default_branch(self.clone_dir)
        self.assertEqual(default, 'master')

    def test_get_commits_fallback_to_default_branch(self):
        """Test that get_commits falls back to default branch when specified branch doesn't exist."""
        commits = get_commits(self.clone_dir, 'main')
        self.assertGreater(len(commits), 0)
        self.assertEqual(commits[0]['message'], 'initial')

    def test_get_commits_specified_branch_works(self):
        """Test that get_commits works when the correct branch is specified."""
        commits = get_commits(self.clone_dir, 'master')
        self.assertGreater(len(commits), 0)


if __name__ == '__main__':
    unittest.main()
