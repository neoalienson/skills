from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Any
from datetime import datetime


class TodoItem(BaseModel):
    model_config = ConfigDict(extra='allow')

    id: int
    text: str = Field(..., min_length=1)
    completed: bool = False
    createdAt: Optional[str] = None
    priority: Literal['high', 'medium', 'low', 'backlog'] = 'medium'
    dueDate: Optional[str] = None
    category: str = 'no category'
    assignee: Optional[str] = None
    completedAt: Optional[str] = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        if 'assignee' not in data:
            data['assignee'] = None
        if 'completedAt' not in data:
            data['completedAt'] = None
        return cls(**data)


class TodoListData(BaseModel):
    model_config = ConfigDict(extra='allow')

    todos: list[dict] = []
    categories: list[str] = ['no category']
