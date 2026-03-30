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
        self._original_ids = set()  # Track IDs loaded from storage
        self._deleted_ids = set()    # Track deleted IDs for sync
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
                secret_key=cfg.storage.supabase.secret_key,
                publishable_key=cfg.storage.supabase.publishable_key,
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
            # Track original IDs for sync
            self._original_ids = {t.id for t in self.todos}
            self._deleted_ids = set()
        except Exception as e:
            print(f'Error loading todos: {e}')
            self.todos = []
            self.categories = ['no category']
            self._original_ids = set()
            self._deleted_ids = set()

    def save_todos(self):
        try:
            # Check if storage supports individual add/update/delete
            has_add = hasattr(self._storage, 'add') and callable(getattr(self._storage, 'add', None))
            has_update = hasattr(self._storage, 'update') and callable(getattr(self._storage, 'update', None))
            has_delete = hasattr(self._storage, 'delete') and callable(getattr(self._storage, 'delete', None))
            
            supports_crud = has_add and has_update and has_delete
            
            if supports_crud:
                # Use individual add/update/delete for Supabase
                current_ids = set()
                
                for todo in self.todos:
                    todo_dict = todo.model_dump()
                    current_ids.add(todo.id)
                    
                    if todo.id not in self._original_ids:
                        # New todo - insert and get generated ID
                        new_id = self._storage.add(todo_dict)
                        todo.id = new_id
                    else:
                        # Existing todo - update
                        self._storage.update(todo_dict)
                
                # Delete removed todos
                for deleted_id in self._deleted_ids:
                    if deleted_id in self._original_ids:
                        self._storage.delete(deleted_id)
                
                # Save categories
                data_to_save = {'categories': self.categories}
                self._storage.save(data_to_save)
                
                # Reset tracking
                self._original_ids = current_ids
                self._deleted_ids = set()
            else:
                # Use bulk save for Local/GitHub storage
                data_to_save = {
                    'todos': [t.model_dump() for t in self.todos],
                    'categories': self.categories
                }
                self._storage.save(data_to_save)
        except Exception as e:
            print(f'Error saving todos: {e}')
            raise

    def _get_category_name(self, cat):
        """Get category name from either dict or string format."""
        return cat['name'].lower() if isinstance(cat, dict) else cat.lower()

    def add_category(self, category_name):
        if category_name is None or (isinstance(category_name, str) and not category_name.strip()):
            raise ValueError('Category name cannot be empty')

        normalized_category = category_name.strip()

        for cat in self.categories:
            if self._get_category_name(cat) == normalized_category.lower():
                return False

        self.categories.append({"name": normalized_category})
        self.save_todos()
        return True

    def remove_category(self, category_name):
        if category_name is None or (isinstance(category_name, str) and not category_name.strip()):
            raise ValueError('Category name cannot be empty')

        if len(self.categories) == 1 and self._get_category_name(self.categories[0]) == category_name.strip().lower():
            raise ValueError('Cannot remove the last remaining category')

        normalized_category = category_name.strip()
        initial_length = len(self.categories)

        self.categories = [cat for cat in self.categories
                          if self._get_category_name(cat) != normalized_category.lower()]

        if initial_length != len(self.categories):
            for todo in self.todos:
                if todo.category.lower() == normalized_category.lower():
                    todo.category = 'no category'
            self.save_todos()
            return True

        return False

    def list_categories(self):
        return [c['name'] if isinstance(c, dict) else c for c in self.categories]

    def add_todo(self, item, priority='medium', due_date=None, category='no category', assignee=None):
        if item is None or (isinstance(item, str) and not item.strip()):
            raise ValueError('Todo text cannot be empty')

        valid_priorities = ['high', 'medium', 'low', 'backlog']
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

    def list_todos(self, filter_type='all', category=None, assignee=None, list_='default'):
        filtered_todos = list(self.todos)

        if list_ == 'default':
            filtered_todos = [t for t in filtered_todos if t.priority.lower() != 'backlog']
        elif list_ == 'backlog':
            filtered_todos = [t for t in filtered_todos if t.priority.lower() == 'backlog']
        elif list_ == 'all':
            pass

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
                self._deleted_ids.add(todo_id)
                self.save_todos()
                return removed
        return None



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
                    if priority not in ('high', 'medium', 'low', 'backlog'):
                        raise ValueError(f'Invalid priority "{priority}". Must be one of: high, medium, low, backlog')
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
                    category_names = self.list_categories()
                    if category and category not in category_names:
                        self.add_category(category)
                    todo.category = category if category else 'no category'

                if 'assignee' in kwargs:
                    todo.assignee = kwargs['assignee']

                if 'id' in kwargs:
                    new_id = kwargs['id']
                    if not isinstance(new_id, int):
                        try:
                            new_id = int(new_id)
                        except (ValueError, TypeError):
                            raise ValueError(f'Invalid ID "{new_id}". Must be an integer')
                    if any(t.id == new_id and t.id != todo_id for t in self.todos):
                        raise ValueError(f'ID {new_id} already exists')
                    todo.id = new_id

                if 'completed' in kwargs:
                    todo.completed = kwargs['completed']
                    if todo.completed:
                        todo.completedAt = datetime.now().isoformat()
                    else:
                        todo.completedAt = None

                self.save_todos()
                return todo
        return None





