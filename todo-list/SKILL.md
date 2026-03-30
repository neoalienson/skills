---
name: todo
description: A skill for managing personal todo lists with add, remove, complete, and view functionality.
user-invocable: true
---

# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Features

- Add, update, complete, and remove todo items
- Priority levels (high, medium, low, backlog)
- Categories and assignees
- Due dates
- Multiple storage backends (local, GitHub, Supabase)

## Important

The agent must not access the storage directly. The storage must update through the `todo.py` cli

## Usage

`python todo.py <command>`

### Commands

- `todo add [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <text>` - Add item
- `todo list [--filter all|pending|completed] [--list default|backlog|all] [--category NAME] [--assignee NAME] [--json|--text]` - List items
- `todo update <id> [--text TEXT] [--priority PRIORITY] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]` - Update item
- `todo complete <id>` - Mark item complete
- `todo remove <id>` - Remove item
- `todo stats` - Show statistics
- `todo categories` - List categories
- `todo add-category <name>` / `todo remove-category <name>` - Manage categories

### List Defaults

By default, `list` shows **pending items only** in **JSON format**, excluding items with `priority: "backlog"`.

```bash
todo list                    # Pending items (excludes backlog)
todo list --all             # All items (includes backlog)
todo list --list backlog     # Only backlog items
todo list --completed        # Completed items
todo list --assignee NAME    # Filter by assignee
todo list --category NAME    # Filter by category
todo list --text             # Human-readable format
```

## Backlog

Items with `priority: "backlog"` are hidden from the default view. Use `todo list --all` to see them.
