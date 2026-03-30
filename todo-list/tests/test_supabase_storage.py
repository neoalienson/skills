import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from storage.supabase import SupabaseStorage, SupabaseMigration


class TestSupabaseStorageConfiguration:
    def test_default_initialization(self):
        storage = SupabaseStorage(
            url='https://test.supabase.co',
            anon_key='test-key'
        )
        assert storage.url == 'https://test.supabase.co'
        assert storage.anon_key == 'test-key'
        assert storage.todos_table == 'todos'
        assert storage.categories_table == 'categories'

    def test_custom_table_names(self):
        storage = SupabaseStorage(
            url='https://test.supabase.co',
            anon_key='test-key',
            todos_table='my_todos',
            categories_table='my_categories'
        )
        assert storage.todos_table == 'my_todos'
        assert storage.categories_table == 'my_categories'

    def test_client_lazy_initialization(self):
        storage = SupabaseStorage(
            url='https://test.supabase.co',
            anon_key='test-key'
        )
        assert storage._client is None
        storage._get_client()
        assert storage._client is not None


class TestSupabaseStorageLoad:
    @patch('supabase.create_client')
    def test_load_returns_todos_and_categories(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'id': 1, 'text': 'Task 1', 'completed': False}]),
            MagicMock(data=[{'name': 'work'}, {'name': 'home'}])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert 'todos' in result
        assert 'categories' in result
        assert len(result['todos']) == 1
        assert len(result['categories']) == 2

    @patch('supabase.create_client')
    def test_load_empty_data_returns_defaults(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[]),
            MagicMock(data=[])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert result['todos'] == []
        assert result['categories'] == [{'name': 'no category'}]

    @patch('supabase.create_client')
    def test_load_categories_empty_defaults_to_no_category(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'id': 1, 'text': 'Task 1'}]),
            MagicMock(data=[])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert result['categories'] == [{'name': 'no category'}]

    @patch('supabase.create_client')
    def test_load_network_error_returns_defaults(self, mock_create_client):
        mock_create_client.side_effect = Exception('Network error')

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert result == {'todos': [], 'categories': [{'name': 'no category'}]}

    @patch('supabase.create_client')
    def test_load_table_not_found_returns_defaults(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = Exception('table not found')
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert result == {'todos': [], 'categories': [{'name': 'no category'}]}


class TestSupabaseStorageSave:
    @patch('supabase.create_client')
    def test_save_clears_and_inserts_todos(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        data = {
            'todos': [
                {'id': 1, 'text': 'New task', 'completed': False, 'priority': 'medium', 'dueDate': None, 'category': 'work', 'createdAt': '2024-01-01'}
            ],
            'categories': [{'name': 'work'}]
        }
        storage.save(data)

        assert mock_client.table.return_value.delete.return_value.neq.return_value.execute.called
        assert mock_client.table.return_value.insert.return_value.execute.called

    @patch('supabase.create_client')
    def test_save_skips_todo_insert_when_empty(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        data = {'todos': [], 'categories': []}
        storage.save(data)

        insert_calls = [c for c in mock_client.table.return_value.insert.return_value.execute.call_args_list]
        assert len(insert_calls) == 0

    @patch('supabase.create_client')
    def test_save_network_error_raises(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.delete.return_value.neq.return_value.execute.side_effect = Exception('Network error')
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        data = {'todos': [{'id': 1}], 'categories': []}

        with pytest.raises(Exception, match='Network error'):
            storage.save(data)

    @patch('supabase.create_client')
    def test_save_only_inserts_new_categories(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[]),
            MagicMock(data=[{'name': 'work'}, {'name': 'home'}])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        data = {
            'todos': [],
            'categories': [{'name': 'work'}, {'name': 'home'}, {'name': 'new'}]
        }
        storage.save(data)


class TestSupabaseStorageExists:
    @patch('supabase.create_client')
    def test_exists_returns_true_when_table_accessible(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{'id': 1}])
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        assert storage.exists() is True

    @patch('supabase.create_client')
    def test_exists_returns_false_on_error(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception('Connection failed')
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        assert storage.exists() is False

    @patch('supabase.create_client')
    def test_exists_returns_false_on_auth_error(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception('Invalid API key')
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='invalid-key')
        assert storage.exists() is False


class TestSupabaseStorageEdgeCases:
    @patch('supabase.create_client')
    def test_load_handles_malformed_response(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            Exception('Invalid JSON response'),
            Exception('Invalid JSON response')
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert result == {'todos': [], 'categories': [{'name': 'no category'}]}

    @patch('supabase.create_client')
    def test_save_handles_concurrent_modification(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.delete.return_value.neq.return_value.execute.side_effect = [
            Exception('Conflict: row modified by another request')
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')

        with pytest.raises(Exception):
            storage.save({'todos': [], 'categories': []})

    @patch('supabase.create_client')
    def test_save_empty_categories_list(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[]),
            MagicMock(data=[])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        data = {'todos': [{'id': 1, 'text': 'Task'}], 'categories': []}
        storage.save(data)

        assert mock_client.table.return_value.insert.return_value.execute.called

    @patch('supabase.create_client')
    def test_load_with_string_categories(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'id': 1, 'text': 'Task', 'category': 'work'}]),
            MagicMock(data=[{'name': 'work'}, {'name': 'home'}])
        ]
        mock_create_client.return_value = mock_client

        storage = SupabaseStorage(url='https://test.supabase.co', anon_key='test-key')
        result = storage.load()

        assert len(result['categories']) == 2


class TestSupabaseMigrationConfiguration:
    def test_migration_initialization(self):
        migration = SupabaseMigration(
            url='https://test.supabase.co',
            service_role_key='service-key'
        )
        assert migration.url == 'https://test.supabase.co'
        assert migration.service_role_key == 'service-key'
        assert migration.todos_table == 'todos'
        assert migration.categories_table == 'categories'

    def test_migration_custom_tables(self):
        migration = SupabaseMigration(
            url='https://test.supabase.co',
            service_role_key='service-key',
            todos_table='custom_todos',
            categories_table='custom_categories'
        )
        assert migration.todos_table == 'custom_todos'
        assert migration.categories_table == 'custom_categories'


class TestSupabaseMigrationImport:
    @patch('supabase.create_client')
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.exists')
    def test_import_from_json(self, mock_exists, mock_open, mock_create_client):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
            'todos': [
                {'id': 1, 'text': 'Task 1', 'completed': False, 'priority': 'high', 'dueDate': None, 'category': 'work', 'createdAt': '2024-01-01'}
            ],
            'categories': [{'name': 'work'}]
        })

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        migration = SupabaseMigration(
            url='https://test.supabase.co',
            service_role_key='service-key'
        )
        migration.import_from_json('test.json')

        assert mock_client.table.return_value.insert.return_value.execute.call_count >= 2

    @patch('pathlib.Path.exists')
    def test_import_file_not_found(self, mock_exists):
        mock_exists.return_value = False

        migration = SupabaseMigration(
            url='https://test.supabase.co',
            service_role_key='service-key'
        )

        with pytest.raises(FileNotFoundError):
            migration.import_from_json('nonexistent.json')


class TestSupabaseStorageFactory:
    def test_factory_creates_supabase_storage(self):
        from storage import get_storage

        storage = get_storage('supabase', url='https://test.supabase.co', anon_key='test-key')

        assert isinstance(storage, SupabaseStorage)
        assert storage.url == 'https://test.supabase.co'
        assert storage.anon_key == 'test-key'

    def test_factory_raises_for_unknown_type(self):
        from storage import get_storage

        with pytest.raises(ValueError, match='Unknown storage type'):
            get_storage('unknown', url='https://test.supabase.co', anon_key='test-key')


import json
