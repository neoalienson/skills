#!/usr/bin/env python3

import os
import random
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .base import StorageBackend


class GitHubStorage(StorageBackend):
    """Git-based GitHub storage backend."""

    def __init__(
        self,
        repo_url: str,
        branch: str = 'main',
        data_file: str = 'todo-data.json',
        commit_message: str = 'Update todos {timestamp}',
        clone_dir: Optional[str] = None
    ):
        self.repo_url = repo_url
        self.branch = branch
        self.data_file = data_file
        self.commit_message = commit_message
        self.clone_dir = clone_dir

    def _get_clone_dir(self) -> str:
        """Get the clone directory, creating one under project-level tmp if not specified."""
        if self.clone_dir:
            return self.clone_dir
        project_dir = Path(__file__).parent.parent
        tmp_dir = project_dir / 'tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        repo_name = self.repo_url.split('/')[-1].replace('.git', '')
        return str(tmp_dir / f'todo-git-{repo_name}')

    def _run_git(self, args, cwd=None, capture_output=True):
        """Run a git command."""
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0 and capture_output:
            print(f'Git command failed: git {" ".join(args)}')
            print(f'Error: {result.stderr}')
        return result

    def _is_ssh_url(self) -> bool:
        """Check if the repo URL is SSH format."""
        return self.repo_url.startswith('git@') or self.repo_url.startswith('ssh://')

    def load(self) -> Dict[str, Any]:
        """Load todo data from GitHub repository."""
        clone_dir = self._get_clone_dir()
        git_dir = Path(clone_dir) / '.git'

        try:
            if git_dir.exists():
                self._run_git(['fetch', 'origin', self.branch], cwd=clone_dir)
                self._run_git(['checkout', self.branch], cwd=clone_dir)
            else:
                os.makedirs(clone_dir, exist_ok=True)
                result = self._run_git([
                    'clone',
                    '--branch', self.branch,
                    self.repo_url,
                    clone_dir
                ])
                if result.returncode != 0:
                    raise RuntimeError(f'Failed to clone repository: {result.stderr}')

            data_path = Path(clone_dir) / self.data_file

            if not data_path.exists():
                return {'todos': [], 'categories': ['no category']}

            import json
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data is None:
                return {'todos': [], 'categories': ['no category']}

            if isinstance(data, list):
                return {'todos': data, 'categories': ['no category']}

            return {
                'todos': data.get('todos', []),
                'categories': data.get('categories', ['no category'])
            }

        except Exception as e:
            print(f'Error loading from GitHub: {e}')
            return {'todos': [], 'categories': ['no category']}

    def save(self, data: Dict[str, Any]) -> None:
        """Save todo data to GitHub repository."""
        clone_dir = self._get_clone_dir()
        git_dir = Path(clone_dir) / '.git'

        try:
            if git_dir.exists():
                self._run_git(['fetch', 'origin', self.branch], cwd=clone_dir)
                self._run_git(['pull', '--rebase', '-X', 'theirs', 'origin', self.branch], cwd=clone_dir)
            else:
                os.makedirs(clone_dir, exist_ok=True)
                result = self._run_git([
                    'clone',
                    '--branch', self.branch,
                    self.repo_url,
                    clone_dir
                ])
                if result.returncode != 0:
                    raise RuntimeError(f'Failed to clone repository: {result.stderr}')

            data_path = Path(clone_dir) / self.data_file
            data_path.parent.mkdir(parents=True, exist_ok=True)

            import json
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._run_git(['add', self.data_file], cwd=clone_dir, capture_output=False)

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            message = self.commit_message.format(timestamp=timestamp)

            result = self._run_git([
                'commit', '-m', message
            ], cwd=clone_dir)

            if result.returncode != 0:
                if 'nothing to commit' in result.stdout.lower():
                    return
                raise RuntimeError(f'Failed to commit: {result.stderr}')

            result = self._run_git([
                'push', '-u', 'origin', self.branch
            ], cwd=clone_dir)

            if result.returncode != 0:
                raise RuntimeError(f'Failed to push: {result.stderr}')

        except Exception as e:
            print(f'Error saving to GitHub: {e}')
            raise

    def _cleanup_clone(self, clone_dir: str) -> None:
        """Clean up the clone directory (disabled - we reuse the clone)."""
        pass

    def exists(self) -> bool:
        """Check if GitHub repository is accessible."""
        result = self._run_git([
            'ls-remote',
            '--heads',
            '--exit-code',
            self.repo_url,
            self.branch
        ])
        return result.returncode == 0
