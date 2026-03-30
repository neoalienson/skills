#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.supabase import SupabaseMigration


def main():
    parser = argparse.ArgumentParser(description='Supabase migration utility')
    parser.add_argument('--url', required=True, help='Supabase project URL')
    parser.add_argument('--service-key', required=True, help='Supabase service role key')
    parser.add_argument('--todos-table', default='todos', help='Todos table name')
    parser.add_argument('--categories-table', default='categories', help='Categories table name')
    parser.add_argument('--create-tables', action='store_true', help='Create tables')
    parser.add_argument('--drop-tables', action='store_true', help='Drop tables')
    parser.add_argument('--import-json', metavar='FILE', help='Import data from JSON file')

    args = parser.parse_args()

    migration = SupabaseMigration(
        url=args.url,
        service_role_key=args.service_key,
        todos_table=args.todos_table,
        categories_table=args.categories_table
    )

    if args.drop_tables:
        print('Dropping tables...')
        migration.drop_tables()
        print('Done.')

    if args.create_tables:
        print('Creating tables...')
        migration.create_tables()
        print('Done.')

    if args.import_json:
        print(f'Importing data from {args.import_json}...')
        migration.import_from_json(args.import_json)
        print('Done.')


if __name__ == '__main__':
    main()
