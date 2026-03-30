# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Features

- Add, update, complete, and remove todo items
- Priority levels (high, medium, low, backlog)
- Categories and assignees
- Due dates
- Multiple storage backends (local, GitHub, Supabase)

## Setup

1. Copy `config.yml.sample` to `config.yml`
2. Configure your preferred storage backend
3. Run `python todo.py <command>`

## Configuration

### Local Storage (Default)

```yaml
storage:
  type: local
local:
  path: ./todo-data.json
```

### GitHub Storage

```yaml
storage:
  type: github
github:
  repo_url: git@github.com:user/repo.git
  branch: gh-pages
  data_file: todo-data.json
```

### Supabase Storage

```yaml
storage:
  type: supabase
supabase:
  url: https://your-project.supabase.co
  publishable_key: your-key
  secret_key: your-secret-key
```

## Backlog

Items with `priority: "backlog"` are hidden from the default view:

```bash
todo add "Later task" --priority backlog    # Add to backlog
todo list                                    # Excludes backlog
todo list --all                             # Includes backlog
todo list --list backlog                    # Only backlog
```

## Data Format

```json
{
  "todos": [
    {
      "id": 1234567890,
      "text": "Task text",
      "completed": false,
      "priority": "medium",
      "dueDate": null,
      "category": "no category",
      "assignee": null
    }
  ],
  "categories": ["no category", "work"]
}
```
