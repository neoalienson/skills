#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Dict, Any

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, path: str = './todo-data.json'):
        self.path = Path(path)

    def load(self) -> Dict[str, Any]:
        """Load todo data from local JSON file."""
        if not self.exists():
            return {'todos': [], 'categories': ['no category']}

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
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
            print(f'Error loading todos from {self.path}: {e}')
            return {'todos': [], 'categories': ['no category']}

    def save(self, data: Dict[str, Any]) -> None:
        """Save todo data to local JSON file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'Error saving todos to {self.path}: {e}')
            raise

    def exists(self) -> bool:
        """Check if local file exists."""
        return self.path.exists()

    def add(self, todo: Dict[str, Any]) -> int:
        """Add is not supported for local storage - use save() instead."""
        raise NotImplementedError("add() not supported for local storage - use save() instead")

    def update(self, todo: Dict[str, Any]) -> None:
        """Update is not supported for local storage - use save() instead."""
        raise NotImplementedError("update() not supported for local storage - use save() instead")

    def delete(self, todo_id: int) -> None:
        """Delete is not supported for local storage - use save() instead."""
        raise NotImplementedError("delete() not supported for local storage - use save() instead")
