#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class StorageBackend(ABC):
    """Abstract base class for todo storage backends."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Load todo data from the storage.

        Returns:
            Dict with 'todos' and 'categories' keys.
            Example: {'todos': [...], 'categories': [...]}
        """
        pass

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """
        Save todo data to the storage.

        Note: For Supabase, use add/update/delete methods instead of bulk save
        to properly handle auto-increment IDs.

        Args:
            data: Dict with 'todos' and 'categories' keys.
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if the storage exists and is accessible.

        Returns:
            True if storage exists, False otherwise.
        """
        pass

    def add(self, todo: Dict[str, Any]) -> int:
        """
        Add a single todo. Override in subclasses that support individual operations.
        
        Returns:
            The ID of the inserted todo.
        """
        raise NotImplementedError("add() not supported for this storage type")

    def update(self, todo: Dict[str, Any]) -> None:
        """
        Update a single todo. Override in subclasses that support individual operations.
        """
        raise NotImplementedError("update() not supported for this storage type")

    def delete(self, todo_id: int) -> None:
        """
        Delete a single todo by ID. Override in subclasses that support individual operations.
        """
        raise NotImplementedError("delete() not supported for this storage type")
