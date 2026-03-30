#!/usr/bin/env python3

from typing import Dict, Any, Optional, List
from .base import StorageBackend


# Field mapping: Python camelCase → Supabase snake_case
TODO_TO_DB = {
    'id': 'id',
    'text': 'text',
    'completed': 'completed',
    'priority': 'priority',
    'dueDate': 'due_date',
    'category': 'category',
    'assignee': 'assignee',
    'createdAt': 'created_at',
    'completedAt': 'completed_at',
}

DB_TO_TODO = {v: k for k, v in TODO_TO_DB.items()}


def _map_todo_to_db(todo: dict) -> dict:
    """Convert Python todo dict to Supabase column names."""
    return {TODO_TO_DB.get(k, k): v for k, v in todo.items()}


def _map_todo_from_db(todo: dict) -> dict:
    """Convert Supabase column names to Python todo dict."""
    return {DB_TO_TODO.get(k, k): v for k, v in todo.items()}


class SupabaseStorage(StorageBackend):
    """Supabase-based storage backend."""

    def __init__(
        self,
        url: str,
        secret_key: str,
        todos_table: str = 'todos',
        categories_table: str = 'categories',
        publishable_key: str = ''
    ):
        self.url = url
        self.secret_key = secret_key
        self.publishable_key = publishable_key
        self.todos_table = todos_table
        self.categories_table = categories_table
        self._client = None

    def _get_client(self):
        if self._client is None:
            from supabase import create_client
            self._client = create_client(self.url, self.secret_key)
        return self._client

    def load(self) -> Dict[str, Any]:
        try:
            client = self._get_client()

            todos_response = client.table(self.todos_table).select('*').execute()
            categories_response = client.table(self.categories_table).select('*').execute()

            todos = todos_response.data if todos_response.data else []
            categories = categories_response.data if categories_response.data else []

            # Map database fields to Python fields
            todos = [_map_todo_from_db(t) for t in todos]

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
        """
        Save todo data using upsert (for backward compatibility).
        
        Note: For better performance with auto-increment IDs, use add()/update()/delete()
        methods instead of bulk save.
        """
        try:
            client = self._get_client()

            todos = data.get('todos', [])
            categories = data.get('categories', [])

            # Map Python fields to database fields
            todos_db = [_map_todo_to_db(t) for t in todos]

            # Use upsert instead of delete-all + insert-all
            for todo in todos_db:
                client.table(self.todos_table).upsert(
                    todo,
                    on_conflict='id'
                ).execute()

            existing_categories = client.table(self.categories_table).select('name').execute()
            existing_names = {c.get('name') for c in (existing_categories.data or [])}

            new_categories = [c for c in categories if isinstance(c, dict) and c.get('name') not in existing_names]

            if new_categories:
                client.table(self.categories_table).insert(new_categories).execute()

        except Exception as e:
            print(f'Error saving to Supabase: {e}')
            raise

    def add(self, todo: Dict[str, Any]) -> int:
        """Add a single todo and return the generated ID."""
        client = self._get_client()
        todo_db = _map_todo_to_db(todo)
        
        todo_db = {k: v for k, v in todo_db.items() if k != 'id'}
        
        response = client.table(self.todos_table).insert(todo_db).execute()
        
        if response.data:
            return response.data[0]['id']
        raise ValueError("Failed to insert todo")

    def update(self, todo: Dict[str, Any]) -> None:
        """Update a single todo by ID."""
        client = self._get_client()
        todo_db = _map_todo_to_db(todo)
        todo_id = todo_db.pop('id', None)
        
        if todo_id is None:
            raise ValueError("Todo ID is required for update")
        
        client.table(self.todos_table).update(todo_db).eq('id', todo_id).execute()

    def delete(self, todo_id: int) -> None:
        """Delete a single todo by ID."""
        client = self._get_client()
        client.table(self.todos_table).delete().eq('id', todo_id).execute()

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
        """Create tables using raw SQL via RPC since client.create() is deprecated."""
        client = self._get_admin_client()
        
        # Use RPC to execute raw SQL for creating tables
        # First, try to create categories table
        try:
            client.rpc('exec', {
                'query': '''
                    CREATE TABLE IF NOT EXISTS categories (
                        id: integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                        name: text NOT NULL,
                        created_at: timestamp DEFAULT NOW()
                    );
                '''
            }).execute()
        except Exception:
            # RPC exec function may not exist, fall back to table API
            pass
        
        # Create todos table with proper schema
        try:
            client.rpc('exec', {
                'query': '''
                    CREATE TABLE IF NOT EXISTS todos (
                        id: integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                        text: text NOT NULL,
                        completed: boolean DEFAULT false,
                        priority: text DEFAULT 'medium',
                        due_date: timestamp,
                        category: text DEFAULT 'no category',
                        assignee: text,
                        created_at: timestamp DEFAULT NOW(),
                        completed_at: timestamp
                    );
                '''
            }).execute()
        except Exception:
            pass

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
            todo_db = _map_todo_to_db(todo)
            todo_copy = {k: v for k, v in todo_db.items() if k != 'id'}
            client.table(self.todos_table).insert(todo_copy).execute()

        for cat in categories:
            if isinstance(cat, str):
                cat = {'name': cat}
            client.table(self.categories_table).insert(cat).execute()
