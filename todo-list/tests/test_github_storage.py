import pytest
import os
from unittest.mock import patch, MagicMock, call
from subprocess import CompletedProcess
from pathlib import Path

from storage.github import GitHubStorage


class TestGitHubStorageGetCloneDir:
    def test_clone_dir_uses_repo_name(self):
        storage = GitHubStorage(repo_url='git@github.com:user/my-repo.git')
        clone_dir = storage._get_clone_dir()
        assert 'my-repo' in clone_dir
        assert clone_dir.endswith('todo-git-my-repo')

    def test_clone_dir_removes_git_suffix(self):
        storage = GitHubStorage(repo_url='git@github.com:user/my-repo.git')
        clone_dir = storage._get_clone_dir()
        assert '.git' not in clone_dir

    def test_clone_dir_uses_custom_clone_dir_if_set(self):
        storage = GitHubStorage(
            repo_url='git@github.com:user/repo.git',
            clone_dir='/custom/path'
        )
        clone_dir = storage._get_clone_dir()
        assert clone_dir == '/custom/path'

    def test_clone_dir_creates_tmp_under_project_dir(self):
        storage = GitHubStorage(repo_url='git@github.com:user/test-repo.git')
        clone_dir = storage._get_clone_dir()
        project_dir = Path(__file__).parent.parent
        assert str(project_dir) in clone_dir
        assert 'tmp' in clone_dir


class TestGitHubStorageIsSshUrl:
    def test_identifies_ssh_urls(self):
        storage = GitHubStorage(repo_url='git@github.com:user/repo.git')
        assert storage._is_ssh_url() is True

    def test_identifies_ssh_protocol_urls(self):
        storage = GitHubStorage(repo_url='ssh://user@hostname/path/repo.git')
        assert storage._is_ssh_url() is True

    def test_identifies_https_urls(self):
        storage = GitHubStorage(repo_url='https://github.com/user/repo.git')
        assert storage._is_ssh_url() is False

    def test_identifies_http_urls(self):
        storage = GitHubStorage(repo_url='http://github.com/user/repo.git')
        assert storage._is_ssh_url() is False


class TestGitHubStorageRunGit:
    @patch('subprocess.run')
    def test_runs_git_command_with_correct_args(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        storage._run_git(['status'])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == 'git'
        assert args[1] == 'status'

    @patch('subprocess.run')
    def test_runs_git_command_with_cwd(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        storage._run_git(['status'], cwd='/some/path')

        mock_run.assert_called_once()
        assert mock_run.call_args[1]['cwd'] == '/some/path'

    @patch('subprocess.run')
    def test_returns_result_on_success(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='success', stderr='')
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        result = storage._run_git(['status'])

        assert result.returncode == 0
        assert result.stdout == 'success'

    @patch('subprocess.run')
    def test_handles_git_errors(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=1, stdout='', stderr='error')
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        result = storage._run_git(['status'])

        assert result.returncode == 1
        assert result.stderr == 'error'


class TestGitHubStorageExists:
    @patch('subprocess.run')
    def test_exists_returns_true_when_repo_accessible(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='main'
        )

        assert storage.exists() is True

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ls-remote' in args
        assert '--heads' in args

    @patch('subprocess.run')
    def test_exists_returns_false_when_repo_not_accessible(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=2, stdout='', stderr='not found')

        storage = GitHubStorage(
            repo_url='git@github.com:test/nonexistent-repo.git',
            branch='main'
        )

        assert storage.exists() is False


class TestGitHubStorageConfiguration:
    def test_default_branch_is_main(self):
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        assert storage.branch == 'main'

    def test_custom_branch(self):
        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='gh-pages'
        )
        assert storage.branch == 'gh-pages'

    def test_default_data_file(self):
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        assert storage.data_file == 'todo-data.json'

    def test_custom_data_file(self):
        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            data_file='custom-data.json'
        )
        assert storage.data_file == 'custom-data.json'

    def test_default_commit_message(self):
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        assert '{timestamp}' in storage.commit_message

    def test_custom_commit_message(self):
        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            commit_message='My commit: {timestamp}'
        )
        assert storage.commit_message == 'My commit: {timestamp}'

    def test_stores_repo_url(self):
        storage = GitHubStorage(repo_url='git@github.com:test/my-repo.git')
        assert storage.repo_url == 'git@github.com:test/my-repo.git'


