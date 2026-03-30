import pytest
import json
from datetime import datetime

from todo import TodoManager
from tests.conftest import MockStorage


class TestBasicTodoOperations:
    def test_should_add_a_new_todo_with_default_values(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Test task')

        assert todo['text'] == 'Test task'
        assert todo['completed'] is False
        assert todo['priority'] == 'medium'
        assert todo['category'] == 'no category'
        assert todo['id'] is not None
        assert todo['createdAt'] is not None

        todos = todo_manager.list_todos()
        assert len(todos) == 1
        assert todos[0]['text'] == 'Test task'

    def test_should_add_a_new_todo_with_custom_priority_and_due_date(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('High priority task', 'high', '2023-12-31')

        assert todo['text'] == 'High priority task'
        assert todo['priority'] == 'high'
        assert todo['dueDate'] == '2023-12-31'
        assert todo['category'] == 'no category'

    def test_should_add_a_new_todo_with_a_specific_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo = todo_manager.add_todo('Work task', 'medium', None, 'work')

        assert todo['text'] == 'Work task'
        assert todo['category'] == 'work'

        categories = todo_manager.list_categories()
        assert 'work' in categories

    def test_should_list_all_todos(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_todo('Task 1')
        todo_manager.add_todo('Task 2')

        todos = todo_manager.list_todos()
        assert len(todos) == 2
        assert todos[0]['text'] == 'Task 1'
        assert todos[1]['text'] == 'Task 2'

    def test_should_list_pending_todos(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo1 = todo_manager.add_todo('Pending task')
        todo2 = todo_manager.add_todo('Completed task')

        todo_manager.mark_complete(todo2['id'])

        pending_todos = todo_manager.list_todos('pending')
        assert len(pending_todos) == 1
        assert pending_todos[0]['text'] == 'Pending task'
        assert pending_todos[0]['completed'] is False

    def test_should_list_completed_todos(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo1 = todo_manager.add_todo('Completed task')
        todo2 = todo_manager.add_todo('Pending task')

        todo_manager.mark_complete(todo1['id'])

        completed_todos = todo_manager.list_todos('completed')
        assert len(completed_todos) == 1
        assert completed_todos[0]['text'] == 'Completed task'
        assert completed_todos[0]['completed'] is True

    def test_should_mark_a_todo_as_complete(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Complete me')
        completed_todo = todo_manager.mark_complete(todo['id'])

        assert completed_todo['completed'] is True
        assert completed_todo.get('completedAt') is not None

        todos = todo_manager.list_todos()
        stored_todo = next(t for t in todos if t['id'] == todo['id'])
        assert stored_todo['completed'] is True

    def test_should_remove_a_todo(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Remove me')
        removed_todo = todo_manager.remove_todo(todo['id'])

        assert removed_todo['text'] == 'Remove me'

        todos = todo_manager.list_todos()
        assert len(todos) == 0

    def test_should_clear_completed_todos(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo1 = todo_manager.add_todo('Keep me')
        todo2 = todo_manager.add_todo('Remove me')

        todo_manager.mark_complete(todo2['id'])

        remaining_count = todo_manager.clear_completed()
        assert remaining_count == 1

        todos = todo_manager.list_todos()
        assert len(todos) == 1
        remaining_todo = next(t for t in todos if t['id'] == todo1['id'])
        assert remaining_todo['text'] == 'Keep me'


class TestCategoryManagement:
    def test_should_add_a_new_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.add_category('work')
        assert result is True

        categories = todo_manager.list_categories()
        assert 'work' in categories

    def test_should_not_add_duplicate_categories_case_insensitive(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result1 = todo_manager.add_category('Work')
        assert result1 is True

        result2 = todo_manager.add_category('WORK')
        assert result2 is False

        categories = todo_manager.list_categories()
        work_count = len([c for c in categories if c.lower() == 'work'])
        assert work_count == 1

    def test_should_reject_empty_category_names(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        with pytest.raises(ValueError, match='Category name cannot be empty'):
            todo_manager.add_category('')

        with pytest.raises(ValueError, match='Category name cannot be empty'):
            todo_manager.add_category(None)

        with pytest.raises(ValueError, match='Category name cannot be empty'):
            todo_manager.add_category('   ')

    def test_should_list_all_categories(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo_manager.add_category('personal')

        categories = todo_manager.list_categories()
        assert 'no category' in categories
        assert 'work' in categories
        assert 'personal' in categories
        assert len(categories) == 3

    def test_should_remove_category_and_reassign_todos_to_no_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo_manager.add_category('personal')

        todo1 = todo_manager.add_todo('Work task', 'medium', None, 'work')
        todo2 = todo_manager.add_todo('Personal task', 'medium', None, 'personal')

        result = todo_manager.remove_category('work')
        assert result is True

        categories = todo_manager.list_categories()
        assert 'work' not in categories
        assert 'personal' in categories
        assert 'no category' in categories

        all_todos = todo_manager.list_todos()
        work_todo = next(t for t in all_todos if t['id'] == todo1['id'])
        assert work_todo['category'] == 'no category'

        personal_todo = next(t for t in all_todos if t['id'] == todo2['id'])
        assert personal_todo['category'] == 'personal'

    def test_should_return_false_when_removing_non_existent_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.remove_category('nonexistent')
        assert result is False

    def test_should_reject_removing_empty_category_name(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        with pytest.raises(ValueError, match='Category name cannot be empty'):
            todo_manager.remove_category('')

    def test_should_update_todo_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo_manager.add_category('personal')

        todo = todo_manager.add_todo('Test task', 'medium', None, 'no category')

        updated_todo = todo_manager.update_todo_category(todo['id'], 'work')
        assert updated_todo['category'] == 'work'

        all_todos = todo_manager.list_todos()
        stored_todo = next(t for t in all_todos if t['id'] == todo['id'])
        assert stored_todo['category'] == 'work'

    def test_should_create_category_if_not_exists_when_updating_todo_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Test task')

        updated_todo = todo_manager.update_todo_category(todo['id'], 'new category')
        assert updated_todo['category'] == 'new category'

        categories = todo_manager.list_categories()
        assert 'new category' in categories

    def test_should_return_null_when_updating_category_for_non_existent_todo(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.update_todo_category(999999, 'work')
        assert result is None

    def test_should_reject_empty_category_name_when_updating_todo_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Test task')

        with pytest.raises(ValueError, match='Category cannot be empty'):
            todo_manager.update_todo_category(todo['id'], '')


class TestCategoryBasedFiltering:
    def test_should_list_todos_by_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo_manager.add_category('personal')

        todo_manager.add_todo('Work task 1', 'medium', None, 'work')
        todo_manager.add_todo('Work task 2', 'medium', None, 'work')
        todo_manager.add_todo('Personal task', 'medium', None, 'personal')

        work_todos = todo_manager.list_todos('all', 'work')
        assert len(work_todos) == 2
        for todo in work_todos:
            assert todo['category'] == 'work'

        personal_todos = todo_manager.list_todos('all', 'personal')
        assert len(personal_todos) == 1
        assert personal_todos[0]['category'] == 'personal'

    def test_should_combine_category_and_status_filtering(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')

        pending_work_todo = todo_manager.add_todo('Pending work', 'medium', None, 'work')
        completed_work_todo = todo_manager.add_todo('Completed work', 'medium', None, 'work')

        todo_manager.mark_complete(completed_work_todo['id'])

        pending_work_todos = todo_manager.list_todos('pending', 'work')
        assert len(pending_work_todos) == 1
        assert pending_work_todos[0]['id'] == pending_work_todo['id']
        assert pending_work_todos[0]['completed'] is False

        completed_work_todos = todo_manager.list_todos('completed', 'work')
        assert len(completed_work_todos) == 1
        assert completed_work_todos[0]['id'] == completed_work_todo['id']
        assert completed_work_todos[0]['completed'] is True

    def test_should_handle_no_category_filtering(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_without_category = todo_manager.add_todo('No category task')
        todo_explicit_no_category = todo_manager.add_todo('Explicit no category', 'medium', None, 'no category')

        todo_manager.add_category('work')
        work_todo = todo_manager.add_todo('Work task', 'medium', None, 'work')

        no_category_todos = todo_manager.list_todos('all', 'no category')
        assert len(no_category_todos) == 2

        no_cat_ids = [t['id'] for t in no_category_todos]
        assert todo_without_category['id'] in no_cat_ids
        assert todo_explicit_no_category['id'] in no_cat_ids
        assert work_todo['id'] not in no_cat_ids


class TestDataPersistence:
    def test_should_save_and_load_todos_with_categories(self, mock_storage):
        todo_manager1 = TodoManager(storage_backend=mock_storage)
        todo_manager1.add_category('work')
        todo_manager1.add_category('personal')

        todo1 = todo_manager1.add_todo('Work task', 'high', '2023-12-31', 'work')
        todo2 = todo_manager1.add_todo('Personal task', 'low', None, 'personal')

        assert mock_storage.save_called is True

        todos = mock_storage.last_saved_data['todos']
        categories = mock_storage.last_saved_data['categories']
        assert len(todos) == 2
        assert 'work' in categories
        assert 'personal' in categories

        mock_storage.load_called = False
        todo_manager2 = TodoManager(storage_backend=mock_storage)
        assert mock_storage.load_called is True

        loaded_todos = todo_manager2.list_todos()
        assert len(loaded_todos) == 2

    def test_should_handle_saving_and_loading_with_proper_data_structure(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('test')
        todo_manager.add_todo('Test task', 'medium', None, 'test')

        saved_data = mock_storage.last_saved_data
        assert 'todos' in saved_data
        assert 'categories' in saved_data
        assert isinstance(saved_data['todos'], list)
        assert isinstance(saved_data['categories'], list)
        assert len(saved_data['todos']) == 1
        assert len(saved_data['categories']) == 2


class TestEdgeCasesAndErrorHandling:
    def test_should_handle_non_existent_todo_ids_gracefully(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.mark_complete(999999)
        assert result is None

        result2 = todo_manager.remove_todo(999999)
        assert result2 is None

    def test_should_normalize_category_names_properly(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.add_category('  Work  ')
        assert result is True

        categories = todo_manager.list_categories()
        assert any(cat.strip() == 'Work' for cat in categories)

        todo_manager.add_category('work')
        categories_after = todo_manager.list_categories()
        work_matches = [c for c in categories_after if c.lower() == 'work']
        assert len(work_matches) == 1


class TestBackwardCompatibility:
    def test_should_handle_old_format_array_of_todos_only(self, mock_storage):
        mock_storage.set_data([
            {
                'id': 1,
                'text': 'Old task',
                'completed': False,
                'createdAt': '2023-01-01T00:00:00.000Z',
                'priority': 'medium',
                'dueDate': None
            }
        ])

        todo_manager = TodoManager(storage_backend=mock_storage)

        assert len(todo_manager.todos) == 1
        assert todo_manager.todos[0]['text'] == 'Old task'
        assert todo_manager.todos[0]['id'] == 1
        assert len(todo_manager.categories) == 1
        assert todo_manager.categories[0] == 'no category'

    def test_should_handle_missing_properties_in_old_format_gracefully(self, mock_storage):
        mock_storage.set_data([
            {
                'id': 1,
                'text': 'Minimal task',
                'completed': False
            }
        ])

        todo_manager = TodoManager(storage_backend=mock_storage)

        todos = todo_manager.list_todos()
        assert len(todos) == 1
        todo = todos[0]
        assert todo['text'] == 'Minimal task'
        assert todo['completed'] is False

    def test_should_maintain_backward_compatibility_when_adding_categories_to_old_data(self, mock_storage):
        mock_storage.set_data([
            {
                'id': 1,
                'text': 'Old task',
                'completed': False,
                'createdAt': '2023-01-01T00:00:00.000Z',
                'priority': 'medium'
            }
        ])

        todo_manager = TodoManager(storage_backend=mock_storage)

        categories = todo_manager.list_categories()
        assert len(categories) == 1
        assert categories[0] == 'no category'

        todo_manager.add_category('new-cat')
        updated_categories = todo_manager.list_categories()
        assert 'new-cat' in updated_categories

        new_todo = todo_manager.add_todo('New task', 'high', None, 'new-cat')
        assert new_todo['category'] == 'new-cat'


class TestStatistics:
    def test_should_provide_accurate_statistics_including_by_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_category('work')
        todo_manager.add_category('personal')

        todo_manager.add_todo('Work task 1', 'high', None, 'work')
        todo_manager.add_todo('Work task 2', 'medium', None, 'work')
        todo_manager.add_todo('Personal task', 'low', None, 'personal')
        todo_manager.add_todo('No category task', 'medium', None, 'no category')

        work_todo = next(t for t in todo_manager.list_todos() if t.get('category') == 'work')
        todo_manager.mark_complete(work_todo['id'])

        stats = todo_manager.get_stats()

        assert stats['total'] == 4
        assert stats['completed'] == 1
        assert stats['pending'] == 3

        assert stats['categories']['work'] == 2
        assert stats['categories']['personal'] == 1
        assert stats['categories']['no category'] == 1

        assert stats['priorities']['high'] == 1
        assert stats['priorities']['medium'] == 2
        assert stats['priorities']['low'] == 1

    def test_should_handle_overdue_todos_in_statistics(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_todo('Overdue task', 'medium', '2020-01-01')
        todo_manager.add_todo('Future task', 'medium', '2030-01-01')
        todo_manager.add_todo('No due task', 'medium', None)

        stats = todo_manager.get_stats()
        assert stats['overdue'] == 1


class TestAdditionalEdgeCases:
    def test_should_reject_empty_todo_text(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        with pytest.raises(ValueError, match='Todo text cannot be empty'):
            todo_manager.add_todo('')

        with pytest.raises(ValueError, match='Todo text cannot be empty'):
            todo_manager.add_todo('   ')

    def test_should_reject_invalid_priority_value(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        valid_priorities = ['high', 'medium', 'low']
        for invalid_priority in ['invalid', 'urgent', 'critical', 'HIGH', 'Medium', '']:
            if invalid_priority not in valid_priorities:
                try:
                    todo_manager.add_todo('Test task', invalid_priority)
                    assert False, f'Expected ValueError for priority: {invalid_priority}'
                except ValueError as e:
                    assert 'Invalid priority' in str(e)

    def test_should_reject_invalid_due_date_format(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        invalid_dates = ['not-a-date', '2024/01/01', '01-01-2024', 'yesterday', 'tomorrow']
        for invalid_date in invalid_dates:
            try:
                todo_manager.add_todo('Test task', 'medium', invalid_date)
                assert False, f'Expected ValueError for date: {invalid_date}'
            except ValueError:
                pass

    def test_should_handle_special_characters_in_todo_text(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        special_texts = [
            'Task with "double quotes"',
            "Task with 'single quotes'",
            'Task with <brackets>',
            'Task with $ymbols & ampersand',
            'Task with newline\ncharacter',
            'Task with\ttab\tcharacter',
        ]

        for text in special_texts:
            todo = todo_manager.add_todo(text)
            assert todo['text'] == text
            loaded_todos = todo_manager.list_todos()
            loaded_todo = next(t for t in loaded_todos if t['id'] == todo['id'])
            assert loaded_todo['text'] == text

    def test_should_handle_unicode_in_todo_text(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        unicode_texts = [
            'Unicode task: \u4e2d\u6587',
            'Emoji task: \U0001f4dd',
            'Accents: caf\u00e9, na\u00efve',
            'Japanese: \u65e5\u672c\u8a9e',
        ]

        for text in unicode_texts:
            todo = todo_manager.add_todo(text)
            assert todo['text'] == text
            loaded_todos = todo_manager.list_todos()
            loaded_todo = next(t for t in loaded_todos if t['id'] == todo['id'])
            assert loaded_todo['text'] == text

    def test_should_not_allow_removing_last_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        with pytest.raises(ValueError, match='Cannot remove the last remaining category'):
            todo_manager.remove_category('no category')

        categories = todo_manager.list_categories()
        assert 'no category' in categories
        assert len(categories) == 1

    def test_should_handle_due_date_before_created_date(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Test task', 'medium', '2020-01-01')
        assert todo['dueDate'] == '2020-01-01'

        stats = todo_manager.get_stats()
        assert stats['overdue'] == 1

    def test_should_handle_very_long_todo_text(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        long_text = 'A' * 10000
        todo = todo_manager.add_todo(long_text)
        assert todo['text'] == long_text

        loaded_todos = todo_manager.list_todos()
        loaded_todo = next(t for t in loaded_todos if t['id'] == todo['id'])
        assert loaded_todo['text'] == long_text

    def test_should_handle_duplicate_todo_ids_gracefully(self, mock_storage):
        duplicate_id = 1234567890

        mock_storage.set_data({
            'todos': [
                {
                    'id': duplicate_id,
                    'text': 'First task',
                    'completed': False,
                    'createdAt': datetime.now().isoformat(),
                    'priority': 'medium',
                    'dueDate': None,
                    'category': 'no category'
                },
                {
                    'id': duplicate_id,
                    'text': 'Second task',
                    'completed': False,
                    'createdAt': datetime.now().isoformat(),
                    'priority': 'high',
                    'dueDate': None,
                    'category': 'no category'
                }
            ],
            'categories': ['no category']
        })

        todo_manager = TodoManager(storage_backend=mock_storage)

        todos = todo_manager.list_todos()
        duplicate_todos = [t for t in todos if t['id'] == duplicate_id]
        assert len(duplicate_todos) == 2

    def test_should_mark_already_completed_todo_as_complete(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo = todo_manager.add_todo('Test task')
        todo_manager.mark_complete(todo['id'])

        completed_todo = todo_manager.mark_complete(todo['id'])
        assert completed_todo['completed'] is True
        assert 'completedAt' in completed_todo

    def test_should_handle_category_name_with_special_characters(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        special_categories = [
            'work-home',
            'work/home',
            'category.with.dots',
            'category_with_underscores',
        ]

        for cat in special_categories:
            result = todo_manager.add_category(cat)
            assert result is True
            categories = todo_manager.list_categories()
            assert cat in categories


class TestConfigAndStorage:
    def test_should_use_storage_backend_provided(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todo_manager.add_todo('Test task')
        todos = todo_manager.list_todos()
        assert len(todos) == 1

    def test_should_fail_when_storage_not_defined(self):
        import config as config_module
        original_find = config_module.Config._find_config

        def mock_find(self):
            return None

        config_module.Config._find_config = mock_find
        try:
            cfg = config_module.Config(fail_if_no_config=True)
            assert False, 'Expected ValueError'
        except ValueError as e:
            assert 'not defined' in str(e).lower() or 'config' in str(e).lower()
        finally:
            config_module.Config._find_config = original_find


class TestListCommandOutput:
    def test_list_returns_todo_items(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo_manager.add_todo('Test task', 'high', '2026-04-01', 'work', 'Neo')

        todos = todo_manager.list_todos('all')

        assert len(todos) == 1
        assert todos[0].text == 'Test task'
        assert todos[0].priority == 'high'
        assert todos[0].dueDate == '2026-04-01'
        assert todos[0].category == 'work'
        assert todos[0].assignee == 'Neo'

    def test_list_with_assignee_filter(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo_manager.add_todo('Task 1', 'medium', None, 'no category', 'Neo')
        todo_manager.add_todo('Task 2', 'medium', None, 'no category', 'Jane')
        todo_manager.add_todo('Task 3', 'medium', None, 'no category', 'Neo')

        todos = todo_manager.list_todos('all', None, 'Neo')

        assert len(todos) == 2
        assert all(t.assignee == 'Neo' for t in todos)

    def test_list_with_category_filter_case_insensitive(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo_manager.add_category('Work')
        todo_manager.add_todo('Task 1', 'medium', None, 'Work')
        todo_manager.add_todo('Task 2', 'medium', None, 'work')

        todos = todo_manager.list_todos('all', 'WORK')

        assert len(todos) == 2

    def test_list_empty_result(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        todos = todo_manager.list_todos('all')

        assert len(todos) == 0

    def test_list_filter_pending_only(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo_manager.add_todo('Pending task')
        todo_manager.add_todo('Completed task')
        todo_manager.mark_complete(todo_manager.list_todos('all')[1].id)

        pending = todo_manager.list_todos('pending')

        assert len(pending) == 1
        assert pending[0].text == 'Pending task'
        assert pending[0].completed is False

    def test_list_filter_completed_only(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo_manager.add_todo('Pending task')
        todo_manager.add_todo('Completed task')
        todo_manager.mark_complete(todo_manager.list_todos('all')[1].id)

        completed = todo_manager.list_todos('completed')

        assert len(completed) == 1
        assert completed[0].text == 'Completed task'
        assert completed[0].completed is True


class TestUpdateCommand:
    def test_update_priority(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, priority='high')

        assert updated.priority == 'high'

    def test_update_assignee(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, assignee='Neo')

        assert updated.assignee == 'Neo'

    def test_update_assignee_empty_string(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task', assignee='Neo')

        updated = todo_manager.update_todo(todo.id, assignee='')

        assert updated.assignee == ''

    def test_update_multiple_fields(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, priority='high', assignee='Neo', due_date='2026-04-01')

        assert updated.priority == 'high'
        assert updated.assignee == 'Neo'
        assert updated.dueDate == '2026-04-01'

    def test_update_text(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, text='Updated text')

        assert updated.text == 'Updated text'

    def test_update_invalid_priority_raises_error(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        with pytest.raises(ValueError, match='Invalid priority'):
            todo_manager.update_todo(todo.id, priority='invalid')

    def test_update_empty_text_raises_error(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        with pytest.raises(ValueError, match='Todo text cannot be empty'):
            todo_manager.update_todo(todo.id, text='')

    def test_update_nonexistent_todo_returns_none(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)

        result = todo_manager.update_todo(99999, priority='high')

        assert result is None

    def test_update_due_date_clears_with_empty(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task', due_date='2026-04-01')

        updated = todo_manager.update_todo(todo.id, due_date='')

        assert updated.dueDate == ''

    def test_update_invalid_due_date_raises_error(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        with pytest.raises(ValueError, match='Invalid due date format'):
            todo_manager.update_todo(todo.id, due_date='invalid-date')

    def test_update_category_creates_new_category(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, category='NewCategory')

        assert updated.category == 'NewCategory'
        assert 'NewCategory' in todo_manager.list_categories()

    def test_update_completed_status(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        updated = todo_manager.update_todo(todo.id, completed=True)

        assert updated.completed is True
        assert updated.completedAt is not None

    def test_update_pending_status_clears_completedAt(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')
        todo_manager.mark_complete(todo.id)

        updated = todo_manager.update_todo(todo.id, completed=False)

        assert updated.completed is False
        assert updated.completedAt is None


class TestTodoItemModel:
    def test_todo_item_dict_access(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task', 'high', '2026-04-01', 'work', 'Neo')

        assert todo['text'] == 'Test task'
        assert todo['priority'] == 'high'
        assert todo['dueDate'] == '2026-04-01'
        assert todo['category'] == 'work'
        assert todo['assignee'] == 'Neo'

    def test_todo_item_get_method(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        assert todo.get('text') == 'Test task'
        assert todo.get('nonexistent', 'default') == 'default'

    def test_todo_item_contains(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        assert 'text' in todo
        assert 'nonexistent' not in todo

    def test_todo_item_assignment(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task')

        todo.text = 'Updated text'
        todo.assignee = 'Neo'

        assert todo.text == 'Updated text'
        assert todo.assignee == 'Neo'

    def test_todo_item_model_dump(self, mock_storage):
        todo_manager = TodoManager(storage_backend=mock_storage)
        todo = todo_manager.add_todo('Test task', 'high', '2026-04-01', 'work', 'Neo')

        data = todo.model_dump()

        assert data['text'] == 'Test task'
        assert data['priority'] == 'high'
        assert data['dueDate'] == '2026-04-01'
        assert data['category'] == 'work'
        assert data['assignee'] == 'Neo'
        assert data['completed'] is False

    def test_todo_item_backward_compatibility_missing_fields(self, mock_storage):
        mock_storage.set_data({
            'todos': [
                {
                    'id': 1,
                    'text': 'Minimal task',
                    'completed': False
                }
            ],
            'categories': ['no category']
        })

        todo_manager = TodoManager(storage_backend=mock_storage)
        todos = todo_manager.list_todos()

        assert len(todos) == 1
        assert todos[0].text == 'Minimal task'
        assert todos[0].assignee is None
        assert todos[0].completedAt is None
        assert todos[0].priority == 'medium'
