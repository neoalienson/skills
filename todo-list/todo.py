#!/usr/bin/env python3

import json
import os
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import config
import storage
from models import TodoItem


class TodoManager:
    def __init__(self, workspace_dir='/home/neo/clawd', storage_backend=None):
        self.workspace_dir = workspace_dir

        if storage_backend is not None:
            self._storage = storage_backend
        else:
            cfg = config.Config()
            cfg.validate()
            self._storage = self._create_storage_from_config(cfg)

        self.todos = []
        self.categories = ['no category']
        self.load_todos()

    def _create_storage_from_config(self, cfg):
        """Create a storage backend from config."""
        if cfg.storage.type == 'local':
            return storage.get_storage(
                'local',
                path=cfg.storage.local.path
            )
        elif cfg.storage.type == 'github':
            return storage.get_storage(
                'github',
                repo_url=cfg.storage.github.repo_url,
                branch=cfg.storage.github.branch,
                data_file=cfg.storage.github.data_file,
                commit_message=cfg.storage.github.commit_message,
                clone_dir=cfg.storage.github.clone_dir
            )
        elif cfg.storage.type == 'supabase':
            return storage.get_storage(
                'supabase',
                url=cfg.storage.supabase.url,
                anon_key=cfg.storage.supabase.anon_key,
                todos_table=cfg.storage.supabase.todos_table,
                categories_table=cfg.storage.supabase.categories_table
            )
        else:
            raise ValueError(f'Unknown storage type: {cfg.storage.type}')

    def load_todos(self):
        try:
            data = self._storage.load()
            todo_data = data.get('todos', [])
            self.todos = [TodoItem.from_dict(t) for t in todo_data]
            self.categories = data.get('categories', ['no category'])
        except Exception as e:
            print(f'Error loading todos: {e}')
            self.todos = []
            self.categories = ['no category']

    def save_todos(self):
        try:
            data_to_save = {
                'todos': [t.model_dump() for t in self.todos],
                'categories': self.categories
            }
            self._storage.save(data_to_save)
        except Exception as e:
            print(f'Error saving todos: {e}')
            raise

    def add_category(self, category_name):
        if category_name is None or (isinstance(category_name, str) and not category_name.strip()):
            raise ValueError('Category name cannot be empty')

        normalized_category = category_name.strip()

        for cat in self.categories:
            if cat.lower() == normalized_category.lower():
                return False

        self.categories.append(normalized_category)
        self.save_todos()
        return True

    def remove_category(self, category_name):
        if category_name is None or (isinstance(category_name, str) and not category_name.strip()):
            raise ValueError('Category name cannot be empty')

        if len(self.categories) == 1 and self.categories[0].lower() == category_name.strip().lower():
            raise ValueError('Cannot remove the last remaining category')

        normalized_category = category_name.strip()
        initial_length = len(self.categories)

        self.categories = [cat for cat in self.categories
                          if cat.lower() != normalized_category.lower()]

        if initial_length != len(self.categories):
            for todo in self.todos:
                if todo.category.lower() == normalized_category.lower():
                    todo.category = 'no category'
            self.save_todos()
            return True

        return False

    def list_categories(self):
        return list(self.categories)

    def add_todo(self, item, priority='medium', due_date=None, category='no category', assignee=None):
        if item is None or (isinstance(item, str) and not item.strip()):
            raise ValueError('Todo text cannot be empty')

        valid_priorities = ['high', 'medium', 'low']
        if priority not in valid_priorities:
            raise ValueError(f'Invalid priority "{priority}". Must be one of: {", ".join(valid_priorities)}')

        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f'Invalid due date format "{due_date}". Use YYYY-MM-DD')

        if category and category not in self.categories:
            self.add_category(category)

        new_todo = TodoItem(
            id=int(time.time() * 1000000),
            text=item,
            completed=False,
            createdAt=datetime.now().isoformat(),
            priority=priority,
            dueDate=due_date,
            category=category,
            assignee=assignee
        )

        self.todos.append(new_todo)
        self.save_todos()
        return new_todo

    def list_todos(self, filter_type='all', category=None, assignee=None):
        filtered_todos = list(self.todos)

        if category:
            category_lower = category.lower()
            if category_lower == 'no category':
                filtered_todos = [
                    todo for todo in filtered_todos
                    if not todo.category or todo.category.lower() == 'no category'
                ]
            else:
                filtered_todos = [
                    todo for todo in filtered_todos
                    if todo.category.lower() == category_lower
                ]

        if assignee:
            assignee_lower = assignee.lower()
            filtered_todos = [
                todo for todo in filtered_todos
                if todo.assignee and todo.assignee.lower() == assignee_lower
            ]

        if filter_type == 'pending':
            filtered_todos = [todo for todo in filtered_todos if not todo.completed]
        elif filter_type == 'completed':
            filtered_todos = [todo for todo in filtered_todos if todo.completed]

        return filtered_todos

    def mark_complete(self, todo_id):
        for todo in self.todos:
            if todo.id == todo_id:
                todo.completed = True
                todo.completedAt = datetime.now().isoformat()
                self.save_todos()
                self.remove_associated_cron_job(todo_id)
                return todo
        return None

    def remove_associated_cron_job(self, todo_id):
        try:
            result = subprocess.run(
                ['clawdbot', 'cron', 'list', '--json'],
                capture_output=True, text=True, encoding='utf-8'
            )
            cron_data = json.loads(result.stdout)

            if isinstance(cron_data.get('jobs'), list):
                for job in cron_data['jobs']:
                    if job.get('name') and str(todo_id) in job.get('name', ''):
                        job_id = job.get('id')
                        try:
                            subprocess.run(['clawdbot', 'cron', 'rm', str(job_id)], capture_output=True)
                            print(f'Removed associated cron job {job_id} for todo {todo_id}')
                        except Exception as err:
                            print(f'Failed to remove cron job {job_id}: {err}')
        except Exception as error:
            print(f'Error checking for associated cron jobs: {error}')

    def remove_todo(self, todo_id):
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                removed = self.todos.pop(i)
                self.save_todos()
                return removed
        return None

    def clear_completed(self):
        self.todos = [todo for todo in self.todos if not todo.completed]
        self.save_todos()
        return len(self.todos)

    def get_stats(self):
        total = len(self.todos)
        completed = len([t for t in self.todos if t.completed])
        pending = total - completed

        now = datetime.now()
        overdue = len([
            t for t in self.todos
            if not t.completed and t.dueDate and datetime.fromisoformat(t.dueDate) < now
        ])

        priorities = {}
        for todo in self.todos:
            priority = todo.priority
            priorities[priority] = priorities.get(priority, 0) + 1

        categories = {}
        for todo in self.todos:
            cat = todo.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'overdue': overdue,
            'priorities': priorities,
            'categories': categories
        }

    def update_todo_category(self, todo_id, new_category):
        if not new_category:
            raise ValueError('Category cannot be empty')
        return self.update_todo(todo_id, category=new_category)

    def update_todo(self, todo_id, **kwargs) -> TodoItem | None:
        for todo in self.todos:
            if todo.id == todo_id:
                if 'text' in kwargs:
                    text = kwargs['text']
                    if not text or (isinstance(text, str) and not text.strip()):
                        raise ValueError('Todo text cannot be empty')
                    todo.text = text

                if 'priority' in kwargs:
                    priority = kwargs['priority']
                    if priority not in ('high', 'medium', 'low'):
                        raise ValueError(f'Invalid priority "{priority}". Must be one of: high, medium, low')
                    todo.priority = priority

                if 'due_date' in kwargs:
                    due_date = kwargs['due_date']
                    if due_date:
                        try:
                            datetime.strptime(due_date, '%Y-%m-%d')
                        except ValueError:
                            raise ValueError(f'Invalid due date format "{due_date}". Use YYYY-MM-DD')
                    todo.dueDate = due_date

                if 'category' in kwargs:
                    category = kwargs['category']
                    if category and category not in self.categories:
                        self.add_category(category)
                    todo.category = category if category else 'no category'

                if 'assignee' in kwargs:
                    todo.assignee = kwargs['assignee']

                if 'completed' in kwargs:
                    todo.completed = kwargs['completed']
                    if todo.completed:
                        todo.completedAt = datetime.now().isoformat()
                    else:
                        todo.completedAt = None

                self.save_todos()
                return todo
        return None