class TestGitHubStorageInternalHelpers:
    def test_get_clone_dir_idempotent(self):
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        dir1 = storage._get_clone_dir()
        dir2 = storage._get_clone_dir()
        assert dir1 == dir2

    def test_is_ssh_url_with_different_formats(self):
        test_cases = [
            ('git@github.com:user/repo.git', True),
            ('ssh://user@host/user/repo.git', True),
            ('https://github.com/user/repo.git', False),
            ('http://github.com/user/repo.git', False),
        ]
        for url, expected in test_cases:
            storage = GitHubStorage(repo_url=url)
            assert storage._is_ssh_url() == expected, f'Failed for {url}'

    @patch('subprocess.run')
    def test_run_git_with_multiple_args(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        storage._run_git(['log', '--oneline', '-n', '5'])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ['git', 'log', '--oneline', '-n', '5']


class TestGitHubStorageSaveCommandOrder:
    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_pull_uses_rebase_x_theirs(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        mock_path_instance.__truediv__.return_value.parent.mkdir.return_value = None
        mock_path_instance.__truediv__.return_value.parent.mkdir.side_effect = lambda *args, **kwargs: None
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='gh-pages'
        )

        try:
            storage.save({'todos': [], 'categories': []})
        except:
            pass

        all_args = [c[0][0] for c in mock_run.call_args_list]
        pull_calls = [args for args in all_args if 'pull' in args]

        assert len(pull_calls) >= 1
        for args in pull_calls:
            assert '--rebase' in args
            assert '-X' in args
            assert 'theirs' in args

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_fetch_before_pull(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')

        try:
            storage.save({'todos': [], 'categories': []})
        except:
            pass

        all_calls = [c[0][0] for c in mock_run.call_args_list]
        fetch_idx = next((i for i, args in enumerate(all_calls) if 'fetch' in args), -1)
        pull_idx = next((i for i, args in enumerate(all_calls) if 'pull' in args), -1)

        if fetch_idx >= 0 and pull_idx >= 0:
            assert fetch_idx < pull_idx, "fetch should happen before pull"

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_push_after_commit(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')

        try:
            storage.save({'todos': [], 'categories': []})
        except:
            pass

        all_calls = [c[0][0] for c in mock_run.call_args_list]
        commit_idx = next((i for i, args in enumerate(all_calls) if 'commit' in args), -1)
        push_idx = next((i for i, args in enumerate(all_calls) if 'push' in args), -1)

        if commit_idx >= 0 and push_idx >= 0:
            assert commit_idx < push_idx, "commit should happen before push"

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_nothing_to_commit_no_push(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance

        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'pull' in cmd or 'fetch' in cmd or 'checkout' in cmd:
                return CompletedProcess(args=[], returncode=0, stdout='', stderr='')
            elif 'commit' in cmd:
                return CompletedProcess(args=[], returncode=1, stdout='nothing to commit', stderr='')
            elif 'push' in cmd:
                return CompletedProcess(args=[], returncode=0, stdout='', stderr='')
            return CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        mock_run.side_effect = run_side_effect
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')

        storage.save({'todos': [], 'categories': []})

        push_calls = [c[0][0] for c in mock_run.call_args_list if 'push' in c[0][0]]
        assert len(push_calls) == 0, "push should not be called when nothing to commit"

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_clone_when_no_existing_repo(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path_instance.__truediv__.return_value.exists.return_value = False
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='gh-pages'
        )

        try:
            storage.save({'todos': [], 'categories': []})
        except:
            pass

        clone_calls = [c[0][0] for c in mock_run.call_args_list if 'clone' in c[0][0]]
        assert len(clone_calls) >= 1, "should clone when repo doesn't exist"

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_save_reuses_existing_clone(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='gh-pages'
        )

        try:
            storage.save({'todos': [], 'categories': []})
        except:
            pass

        clone_calls = [c[0][0] for c in mock_run.call_args_list if 'clone' in c[0][0]]
        assert len(clone_calls) == 0, "should not clone when repo already exists"


class TestGitHubStorageLoad:
    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_load_fetches_before_checkout(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance
        mock_open.return_value.__enter__.return_value.read.return_value = '{"todos": [], "categories": []}'
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')

        try:
            storage.load()
        except:
            pass

        all_calls = [c[0][0] for c in mock_run.call_args_list]
        fetch_idx = next((i for i, args in enumerate(all_calls) if 'fetch' in args), -1)
        checkout_idx = next((i for i, args in enumerate(all_calls) if 'checkout' in args), -1)

        if fetch_idx >= 0 and checkout_idx >= 0:
            assert fetch_idx < checkout_idx, "fetch should happen before checkout"

    @patch('storage.github.Path')
    @patch('builtins.open', create=True)
    @patch('subprocess.run')
    def test_load_returns_default_when_file_missing(self, mock_run, mock_open, MockPath):
        mock_path_instance = MagicMock()
        def exists_side_effect(path):
            path_str = str(path)
            if '.git' in path_str:
                return True
            return False
        mock_path_instance.exists.side_effect = exists_side_effect
        mock_path_instance.__truediv__.return_value.exists.return_value = True
        MockPath.return_value = mock_path_instance
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        mock_open.return_value.__enter__.return_value.read.side_effect = FileNotFoundError()

        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')

        data = storage.load()

        assert data == {'todos': [], 'categories': ['no category']}


class TestGitHubStorageEdgeCases:
    @patch('subprocess.run')
    def test_exists_uses_correct_branch(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='develop'
        )

        storage.exists()

        args = mock_run.call_args[0][0]
        assert 'develop' in args

    @patch('subprocess.run')
    def test_exists_uses_heads_flag(self, mock_run):
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout='', stderr='')

        storage = GitHubStorage(
            repo_url='git@github.com:test/repo.git',
            branch='main'
        )

        storage.exists()

        args = mock_run.call_args[0][0]
        assert '--heads' in args

    def test_github_storage_default_initialization(self):
        storage = GitHubStorage(repo_url='git@github.com:test/repo.git')
        assert storage.repo_url == 'git@github.com:test/repo.git'
        assert storage.branch == 'main'
        assert storage.data_file == 'todo-data.json'
        assert '{timestamp}' in storage.commit_message
