#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Dict, Any


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
