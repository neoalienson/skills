---
name: todo
description: A skill for managing personal todo lists with add, remove, complete, and view functionality.
user-invocable: true
---

# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Description

This skill allows users to manage their personal todo lists with the following features:
- Add new todo items with optional priority, due date, category, and assignee
- Update existing todo items (text, priority, due date, category, assignee, completion)
- Mark items as completed
- Remove items from the list
- View pending items (default)
- View completed items
- View all items
- Clear completed items
- Track overdue items
- Organize todos by categories
- Assign todos to assignees
- Schedule reminders for todos

## Usage

When the user wants to manage their todo list, execute the appropriate command using the exec tool:

- Use `exec command="python {baseDir}/todo.py add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>"` to add a new item to the todo list
- Use `exec command="python {baseDir}/todo.py list [--filter all|pending|completed] [--assignee NAME] [--fields FIELD1,FIELD2] [--json|--text]"` to show pending items (default: JSON output)
- Use `exec command="python {baseDir}/todo.py update <id> [--text \"text\"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]"` to update a todo item
- Use `exec command="python {baseDir}/todo.py complete <id>"` to mark an item as completed
- Use `exec command="python {baseDir}/todo.py remove <id>"` to remove an item completely
- Use `exec command="python {baseDir}/todo.py clear-completed"` to remove all completed items
- Use `exec command="python {baseDir}/todo.py stats"` to show statistics about the todo list
- Use `exec command="python {baseDir}/todo.py categories"` to list all categories
- Use `exec command="python {baseDir}/todo.py add-category <name>"` to add a new category
- Use `exec command="python {baseDir}/todo.py remove-category <name>"` to remove a category
- Use `exec command="python {baseDir}/todo.py set-category <id> <category>"` to assign a todo to a category (deprecated, use update)
- Use `exec command="python {baseDir}/todo.py remind <id> <minutes>"` to schedule a reminder for a todo item

## List Command Defaults

By default, `list` shows **pending items only** in **JSON format**. Use flags to change:

```bash
todo list                    # Show pending items in JSON (default)
todo list --all              # Show all items in JSON
todo list --completed        # Show completed items only in JSON
todo list --assignee work   # Filter by assignee
todo list --fields text,priority,dueDate  # Show only specific fields
todo list --text             # Output in human-readable text format
```

Available fields: `id`, `text`, `priority`, `dueDate`, `category`, `assignee`, `completed`

## Integration with Cron for Reminders

To schedule reminders that send WhatsApp messages via agent turns:

1. When user requests a reminder for a specific todo item:
   - First, retrieve the todo details: `exec command="python {baseDir}/todo.py list"`
   - Then schedule the cron job with an isolated session for direct message delivery:

```
exec command="clawdbot cron add --name \"todo-reminder-[id]\" --cron \"MM HH DD MM *\" --session isolated --message \"Reminder: Please complete your task - [task_text]\" --channel whatsapp --to \"+85265432195\" --deliver --delete-after-run"
```

Replace MM HH DD MM with the calculated time values, [id] with a unique identifier, and [task_text] with the actual task text.

## Examples

When the user says "Add a new todo: buy groceries due tomorrow":
- Parse the request and execute: `exec command="python {baseDir}/todo.py add --due $(date -d tomorrow +%Y-%m-%d) buy groceries"`

When the user says "Show my todos":
- Execute: `exec command="python {baseDir}/todo.py list"`

When the user says "Show all my todos":
- Execute: `exec command="python {baseDir}/todo.py list --all"`

When the user says "Mark todo #1 as complete":
- Execute: `exec command="python {baseDir}/todo.py complete 1"`

When the user says "Update todo #1 to high priority and assign to Neo":
- Execute: `exec command="python {baseDir}/todo.py update 1 --priority high --assignee Neo"`

When the user says "Update todo #1's due date to next Friday":
- First calculate the date, then execute: `exec command="python {baseDir}/todo.py update 1 --due $(date -d 'next friday' +%Y-%m-%d)"`

When the user says "Schedule a reminder for todo #1 in 10 minutes":
- First, get the todo: `exec command="python {baseDir}/todo.py list"`
- Then schedule the reminder with calculated time values using:
`exec command="clawdbot cron add --name \"todo-reminder-1\" --cron \"MM HH DD MM *\" --session isolated --message \"Reminder: Please complete your task\" --channel whatsapp --to \"+85265432195\" --deliver --delete-after-run"`
