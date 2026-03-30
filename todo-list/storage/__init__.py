from .base import StorageBackend
from .local import LocalStorage
from .github import GitHubStorage


def get_storage(storage_type: str, **kwargs) -> StorageBackend:
    """Factory function to get a storage backend by type."""
    if storage_type == 'local':
        return LocalStorage(kwargs.get('path', './todo-data.json'))
    elif storage_type == 'github':
        from .github import GitHubStorage
        return GitHubStorage(
            repo_url=kwargs.get('repo_url', ''),
            branch=kwargs.get('branch', 'main'),
            data_file=kwargs.get('data_file', 'todo-data.json'),
            commit_message=kwargs.get('commit_message', 'Update todos {timestamp}'),
            clone_dir=kwargs.get('clone_dir')
        )
    elif storage_type == 'supabase':
        from .supabase import SupabaseStorage
        return SupabaseStorage(
            url=kwargs.get('url', ''),
            secret_key=kwargs.get('secret_key', ''),
            publishable_key=kwargs.get('publishable_key', ''),
            todos_table=kwargs.get('todos_table', 'todos'),
            categories_table=kwargs.get('categories_table', 'categories')
        )
    else:
        raise ValueError(f'Unknown storage type: {storage_type}')


__all__ = ['StorageBackend', 'LocalStorage', 'GitHubStorage', 'SupabaseStorage', 'get_storage']