def schedule_reminder(todo_id, todo_text, delay_minutes, todo_manager):
    try:
        message = f"Reminder: Please complete your task - {todo_text}"
        reminder_command = f'message --action send --target "+85265432195" --message "{message}"'

        print(f'To schedule a reminder for this task, please run the following command separately:')
        print(f'clawdbot cron --action add --job \'{{"schedule": "*/{delay_minutes} * * * *", "command": "{reminder_command}", "description": "Reminder for todo {todo_id}: {todo_text}", "channel": "whatsapp"}}\'')
        print(f'Or for a one-time reminder in {delay_minutes} minutes, calculate the exact time and schedule accordingly.')
    except Exception as error:
        print(f'Error scheduling reminder: {error}')


def main():
    import sys

    if len(sys.argv) < 2:
        print('''Todo List Manager

Usage:
  todo add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>
  todo list [--filter all|pending|completed] [--assignee NAME]
  todo update <id> [--text "text"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]
  todo complete <id>
  todo remove <id>
  todo clear-completed
  todo stats
  todo categories
  todo add-category <name>
  todo remove-category <name>
  todo set-category <id> <category>  (deprecated, use update)
  todo remind <id> <minutes>''')
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    try:
        todo_manager = TodoManager()
    except ValueError as e:
        print(f'Configuration error: {e}')
        print('Please create a config.yml file based on config.yml.sample')
        sys.exit(1)

    if command == 'add':
        if args and args[0] in ('-h', '--help'):
            print('''Usage:
  todo add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>

Options:
  --priority high|medium|low    Set priority (default: medium)
  --due YYYY-MM-DD              Set due date
  --category NAME               Set category
  --assignee NAME              Set assignee (can be empty string)
  --high                        Shortcut for --priority high
  --low                         Shortcut for --priority low
  -h, --help                    Show this help message

Examples:
  todo add "Buy groceries"
  todo add "Finish report" --priority high
  todo add "Submit form" --due 2024-12-31 --category work
  todo add "Call mom" --assignee Neo''')
            sys.exit(0)

        priority = 'medium'
        due_date = None
        category = 'no category'
        assignee = None
        item_text = None

        i = 0
        while i < len(args):
            if args[i] == '--priority' and i + 1 < len(args):
                priority = args[i + 1]
                i += 2
            elif args[i] == '--due' and i + 1 < len(args):
                due_date = args[i + 1]
                i += 2
            elif args[i] == '--category' and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            elif args[i] == '--assignee' and i + 1 < len(args):
                assignee = args[i + 1]
                i += 2
            elif args[i] == '-a' and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            elif args[i] == '--high':
                priority = 'high'
                i += 1
            elif args[i] == '--low':
                priority = 'low'
                i += 1
            else:
                item_text = ' '.join(args[i:])
                break

        if not item_text:
            print('Error: Item text is required')
            print('Usage: todo add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>')
            print('For help: todo add -h')
            sys.exit(1)

        try:
            new_todo = todo_manager.add_todo(item_text, priority, due_date, category, assignee)
            due_info = f', Due: {new_todo.dueDate}' if new_todo.dueDate else ''
            assignee_info = f', Assignee: {new_todo.assignee}' if new_todo.assignee else ''
            print(f'Added: {new_todo.text} (ID: {new_todo.id}, Category: {new_todo.category}){due_info}{assignee_info}')
        except ValueError as e:
            print(f'Error: {e}')
            sys.exit(1)

    elif command in ('list', 'show'):
        if args and args[0] in ('-h', '--help'):
            print('''Usage:
  todo list [--filter all|pending|completed] [--category NAME] [--assignee NAME] [--fields FIELD1,FIELD2,...] [--json|--text]

Options:
  --filter all|pending|completed    Filter by status (default: pending)
  --category NAME                   Filter by category (case insensitive)
  --assignee NAME                   Filter by assignee (case insensitive)
  --pending                         Show pending todos only (default)
  --completed                       Show completed todos only
  --all                             Show all todos
  --fields FIELD1,FIELD2,...        Fields to display (for --text and --json)
                                      Available: id, text, priority, dueDate, category, assignee, completed
  --json                            Output in JSON format (default)
  --text                            Output in human-readable text format
  -h, --help                        Show this help message''')
            sys.exit(0)

        filter_type = 'pending'
        category_filter = None
        assignee_filter = None
        fields = None
        output_format = 'json'

        i = 0
        while i < len(args):
            if args[i] == '--filter' and i + 1 < len(args):
                filter_type = args[i + 1]
                i += 2
            elif args[i] == '--category' and i + 1 < len(args):
                category_filter = args[i + 1]
                i += 2
            elif args[i] == '--assignee' and i + 1 < len(args):
                assignee_filter = args[i + 1]
                i += 2
            elif args[i] == '-a' and i + 1 < len(args):
                category_filter = args[i + 1]
                i += 2
            elif args[i] == '--pending':
                filter_type = 'pending'
                i += 1
            elif args[i] == '--completed':
                filter_type = 'completed'
                i += 1
            elif args[i] == '--all':
                filter_type = 'all'
                i += 1
            elif args[i] == '--fields' and i + 1 < len(args):
                fields = [f.strip() for f in args[i + 1].split(',')]
                i += 2
            elif args[i] == '--json':
                output_format = 'json'
                i += 1
            elif args[i] == '--text':
                output_format = 'text'
                i += 1
            else:
                i += 1

        todos = todo_manager.list_todos(filter_type, category_filter, assignee_filter)

        if not todos:
            if output_format == 'json':
                print('[]')
            else:
                filter_text = 'items' if filter_type == 'all' else filter_type
                category_text = f" for category '{category_filter}'" if category_filter else ''
                assignee_text = f" for assignee '{assignee_filter}'" if assignee_filter else ''
                print(f'No {filter_text} todos found{category_text}{assignee_text}.')
        else:
            if output_format == 'json':
                import json
                if fields:
                    output_todos = [
                        {k: v for k, v in todo.model_dump().items() if k in fields and v is not None}
                        for todo in todos
                    ]
                else:
                    output_todos = [
                        {k: v for k, v in todo.model_dump().items() if v is not None}
                        for todo in todos
                    ]
                print(json.dumps(output_todos, indent=2))
            else:
                title = f"{filter_type.capitalize() if filter_type != 'all' else 'All'} Todos"
                if category_filter:
                    title += f" for category '{category_filter}'"
                if assignee_filter:
                    title += f" for assignee '{assignee_filter}'"
                print(f'{title}:')

                for todo in todos:
                    parts = []
                    if fields is None or 'id' in fields:
                        parts.append(f'#{todo.id}')
                    if fields is None or 'completed' in fields:
                        status = '[x]' if todo.completed else '[ ]'
                        parts.append(status)
                    if fields is None or 'priority' in fields:
                        parts.append(f'[{todo.priority}]')
                    if fields is None or 'text' in fields:
                        parts.append(todo.text)
                    if fields is None or 'dueDate' in fields:
                        if todo.dueDate:
                            parts.append(f'(Due: {todo.dueDate})')
                    if fields is None or 'category' in fields:
                        if todo.category and todo.category != 'no category':
                            parts.append(f'[{todo.category}]')
                    if fields is None or 'assignee' in fields:
                        if todo.assignee:
                            parts.append(f'@{todo.assignee}')
                    print(' '.join(parts))

    elif command in ('complete', 'done'):
        if not args:
            print('Usage: todo complete <id>')
            sys.exit(1)

        completed = todo_manager.mark_complete(int(args[0]))
        if completed:
            print(f'Completed: {completed.text}')
        else:
            print(f'Todo with ID {args[0]} not found.')

    elif command in ('remove', 'delete'):
        if not args:
            print('Usage: todo remove <id>')
            sys.exit(1)

        removed = todo_manager.remove_todo(int(args[0]))
        if removed:
            print(f'Removed: {removed.text}')
        else:
            print(f'Todo with ID {args[0]} not found.')

    elif command == 'clear-completed':
        remaining_count = todo_manager.clear_completed()
        print(f'Cleared all completed todos. {remaining_count} pending todos remain.')

    elif command == 'stats':
        stats = todo_manager.get_stats()
        print('Todo Statistics:')
        print(f'Total: {stats["total"]}')
        print(f'Pending: {stats["pending"]}')
        print(f'Completed: {stats["completed"]}')
        print(f'Overdue: {stats["overdue"]}')
        print(f'By Priority: {stats["priorities"]}')
        print(f'By Category: {stats["categories"]}')

    elif command in ('categories', 'cats'):
        categories = todo_manager.list_categories()
        if not categories:
            print('No categories defined.')
        else:
            print('Categories:')
            for i, cat in enumerate(categories, 1):
                print(f'{i}. {cat}')

    elif command in ('add-category', 'new-category'):
        if not args:
            print('Usage: todo add-category <category name>')
            sys.exit(1)

        category_name = ' '.join(args)
        try:
            added = todo_manager.add_category(category_name)
            if added:
                print(f'Added category: {category_name}')
            else:
                print(f"Category '{category_name}' already exists.")
        except ValueError as e:
            print(f'Error: {e}')
            sys.exit(1)

    elif command in ('remove-category', 'del-category'):
        if not args:
            print('Usage: todo remove-category <category name>')
            sys.exit(1)

        cat_to_remove = ' '.join(args)
        try:
            removed = todo_manager.remove_category(cat_to_remove)
            if removed:
                print(f'Removed category: {cat_to_remove}')
            else:
                print(f"Category '{cat_to_remove}' not found.")
        except ValueError as e:
            print(f'Error: {e}')
            sys.exit(1)

    elif command in ('set-category', 'assign-category'):
        if len(args) < 2:
            print('Usage: todo set-category <id> <category name>')
            print('Note: This command is deprecated. Use: todo update <id> --category <name>')
            sys.exit(1)

        todo_id = int(args[0])
        new_category = ' '.join(args[1:])
        try:
            updated = todo_manager.update_todo_category(todo_id, new_category)
            if updated:
                print(f'Updated category for todo ID {todo_id} to: {new_category}')
            else:
                print(f'Todo with ID {todo_id} not found.')
        except ValueError as e:
            print(f'Error: {e}')
            sys.exit(1)

    elif command == 'update':
        if not args or args[0] in ('-h', '--help'):
            print('''Usage:
  todo update <id> [--text "text"] [--priority high|medium|low]
                   [--due YYYY-MM-DD] [--category NAME] [--assignee NAME]
                   [--completed | --pending]

Options:
  --text "text"                   Update the todo text
  --priority high|medium|low      Update priority
  --due YYYY-MM-DD              Update due date (use empty to clear)
  --category NAME               Update category
  --assignee NAME               Update assignee (use empty string to clear)
  --completed                   Mark as completed
  --pending                      Mark as pending
  -h, --help                    Show this help message

Examples:
  todo update 1 --priority high
  todo update 1 --assignee Neo --priority high
  todo update 1 --due 2024-12-31 --category work
  todo update 1 --assignee ""''')
            sys.exit(0)

        todo_id = None
        update_kwargs = {}

        i = 0
        while i < len(args):
            if args[i] == '--text' and i + 1 < len(args):
                update_kwargs['text'] = args[i + 1]
                i += 2
            elif args[i] == '--priority' and i + 1 < len(args):
                update_kwargs['priority'] = args[i + 1]
                i += 2
            elif args[i] == '--due' and i + 1 < len(args):
                due_val = args[i + 1]
                update_kwargs['due_date'] = due_val if due_val else None
                i += 2
            elif args[i] == '--category' and i + 1 < len(args):
                update_kwargs['category'] = args[i + 1]
                i += 2
            elif args[i] == '--assignee' and i + 1 < len(args):
                assignee_val = args[i + 1]
                update_kwargs['assignee'] = assignee_val if assignee_val else ''
                i += 2
            elif args[i] == '--completed':
                update_kwargs['completed'] = True
                i += 1
            elif args[i] == '--pending':
                update_kwargs['completed'] = False
                i += 1
            elif args[i].isdigit() and todo_id is None:
                todo_id = int(args[i])
                i += 1
            else:
                i += 1

        if not todo_id:
            print('Error: Todo ID is required')
            print('Usage: todo update <id> [--text "text"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME]')
            sys.exit(1)

        try:
            updated = todo_manager.update_todo(todo_id, **update_kwargs)
            if updated:
                print(f'Updated todo #{todo_id}:')
                print(f'  Text: {updated.text}')
                print(f'  Priority: {updated.priority}')
                print(f'  Category: {updated.category}')
                print(f'  Assignee: {updated.assignee if updated.assignee else "(none)"}')
                print(f'  Due: {updated.dueDate if updated.dueDate else "(none)"}')
                print(f'  Completed: {updated.completed}')
            else:
                print(f'Todo with ID {todo_id} not found.')
        except ValueError as e:
            print(f'Error: {e}')
            sys.exit(1)

    elif command in ('remind', 'schedule-reminder'):
        if len(args) < 2:
            print('Usage: todo remind <id> <minutes>')
            sys.exit(1)

        remind_todo_id = int(args[0])
        try:
            minutes = int(args[1])
        except ValueError:
            print('Please specify a valid number of minutes for the reminder.')
            sys.exit(1)

        todo = None
        for t in todo_manager.todos:
            if t.id == remind_todo_id:
                todo = t
                break

        if not todo:
            print(f'Todo with ID {remind_todo_id} not found.')
            sys.exit(1)

        message = f"Reminder: Please complete your task - {todo.text}"

        now = datetime.now()
        future_time = now + timedelta(minutes=minutes)
        cron_minute = future_time.minute
        cron_hour = future_time.hour
        cron_day = future_time.day
        cron_month = future_time.month

        cron_command = f'clawdbot cron add --name "todo-reminder-{remind_todo_id}" --cron "{cron_minute} {cron_hour} {cron_day} {cron_month} *" --session isolated --message "{message}" --channel whatsapp --to "+85265432195" --deliver --delete-after-run'

        print(f'Scheduling reminder for todo ID {remind_todo_id} ({todo["text"]}) in {minutes} minute(s)...')
        print(f'Command to execute: {cron_command}')

    else:
        print('''Todo List Manager

Usage:
  todo add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>
  todo list [--filter all|pending|completed] [--assignee NAME]
  todo update <id> [--text "text"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]
  todo complete <id>
  todo remove <id>
  todo clear-completed
  todo stats
  todo categories
  todo add-category <name>
  todo remove-category <name>
  todo set-category <id> <category>  (deprecated)
  todo remind <id> <minutes>''')


if __name__ == '__main__':
    main()
