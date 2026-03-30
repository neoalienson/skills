#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def main():
    args = sys.argv[1:]

    if not args:
        print('''Todo List Manager

Usage:
  /todo add [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] <item text>
  /todo list [--filter all|pending|completed] [--assignee NAME]
  /todo update <id> [--text "text"] [--priority high|medium|low] [--due YYYY-MM-DD] [--category NAME] [--assignee NAME] [--completed|--pending]
  /todo complete <id>
  /todo remove <id>
  /todo clear-completed
  /todo stats
  /todo categories
  /todo add-category <name>
  /todo remove-category <name>
  /todo set-category <id> <category>  (deprecated)
''')
        sys.exit(0)

    try:
        script_dir = Path.cwd() / 'skills' / 'todo-list'
        command = ['python', str(script_dir / 'todo.py')] + args

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(result.stdout.strip())
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except Exception as e:
        print(f'Error executing todo command: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
