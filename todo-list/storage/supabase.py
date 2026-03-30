#!/usr/bin/env python3

from typing import Dict, Any, Optional, List
from .base import StorageBackend


class SupabaseStorage(StorageBackend):
    """Supabase-based storage backend."""

    def __init__(
        self,
        url: str,
        anon_key: str,
        todos_table: str = 'todos',
        categories_table: str = 'categories'
    ):
        self.url = url
        self.anon_key = anon_key
        self.todos_table = todos_table
        self.categories_table = categories_table
        self._client = None

    def _get_client(self):
        if self._client is None:
            from supabase import create_client
            self._client = create_client(self.url, self.anon_key)
        return self._client

    def load(self) -> Dict[str, Any]:
        try:
            client = self._get_client()

            todos_response = client.table(self.todos_table).select('*').execute()
            categories_response = client.table(self.categories_table).select('*').execute()

            todos = todos_response.data if todos_response.data else []
            categories = categories_response.data if categories_response.data else []

            if not categories:
                categories = [{'name': 'no category'}]
            else:
                categories = [{'name': c.get('name', c.get('id'))} for c in categories]

            return {
                'todos': todos,
                'categories': categories
            }

        except Exception as e:
            print(f'Error loading from Supabase: {e}')
            return {'todos': [], 'categories': [{'name': 'no category'}]}

    def save(self, data: Dict[str, Any]) -> None:
        try:
            client = self._get_client()

            todos = data.get('todos', [])
            categories = data.get('categories', [])

            client.table(self.todos_table).delete().neq('id', 0).execute()

            if todos:
                client.table(self.todos_table).insert(todos).execute()

            existing_categories = client.table(self.categories_table).select('name').execute()
            existing_names = {c.get('name') for c in (existing_categories.data or [])}

            new_categories = [c for c in categories if isinstance(c, dict) and c.get('name') not in existing_names]

            if new_categories:
                client.table(self.categories_table).insert(new_categories).execute()

        except Exception as e:
            print(f'Error saving to Supabase: {e}')
            raise

    def exists(self) -> bool:
        try:
            client = self._get_client()
            client.table(self.todos_table).select('id').limit(1).execute()
            return True
        except Exception:
            return False


class SupabaseMigration:
    """Migration utility for Supabase schema setup."""

    def __init__(
        self,
        url: str,
        service_role_key: str,
        todos_table: str = 'todos',
        categories_table: str = 'categories'
    ):
        self.url = url
        self.service_role_key = service_role_key
        self.todos_table = todos_table
        self.categories_table = categories_table
        self._client = None

    def _get_admin_client(self):
        if self._client is None:
            from supabase import create_client
            self._client = create_client(self.url, self.service_role_key)
        return self._client

    def create_tables(self) -> None:
        client = self._get_admin_client()

        client.table(self.categories_table).create({
            'name': 'text',
            'id': 'integer',
            'created_at': 'timestamp'
        }).execute()

        client.table(self.todos_table).create({
            'id': 'integer',
            'text': 'text',
            'completed': 'boolean',
            'priority': 'text',
            'dueDate': 'text',
            'category': 'text',
            'createdAt': 'text'
        }).execute()

    def drop_tables(self) -> None:
        client = self._get_admin_client()
        try:
            client.table(self.todos_table).delete().neq('id', 0).execute()
        except Exception:
            pass
        try:
            client.table(self.categories_table).delete().neq('id', 0).execute()
        except Exception:
            pass

    def import_from_json(self, json_path: str) -> None:
        import json
        from pathlib import Path

        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f'JSON file not found: {json_path}')

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        todos = data.get('todos', [])
        categories = data.get('categories', [])

        client = self._get_admin_client()

        for todo in todos:
            todo_copy = {k: v for k, v in todo.items() if k != 'id'}
            client.table(self.todos_table).insert(todo_copy).execute()

        for cat in categories:
            if isinstance(cat, str):
                cat = {'name': cat}
            client.table(self.categories_table).insert(cat).execute()
