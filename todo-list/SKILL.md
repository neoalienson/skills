---
name: todo
description: A skill for managing personal todo lists with add, remove, complete, and view functionality.
user-invocable: true
---

# Todo List Manager

A skill for managing personal todo lists with add, remove, complete, and view functionality.

## Description

This skill allows users to manage their personal todo lists with the following features:
- Add new todo items with optional priority and due date
- Mark items as completed
- Remove items from the list
- View all pending items
- View completed items
- Clear completed items
- Track overdue items

## Usage

When the user wants to manage their todo list, execute the appropriate command using the exec tool:

- Use `exec command="node {baseDir}/todo.mjs add [--high|--low] [--due YYYY-MM-DD] <item text>"` to add a new item to the todo list
- Use `exec command="node {baseDir}/todo.mjs list [all|pending|completed]"` to show all pending items
- Use `exec command="node {baseDir}/todo.mjs complete <id>"` to mark an item as completed
- Use `exec command="node {baseDir}/todo.mjs remove <id>"` to remove an item completely
- Use `exec command="node {baseDir}/todo.mjs clear-completed"` to remove all completed items
- Use `exec command="node {baseDir}/todo.mjs stats"` to show statistics about the todo list
- Use `exec command="node {baseDir}/todo.mjs remind <id> <minutes>"` to schedule a reminder for a todo item

## Integration with Cron for Reminders

To schedule reminders that send WhatsApp messages via agent turns:

1. When user requests a reminder for a specific todo item:
   - First, retrieve the todo details: `exec command="node {baseDir}/todo.mjs list"`
   - Then schedule the cron job with an isolated session for direct message delivery:
   
```
exec command="clawdbot cron add --name \\\"todo-reminder-[id]\\\" --cron \\\"MM HH DD MM *\\\" --session isolated --message \\\"⏰ Reminder: Please complete your task - [task_text]\\\" --channel whatsapp --to \\\"+85265432195\\\" --deliver --delete-after-run"
```

Replace MM HH DD MM with the calculated time values, [id] with a unique identifier, and [task_text] with the actual task text.

## Examples

When the user says "Add a new todo: buy groceries due tomorrow":
- Parse the request and execute: `exec command="node {baseDir}/todo.mjs add --due $(date -d tomorrow +%Y-%m-%d) buy groceries"`

When the user says "Show my todos":
- Execute: `exec command="node {baseDir}/todo.mjs list"`

When the user says "Mark todo #1 as complete":
- Execute: `exec command="node {baseDir}/todo.mjs complete 1"`

When the user says "Schedule a reminder for todo #1 in 10 minutes":
- First, get the todo: `exec command="node {baseDir}/todo.mjs list"`
- Then schedule the reminder with calculated time values using:
`exec command="clawdbot cron add --name \\\"todo-reminder-1\\\" --cron \\\"MM HH DD MM *\\\" --session isolated --message \\\"⏰ Reminder: Please complete your task\\\" --channel whatsapp --to \\\"+85265432195\\\" --deliver --delete-after-run"`

## Implementation

Todos are stored in a structured format in the user's workspace, allowing persistence between sessions. The skill provides an easy-to-use interface for common todo management tasks.

## Examples

When the user says "Add a new todo: buy groceries due tomorrow":
- Parse the request and execute: `exec command="node {baseDir}/todo.mjs add --due $(date -d tomorrow +%Y-%m-%d) buy groceries"`

When the user says "Show my todos":
- Execute: `exec command="node {baseDir}/todo.mjs list"`

When the user says "Mark todo #1 as complete":
- Execute: `exec command="node {baseDir}/todo.mjs complete 1"`

When the user says "Show overdue items":
- Execute: `exec command="node {baseDir}/todo.mjs stats"` to see overdue count, then `exec command="node {baseDir}/todo.mjs list pending"` to see pending items which may include overdue ones