def main():
    import sys

    if len(sys.argv) < 2:
        print('''Todo List Manager

Usage:
  todo add [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>
  todo list [--filter all|pending|completed] [--list default|backlog|all] [--category NAME] [--assignee NAME] [--json|--text]
  todo update <id> [--text "text"] [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending] [--id NEW_ID]
  todo complete <id>
  todo remove <id>
  todo stats
  todo categories
  todo add-category <name>
  todo remove-category <name>
  todo export [--format json|yaml]''')
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
  todo add [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>

Options:
  --priority high|medium|low|backlog    Set priority (default: medium)
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
            print('Usage: todo add [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>')
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
  todo list [--filter all|pending|completed] [--category NAME] [--assignee NAME] [--list default|backlog|all] [--fields FIELD1,FIELD2,...] [--json|--text]

Options:
  --filter all|pending|completed    Filter by status (default: pending)
  --category NAME                   Filter by category (case insensitive)
  --assignee NAME                   Filter by assignee (case insensitive)
  --list default|backlog|all        Filter by list (default: default, excludes backlog)
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
        list_filter = 'default'
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
                list_filter = 'all'
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
            elif args[i] == '--list' and i + 1 < len(args):
                list_filter = args[i + 1]
                i += 2
            else:
                i += 1

        todos = todo_manager.list_todos(filter_type, category_filter, assignee_filter, list_filter)

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

    elif command == 'update':
        if not args or args[0] in ('-h', '--help'):
            print('''Usage:
  todo update <id> [--text "text"] [--priority high|medium|low|backlog]
                   [--due YYYY-MM-DD] [--category NAME] [--assignee NAME]
                   [--completed | --pending] [--id NEW_ID]

Options:
  --text "text"                   Update the todo text
  --priority high|medium|low|backlog      Update priority
  --due YYYY-MM-DD              Update due date (use empty to clear)
  --category NAME               Update category
  --assignee NAME               Update assignee (use empty string to clear)
  --completed                   Mark as completed
  --pending                      Mark as pending
  --id NEW_ID                   Change the todo ID
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
            elif args[i] == '--id' and i + 1 < len(args):
                update_kwargs['id'] = args[i + 1]
                i += 2
            elif args[i].isdigit() and todo_id is None:
                todo_id = int(args[i])
                i += 1
            else:
                i += 1

        if not todo_id:
            print('Error: Todo ID is required')
            print('Usage: todo update <id> [--text "text"] [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME]')
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

    else:
        print('''Todo List Manager

Usage:
  todo add [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>
  todo list [--filter all|pending|completed] [--list default|backlog|all] [--category NAME] [--assignee NAME] [--json|--text]
  todo update <id> [--text "text"] [--priority high|medium|low|backlog] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending] [--id NEW_ID]
  todo complete <id>
  todo remove <id>
  todo stats
  todo categories
  todo add-category <name>
  todo remove-category <name>
  todo export [--format json|yaml]''')


if __name__ == '__main__':
    main()
