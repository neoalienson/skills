import { strict as assert } from 'assert';
import { readFileSync, writeFileSync, unlinkSync, existsSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import TodoManager from './todo.mjs';

// Comprehensive unit tests for TodoManager with Category Functionality
// Each test uses a separate temporary file to ensure isolation

async function runTests() {
  console.log('🧪 Running TodoManager unit tests...\n');

  let testsPassed = 0;
  let testsFailed = 0;

  async function test(description, fn) {
    try {
      await fn();
      console.log(`✅ PASS: ${description}`);
      testsPassed++;
    } catch (error) {
      console.log(`❌ FAIL: ${description}`);
      console.log(`   Error: ${error.message}`);
      testsFailed++;
    }
  }

  async function describe(description, fn) {
    console.log(`\n📋 ${description}`);
    await fn();
  }

  // Test helper to create a fresh TodoManager instance for each test
  async function withFreshTodoManager(fn) {
    const tempDir = tmpdir();
    const tempTodoFile = join(tempDir, `test-todo-data-${Date.now()}-${Math.random()}.json`);
    
    const todoManager = new TodoManager(tempDir);
    todoManager.todoFile = tempTodoFile;
    
    // Initialize with clean state
    todoManager.todos = [];
    todoManager.categories = ['no category'];
    todoManager.saveTodos();
    
    try {
      await fn(todoManager, tempTodoFile);
    } finally {
      // Cleanup
      if (existsSync(tempTodoFile)) {
        try {
          unlinkSync(tempTodoFile);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    }
  }

  await describe('Basic Todo Operations', async () => {
    await test('should add a new todo with default values', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('Test task');
        
        assert.strictEqual(todo.text, 'Test task');
        assert.strictEqual(todo.completed, false);
        assert.strictEqual(todo.priority, 'medium');
        assert.strictEqual(todo.category, 'no category');
        assert.ok(todo.id);
        assert.ok(todo.createdAt);
        
        // Verify it was saved
        const todos = todoManager.listTodos();
        assert.strictEqual(todos.length, 1);
        assert.strictEqual(todos[0].text, 'Test task');
      });
    });

    await test('should add a new todo with custom priority and due date', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('High priority task', 'high', '2023-12-31');
        
        assert.strictEqual(todo.text, 'High priority task');
        assert.strictEqual(todo.priority, 'high');
        assert.strictEqual(todo.dueDate, '2023-12-31');
        assert.strictEqual(todo.category, 'no category');
      });
    });

    await test('should add a new todo with a specific category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add a new category first
        todoManager.addCategory('work');
        
        const todo = todoManager.addTodo('Work task', 'medium', null, 'work');
        
        assert.strictEqual(todo.text, 'Work task');
        assert.strictEqual(todo.category, 'work');
        
        // Verify the category was added to the categories list
        const categories = todoManager.listCategories();
        assert(categories.includes('work'));
      });
    });

    await test('should list all todos', async () => {
      await withFreshTodoManager(async (todoManager) => {
        todoManager.addTodo('Task 1');
        todoManager.addTodo('Task 2');
        
        const todos = todoManager.listTodos();
        assert.strictEqual(todos.length, 2);
        assert.strictEqual(todos[0].text, 'Task 1');
        assert.strictEqual(todos[1].text, 'Task 2');
      });
    });

    await test('should list pending todos', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo1 = todoManager.addTodo('Pending task');
        const todo2 = todoManager.addTodo('Completed task');
        
        // Mark one as complete
        todoManager.markComplete(todo2.id);
        
        const pendingTodos = todoManager.listTodos('pending');
        assert.strictEqual(pendingTodos.length, 1);
        assert.strictEqual(pendingTodos[0].text, 'Pending task');
        assert.strictEqual(pendingTodos[0].completed, false);
      });
    });

    await test('should list completed todos', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo1 = todoManager.addTodo('Completed task');
        const todo2 = todoManager.addTodo('Pending task');
        
        // Mark one as complete
        todoManager.markComplete(todo1.id);
        
        const completedTodos = todoManager.listTodos('completed');
        assert.strictEqual(completedTodos.length, 1);
        assert.strictEqual(completedTodos[0].text, 'Completed task');
        assert.strictEqual(completedTodos[0].completed, true);
      });
    });

    await test('should mark a todo as complete', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('Complete me');
        const completedTodo = todoManager.markComplete(todo.id);
        
        assert.strictEqual(completedTodo.completed, true);
        assert.ok(completedTodo.completedAt);
        
        // Verify it's actually marked as complete in storage
        const todos = todoManager.listTodos();
        const storedTodo = todos.find(t => t.id === todo.id);
        assert.strictEqual(storedTodo.completed, true);
      });
    });

    await test('should remove a todo', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('Remove me');
        const removedTodo = todoManager.removeTodo(todo.id);
        
        assert.strictEqual(removedTodo.text, 'Remove me');
        
        // Verify it's removed from storage
        const todos = todoManager.listTodos();
        assert.strictEqual(todos.length, 0);
      });
    });

    await test('should clear completed todos', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo1 = todoManager.addTodo('Keep me');
        const todo2 = todoManager.addTodo('Remove me');
        
        // Mark the 'Remove me' todo as complete
        todoManager.markComplete(todo2.id);
        
        const remainingCount = todoManager.clearCompleted();
        assert.strictEqual(remainingCount, 1);
        
        const todos = todoManager.listTodos();
        assert.strictEqual(todos.length, 1);
        // After clearing completed todos, only the uncompleted one should remain
        // Find the remaining todo and verify it's the 'Keep me' one
        const remainingTodo = todos.find(t => t.id === todo1.id);
        assert.ok(remainingTodo, 'The uncompleted todo should still exist');
        assert.strictEqual(remainingTodo.text, 'Keep me');
      });
    });
  });

  await describe('Category Management', async () => {
    await test('should add a new category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const result = todoManager.addCategory('work');
        assert.strictEqual(result, true);
        
        const categories = todoManager.listCategories();
        assert(categories.includes('work'));
      });
    });

    await test('should not add duplicate categories (case insensitive)', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const result1 = todoManager.addCategory('Work');
        assert.strictEqual(result1, true);
        
        const result2 = todoManager.addCategory('WORK');
        assert.strictEqual(result2, false); // Should return false for duplicate
        
        const categories = todoManager.listCategories();
        const workCount = categories.filter(cat => cat.toLowerCase() === 'work').length;
        assert.strictEqual(workCount, 1); // Only one 'work' category should exist
      });
    });

    await test('should reject empty category names', async () => {
      await withFreshTodoManager(async (todoManager) => {
        assert.throws(() => todoManager.addCategory(''), {
          message: 'Category name cannot be empty'
        });
        
        assert.throws(() => todoManager.addCategory(null), {
          message: 'Category name cannot be empty'
        });
        
        assert.throws(() => todoManager.addCategory(undefined), {
          message: 'Category name cannot be empty'
        });
      });
    });

    await test('should list all categories', async () => {
      await withFreshTodoManager(async (todoManager) => {
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        const categories = todoManager.listCategories();
        assert(categories.includes('no category'));
        assert(categories.includes('work'));
        assert(categories.includes('personal'));
        assert.strictEqual(categories.length, 3);
      });
    });

    await test('should remove a category and reassign todos to "no category"', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add some categories
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        // Add todos with different categories
        const todo1 = todoManager.addTodo('Work task', 'medium', null, 'work');
        const todo2 = todoManager.addTodo('Personal task', 'medium', null, 'personal');
        
        // Remove the 'work' category
        const result = todoManager.removeCategory('work');
        assert.strictEqual(result, true);
        
        // Verify category is removed
        const categories = todoManager.listCategories();
        assert(!categories.includes('work'));
        assert(categories.includes('personal'));
        assert(categories.includes('no category'));
        
        // Verify work todo is reassigned to 'no category'
        const allTodos = todoManager.listTodos();
        const workTodo = allTodos.find(t => t.id === todo1.id);
        assert.strictEqual(workTodo.category, 'no category');
        
        // Verify personal todo keeps its category
        const personalTodo = allTodos.find(t => t.id === todo2.id);
        assert.strictEqual(personalTodo.category, 'personal');
      });
    });

    await test('should return false when trying to remove non-existent category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const result = todoManager.removeCategory('nonexistent');
        assert.strictEqual(result, false);
      });
    });

    await test('should reject removing empty category name', async () => {
      await withFreshTodoManager(async (todoManager) => {
        assert.throws(() => todoManager.removeCategory(''), {
          message: 'Category name cannot be empty'
        });
      });
    });

    await test('should update a todo\'s category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add some categories
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        // Add a todo with initial category
        const todo = todoManager.addTodo('Test task', 'medium', null, 'no category');
        
        // Update its category
        const updatedTodo = todoManager.updateTodoCategory(todo.id, 'work');
        assert.strictEqual(updatedTodo.category, 'work');
        
        // Verify the change is persisted
        const allTodos = todoManager.listTodos();
        const storedTodo = allTodos.find(t => t.id === todo.id);
        assert.strictEqual(storedTodo.category, 'work');
      });
    });

    await test('should create category if it doesn\'t exist when updating todo category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('Test task');
        
        // Update to a category that doesn't exist yet
        const updatedTodo = todoManager.updateTodoCategory(todo.id, 'new category');
        assert.strictEqual(updatedTodo.category, 'new category');
        
        // Verify the new category was added
        const categories = todoManager.listCategories();
        assert(categories.includes('new category'));
      });
    });

    await test('should return null when updating category for non-existent todo', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const result = todoManager.updateTodoCategory(999999, 'work');
        assert.strictEqual(result, null);
      });
    });

    await test('should reject empty category name when updating todo category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const todo = todoManager.addTodo('Test task');
        
        assert.throws(() => todoManager.updateTodoCategory(todo.id, ''), {
          message: 'Category cannot be empty'
        });
      });
    });
  });

  await describe('Category-Based Filtering', async () => {
    await test('should list todos by category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add categories
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        // Add todos with different categories
        todoManager.addTodo('Work task 1', 'medium', null, 'work');
        todoManager.addTodo('Work task 2', 'medium', null, 'work');
        todoManager.addTodo('Personal task', 'medium', null, 'personal');
        
        // List todos in 'work' category
        const workTodos = todoManager.listTodos('all', 'work');
        assert.strictEqual(workTodos.length, 2);
        workTodos.forEach(todo => assert.strictEqual(todo.category, 'work'));
        
        // List todos in 'personal' category
        const personalTodos = todoManager.listTodos('all', 'personal');
        assert.strictEqual(personalTodos.length, 1);
        assert.strictEqual(personalTodos[0].category, 'personal');
      });
    });

    await test('should combine category and status filtering', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add categories
        todoManager.addCategory('work');
        
        // Add todos with different statuses and categories
        const pendingWorkTodo = todoManager.addTodo('Pending work', 'medium', null, 'work');
        const completedWorkTodo = todoManager.addTodo('Completed work', 'medium', null, 'work');
        
        // Mark one as complete
        todoManager.markComplete(completedWorkTodo.id);
        
        // List pending work todos
        const pendingWorkTodos = todoManager.listTodos('pending', 'work');
        assert.strictEqual(pendingWorkTodos.length, 1);
        assert.strictEqual(pendingWorkTodos[0].id, pendingWorkTodo.id);
        assert.strictEqual(pendingWorkTodos[0].completed, false);
        
        // List completed work todos
        const completedWorkTodos = todoManager.listTodos('completed', 'work');
        assert.strictEqual(completedWorkTodos.length, 1);
        assert.strictEqual(completedWorkTodos[0].id, completedWorkTodo.id);
        assert.strictEqual(completedWorkTodos[0].completed, true);
      });
    });

    await test('should handle "no category" filtering', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add a todo without specifying a category (defaults to 'no category')
        const todoWithoutCategory = todoManager.addTodo('No category task');
        
        // Add a todo with explicit 'no category'
        const todoExplicitNoCategory = todoManager.addTodo('Explicit no category', 'medium', null, 'no category');
        
        // Add a todo with a different category
        todoManager.addCategory('work');
        const workTodo = todoManager.addTodo('Work task', 'medium', null, 'work');
        
        // List todos in 'no category'
        const noCategoryTodos = todoManager.listTodos('all', 'no category');
        assert.strictEqual(noCategoryTodos.length, 2);
        
        const noCatIds = noCategoryTodos.map(t => t.id);
        assert(noCatIds.includes(todoWithoutCategory.id));
        assert(noCatIds.includes(todoExplicitNoCategory.id));
        
        // Verify work todo is not in no category list
        assert(!noCatIds.includes(workTodo.id));
      });
    });
  });

  await describe('Data Persistence', async () => {
    await test('should save and load todos with categories', async () => {
      await withFreshTodoManager(async (todoManager, tempTodoFile) => {
        // Add some todos with categories
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        const todo1 = todoManager.addTodo('Work task', 'high', '2023-12-31', 'work');
        const todo2 = todoManager.addTodo('Personal task', 'low', null, 'personal');
        
        // Create a new instance to test loading
        const newTodoManager = new TodoManager(tmpdir());
        newTodoManager.todoFile = tempTodoFile;
        newTodoManager.loadTodos();
        
        const loadedTodos = newTodoManager.listTodos();
        assert.strictEqual(loadedTodos.length, 2);
        
        const loadedWorkTodo = loadedTodos.find(t => t.id === todo1.id);
        assert.strictEqual(loadedWorkTodo.text, 'Work task');
        assert.strictEqual(loadedWorkTodo.category, 'work');
        assert.strictEqual(loadedWorkTodo.priority, 'high');
        assert.strictEqual(loadedWorkTodo.dueDate, '2023-12-31');
        
        const loadedPersonalTodo = loadedTodos.find(t => t.id === todo2.id);
        assert.strictEqual(loadedPersonalTodo.text, 'Personal task');
        assert.strictEqual(loadedPersonalTodo.category, 'personal');
        assert.strictEqual(loadedPersonalTodo.priority, 'low');
        assert.strictEqual(loadedPersonalTodo.dueDate, null);
        
        // Check categories
        const loadedCategories = newTodoManager.listCategories();
        assert(loadedCategories.includes('work'));
        assert(loadedCategories.includes('personal'));
        assert(loadedCategories.includes('no category'));
      });
    });

    await test('should handle saving and loading with proper data structure', async () => {
      await withFreshTodoManager(async (todoManager, tempTodoFile) => {
        // Add some data
        todoManager.addCategory('test');
        todoManager.addTodo('Test task', 'medium', null, 'test');
        
        // Check the saved file structure
        const savedData = JSON.parse(readFileSync(tempTodoFile, 'utf8'));
        assert.ok(savedData.hasOwnProperty('todos'));
        assert.ok(savedData.hasOwnProperty('categories'));
        assert(Array.isArray(savedData.todos));
        assert(Array.isArray(savedData.categories));
        
        assert.strictEqual(savedData.todos.length, 1);
        assert.strictEqual(savedData.categories.length, 2); // 'no category' + 'test'
      });
    });
  });

  await describe('Edge Cases and Error Handling', async () => {
    await test('should handle invalid JSON gracefully during load', async () => {
      const tempDir = tmpdir();
      const tempTodoFile = join(tempDir, `test-todo-data-${Date.now()}-${Math.random()}.json`);
      
      // Write invalid JSON to the file
      writeFileSync(tempTodoFile, 'invalid json content');
      
      try {
        // Create a new manager - should handle the error gracefully
        const newTodoManager = new TodoManager(tempDir);
        newTodoManager.todoFile = tempTodoFile;
        newTodoManager.loadTodos();
        
        // Should initialize with defaults
        assert(Array.isArray(newTodoManager.todos));
        assert(Array.isArray(newTodoManager.categories));
        assert.strictEqual(newTodoManager.categories[0], 'no category');
      } finally {
        // Cleanup
        if (existsSync(tempTodoFile)) {
          try {
            unlinkSync(tempTodoFile);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }
    });

    await test('should handle non-existent todo IDs gracefully', async () => {
      await withFreshTodoManager(async (todoManager) => {
        const result = todoManager.markComplete(999999);
        assert.strictEqual(result, null);
        
        const result2 = todoManager.removeTodo(999999);
        assert.strictEqual(result2, null);
      });
    });

    await test('should normalize category names properly', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add a category with extra spaces
        const result = todoManager.addCategory('  Work  ');
        assert.strictEqual(result, true);
        
        // Should be able to find it by trimmed version
        const categories = todoManager.listCategories();
        assert(categories.some(cat => cat.trim() === 'Work')); // The category should be stored as trimmed
        
        // Add a todo with the same category (different spacing/casing)
        todoManager.addCategory('work'); // This should be detected as duplicate
        const categoriesAfter = todoManager.listCategories();
        const workMatches = categoriesAfter.filter(cat => 
          cat.toLowerCase() === 'work'
        );
        // Should still only have one work category despite different casing/spaces
        assert.strictEqual(workMatches.length, 1);
      });
    });
  });

  await describe('Backward Compatibility', async () => {
    await test('should handle old format (array of todos only) when loading', async () => {
      const tempDir = tmpdir();
      const tempTodoFile = join(tempDir, `test-todo-data-${Date.now()}-${Math.random()}.json`);
      
      try {
        // Create old format data (just an array of todos)
        const oldFormatData = [
          {
            id: 1,
            text: 'Old task',
            completed: false,
            createdAt: '2023-01-01T00:00:00.000Z',
            priority: 'medium',
            dueDate: null
          }
        ];
        writeFileSync(tempTodoFile, JSON.stringify(oldFormatData));
        
        // Load with new manager
        const newTodoManager = new TodoManager(tempDir);
        newTodoManager.todoFile = tempTodoFile;
        newTodoManager.loadTodos();
        
        // Should have converted to new format
        assert.strictEqual(newTodoManager.todos.length, 1);
        assert.strictEqual(newTodoManager.todos[0].text, 'Old task');
        assert.strictEqual(newTodoManager.todos[0].id, 1);
        assert.strictEqual(newTodoManager.categories.length, 1);
        assert.strictEqual(newTodoManager.categories[0], 'no category');
        
        // Verify it saves in new format
        newTodoManager.saveTodos();
        const savedData = JSON.parse(readFileSync(tempTodoFile, 'utf8'));
        assert.ok(savedData.hasOwnProperty('todos'));
        assert.ok(savedData.hasOwnProperty('categories'));
        assert(Array.isArray(savedData.todos));
        assert(Array.isArray(savedData.categories));
      } finally {
        // Cleanup
        if (existsSync(tempTodoFile)) {
          try {
            unlinkSync(tempTodoFile);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }
    });

    await test('should handle missing properties in old format gracefully', async () => {
      const tempDir = tmpdir();
      const tempTodoFile = join(tempDir, `test-todo-data-${Date.now()}-${Math.random()}.json`);
      
      try {
        // Create old format data with minimal properties
        const oldFormatData = [
          {
            id: 1,
            text: 'Minimal task',
            completed: false
            // Missing: createdAt, priority, dueDate
          }
        ];
        writeFileSync(tempTodoFile, JSON.stringify(oldFormatData));
        
        // Load with new manager
        const newTodoManager = new TodoManager(tempDir);
        newTodoManager.todoFile = tempTodoFile;
        newTodoManager.loadTodos();
        
        const todos = newTodoManager.listTodos();
        assert.strictEqual(todos.length, 1);
        const todo = todos[0];
        assert.strictEqual(todo.text, 'Minimal task');
        assert.strictEqual(todo.completed, false);
        // Properties that weren't in old format should have reasonable defaults
        assert.ok(todo.category === 'no category' || todo.category === undefined);
      } finally {
        // Cleanup
        if (existsSync(tempTodoFile)) {
          try {
            unlinkSync(tempTodoFile);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }
    });

    await test('should maintain backward compatibility when adding categories to old data', async () => {
      const tempDir = tmpdir();
      const tempTodoFile = join(tempDir, `test-todo-data-${Date.now()}-${Math.random()}.json`);
      
      try {
        // Start with old format
        const oldFormatData = [
          {
            id: 1,
            text: 'Old task',
            completed: false,
            createdAt: '2023-01-01T00:00:00.000Z',
            priority: 'medium'
          }
        ];
        writeFileSync(tempTodoFile, JSON.stringify(oldFormatData));
        
        // Load and interact with the data
        const newTodoManager = new TodoManager(tempDir);
        newTodoManager.todoFile = tempTodoFile;
        newTodoManager.loadTodos();
        
        // Should work normally now
        const categories = newTodoManager.listCategories();
        assert.strictEqual(categories.length, 1);
        assert.strictEqual(categories[0], 'no category');
        
        // Add a new category
        newTodoManager.addCategory('new-cat');
        const updatedCategories = newTodoManager.listCategories();
        assert(updatedCategories.includes('new-cat'));
        
        // Add a todo with category
        const newTodo = newTodoManager.addTodo('New task', 'high', null, 'new-cat');
        assert.strictEqual(newTodo.category, 'new-cat');
      } finally {
        // Cleanup
        if (existsSync(tempTodoFile)) {
          try {
            unlinkSync(tempTodoFile);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }
    });
  });

  await describe('Statistics', async () => {
    await test('should provide accurate statistics including by category', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add categories
        todoManager.addCategory('work');
        todoManager.addCategory('personal');
        
        // Add various todos
        todoManager.addTodo('Work task 1', 'high', null, 'work');
        todoManager.addTodo('Work task 2', 'medium', null, 'work');
        todoManager.addTodo('Personal task', 'low', null, 'personal');
        todoManager.addTodo('No category task', 'medium', null, 'no category');
        
        // Complete one task
        const workTodo = todoManager.listTodos().find(t => t.category === 'work');
        todoManager.markComplete(workTodo.id);
        
        const stats = todoManager.getStats();
        
        assert.strictEqual(stats.total, 4);
        assert.strictEqual(stats.completed, 1);
        assert.strictEqual(stats.pending, 3);
        
        // Check category breakdown
        assert.ok(stats.categories);
        assert.strictEqual(stats.categories['work'], 2); // Both work tasks
        assert.strictEqual(stats.categories['personal'], 1);
        assert.strictEqual(stats.categories['no category'], 1);
        
        // Check priority breakdown
        assert.ok(stats.priorities);
        assert.strictEqual(stats.priorities.high, 1);
        assert.strictEqual(stats.priorities.medium, 2);
        assert.strictEqual(stats.priorities.low, 1);
      });
    });

    await test('should handle overdue todos in statistics', async () => {
      await withFreshTodoManager(async (todoManager) => {
        // Add a past due date
        todoManager.addTodo('Overdue task', 'medium', '2020-01-01'); // Past date
        todoManager.addTodo('Future task', 'medium', '2030-01-01'); // Future date
        todoManager.addTodo('No due task', 'medium', null);
        
        const stats = todoManager.getStats();
        assert.strictEqual(stats.overdue, 1);
      });
    });
  });

  console.log(`\n📊 Test Results: ${testsPassed} passed, ${testsFailed} failed`);
  
  if (testsFailed === 0) {
    console.log('🎉 All tests passed!');
  } else {
    console.log('💥 Some tests failed!');
    process.exit(1);
  }
}

// Run the tests if this file is executed directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  runTests().catch(err => {
    console.error('Test execution error:', err);
    process.exit(1);
  });
}