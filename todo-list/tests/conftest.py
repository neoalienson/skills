import pytest
from copy import deepcopy
from typing import Dict, Any


class MockStorage:
    """In-memory mock for StorageBackend - NO filesystem I/O."""

    def __init__(self, initial_data: Dict[str, Any] = None):
        self._data = initial_data or {'todos': [], 'categories': ['no category']}
        self._exists = True
        self.load_called = False
        self.save_called = False
        self.last_saved_data = None

    def load(self) -> Dict[str, Any]:
        self.load_called = True
        data = deepcopy(self._data)
        
        if data is None:
            return {'todos': [], 'categories': ['no category']}

        if isinstance(data, list):
            return {'todos': data, 'categories': ['no category']}

        return {
            'todos': data.get('todos', []),
            'categories': data.get('categories', ['no category'])
        }

    def save(self, data: Dict[str, Any]) -> None:
        self.save_called = True
        self.last_saved_data = deepcopy(data)
        self._data = deepcopy(data)

    def exists(self) -> bool:
        return self._exists

    def set_exists(self, exists: bool):
        self._exists = exists

    def set_data(self, data: Dict[str, Any]):
        self._data = deepcopy(data)


@pytest.fixture
def mock_storage():
    """Fixture providing fresh MockStorage for each test."""
    return MockStorage()


@pytest.fixture
def storage_with_todos():
    """Fixture providing MockStorage pre-loaded with sample todos."""
    return MockStorage({
        'todos': [
            {
                'id': 1,
                'text': 'Test task 1',
                'completed': False,
                'createdAt': '2024-01-01T00:00:00',
                'priority': 'medium',
                'dueDate': None,
                'category': 'no category'
            },
            {
                'id': 2,
                'text': 'Test task 2',
                'completed': True,
                'createdAt': '2024-01-01T00:00:00',
                'priority': 'high',
                'dueDate': None,
                'category': 'work'
            }
        ],
        'categories': ['no category', 'work']
    })
