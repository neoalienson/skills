import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

class TodoManager {
  constructor(workspaceDir = '/home/neo/clawd') {
    this.workspaceDir = workspaceDir;
    // Store the todo data file in the skill's own directory for better organization
    this.todoFile = join(workspaceDir, 'skills', 'todo-list', 'todo-data.json');
    this.loadTodos();
  }

  loadTodos() {
    if (existsSync(this.todoFile)) {
      try {
        const data = readFileSync(this.todoFile, 'utf8');
        const parsedData = JSON.parse(data);
        
        // Handle both old format (just array of todos) and new format (with categories)
        if (Array.isArray(parsedData)) {
          // Old format: just an array of todos
          this.todos = parsedData;
          this.categories = ['no category']; // Initialize with default category
        } else {
          // New format: object with todos and categories
          this.todos = parsedData.todos || [];
          this.categories = parsedData.categories || ['no category'];
        }
      } catch (error) {
        console.error('Error loading todos:', error.message);
        this.todos = [];
        this.categories = ['no category'];
      }
    } else {
      this.todos = [];
      this.categories = ['no category'];
    }
  }

  saveTodos() {
    try {
      // Save in new format with both todos and categories
      const dataToSave = {
        todos: this.todos,
        categories: this.categories
      };
      writeFileSync(this.todoFile, JSON.stringify(dataToSave, null, 2));
    } catch (error) {
      console.error('Error saving todos:', error.message);
      throw error;
    }
  }

  // Category management methods
  addCategory(categoryName) {
    if (!categoryName) {
      throw new Error('Category name cannot be empty');
    }
    
    // Normalize category name (trim and lowercase for comparison)
    const normalizedCategory = categoryName.trim();
    
    // Check if category already exists (case insensitive)
    if (this.categories.some(cat => cat.toLowerCase() === normalizedCategory.toLowerCase())) {
      return false; // Category already exists
    }
    
    this.categories.push(normalizedCategory);
    this.saveTodos();
    return true;
  }

  removeCategory(categoryName) {
    if (!categoryName) {
      throw new Error('Category name cannot be empty');
    }
    
    const normalizedCategory = categoryName.trim();
    const initialLength = this.categories.length;
    
    // Remove the category
    this.categories = this.categories.filter(cat => 
      cat.toLowerCase() !== normalizedCategory.toLowerCase()
    );
    
    // Update any todos that had this category to 'no category'
    if (initialLength !== this.categories.length) {
      this.todos = this.todos.map(todo => {
        if (todo.category && 
            todo.category.toLowerCase() === normalizedCategory.toLowerCase()) {
          todo.category = 'no category';
        }
        return todo;
      });
      this.saveTodos();
      return true;
    }
    
    return false; // Category not found
  }

  listCategories() {
    return [...this.categories]; // Return a copy to prevent external modification
  }

  // Modified addTodo method to accept category parameter
  addTodo(item, priority = 'medium', dueDate = null, category = 'no category') {
    // Validate or create category if needed
    if (category && !this.categories.includes(category)) {
      // If the category doesn't exist, add it
      this.addCategory(category);
    }
    
    const newTodo = {
      id: Date.now(),
      text: item,
      completed: false,
      createdAt: new Date().toISOString(),
      priority: priority,
      dueDate: dueDate, // Store the due date if provided
      category: category // Assign category to the todo
    };
    
    this.todos.push(newTodo);
    this.saveTodos();
    return newTodo;
  }

  listTodos(filter = 'all', category = null) {
    let filteredTodos = this.todos;
    
    // Apply category filter if specified
    if (category) {
      filteredTodos = filteredTodos.filter(todo => 
        (todo.category && todo.category.toLowerCase() === category.toLowerCase()) || 
        (category.toLowerCase() === 'no category' && (!todo.category || todo.category === 'no category'))
      );
    }
    
    // Apply completion status filter
    if (filter === 'pending') {
      filteredTodos = filteredTodos.filter(todo => !todo.completed);
    } else if (filter === 'completed') {
      filteredTodos = filteredTodos.filter(todo => todo.completed);
    }
    
    return filteredTodos;
  }

  markComplete(id) {
    const todo = this.todos.find(t => t.id == id);
    if (todo) {
      todo.completed = true;
      todo.completedAt = new Date().toISOString();
      
      // Save todos before attempting to remove cron jobs
      this.saveTodos();
      
      // Try to remove any associated cron job for this todo
      this.removeAssociatedCronJob(id);
      
      return todo;
    }
    return null;
  }
  
  // Helper method to remove associated cron job when marking todo as complete
  removeAssociatedCronJob(todoId) {
    try {
      // Get list of cron jobs to find any related to this todo (using JSON output)
      const cronListOutput = execSync('clawdbot cron list --json', { encoding: 'utf8' });
      
      // Parse the JSON output
      const cronData = JSON.parse(cronListOutput);
      
      // Look for cron jobs that might be related to this todo
      if (Array.isArray(cronData.jobs)) {
        for (const job of cronData.jobs) {
          // Check if the job name contains the todo ID
          if (job.name && job.name.includes(todoId.toString())) {
            const jobId = job.id;
            try {
              execSync(`clawdbot cron rm ${jobId}`, { encoding: 'utf8' });
              console.log(`Removed associated cron job ${jobId} for todo ${todoId}`);
            } catch (err) {
              console.error(`Failed to remove cron job ${jobId}:`, err.message);
            }
          }
        }
      }
    } catch (error) {
      // If cron command is not available or fails, just log the error
      // but don't prevent the todo from being marked as complete
      console.error(`Error checking for associated cron jobs:`, error.message);
    }
  }

  removeTodo(id) {
    const index = this.todos.findIndex(t => t.id == id);
    if (index !== -1) {
      const removed = this.todos.splice(index, 1)[0];
      this.saveTodos();
      return removed;
    }
    return null;
  }

  clearCompleted() {
    this.todos = this.todos.filter(todo => !todo.completed);
    this.saveTodos();
    return this.todos.length;
  }

  getStats() {
    const total = this.todos.length;
    const completed = this.todos.filter(t => t.completed).length;
    const pending = total - completed;
    
    // Count overdue items
    const now = new Date();
    const overdue = this.todos.filter(todo => 
      !todo.completed && 
      todo.dueDate && 
      new Date(todo.dueDate) < now
    ).length;
    
    const priorities = this.todos.reduce((acc, todo) => {
      acc[todo.priority] = (acc[todo.priority] || 0) + 1;
      return acc;
    }, {});
    
    // Count todos by category
    const categories = this.todos.reduce((acc, todo) => {
      const category = todo.category || 'no category';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});
    
    return {
      total,
      completed,
      pending,
      overdue,
      priorities,
      categories
    };
  }

  // Method to update a todo's category
  updateTodoCategory(todoId, newCategory) {
    if (!newCategory) {
      throw new Error('Category cannot be empty');
    }
    
    // Validate or create category if needed
    if (!this.categories.includes(newCategory)) {
      this.addCategory(newCategory);
    }
    
    const todo = this.todos.find(t => t.id == todoId);
    if (todo) {
      todo.category = newCategory;
      this.saveTodos();
      return todo;
    }
    return null;
  }
}

// Export the class for use in other modules
export default TodoManager;

// Function to schedule a reminder via cron using Clawdbot's cron tool
function scheduleReminder(todoId, todoText, delayMinutes, todoManager) {
  try {
    // Create a message for the reminder
    const message = `⏰ Reminder: Please complete your task - ${todoText}`;
    
    // Use Clawdbot's cron functionality to schedule a message
    // We'll create a command that uses the message tool to send a reminder
    const reminderCommand = `message --action send --target "+85265432195" --message "${message}"`;
    
    // For now, we'll output instructions on how to manually set up the cron job
    // since direct cron scheduling from within this script would require additional integration
    console.log(`To schedule a reminder for this task, please run the following command separately:`);
    console.log(`clawdbot cron --action add --job '{"schedule": "*/${delayMinutes} * * * *", "command": "${reminderCommand}", "description": "Reminder for todo ${todoId}: ${todoText}", "channel": "whatsapp"}'`);
    console.log(`Or for a one-time reminder in ${delayMinutes} minutes, calculate the exact time and schedule accordingly.`);
  } catch (error) {
    console.error(`Error scheduling reminder: ${error.message}`);
  }
}

// If running directly, provide a command-line interface
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [, , command, ...args] = process.argv;
  const todoManager = new TodoManager();

  switch (command) {
    case 'add':
      const priority = args.includes('--high') ? 'high' : 
                     args.includes('--low') ? 'low' : 'medium';
      
      // Extract due date if specified with --due flag
      let dueDate = null;
      const dueIndex = args.indexOf('--due');
      if (dueIndex !== -1 && args[dueIndex + 1]) {
        dueDate = args[dueIndex + 1]; // Get the date following --due
        args.splice(dueIndex, 2); // Remove --due and the date from args
      }
      
      // Extract category if specified with --category flag
      let category = 'no category';
      const catIndex = args.indexOf('--category');
      if (catIndex !== -1 && args[catIndex + 1]) {
        category = args[catIndex + 1]; // Get the category following --category
        args.splice(catIndex, 2); // Remove --category and the category from args
      }
      
      const itemText = args.filter(arg => 
        !['--high', '--low'].includes(arg) && 
        arg !== '--no-category'
      ).join(' ');
      
      if (!itemText) {
        console.log('Usage: todo add [--high|--low] [--due YYYY-MM-DD] [--category NAME] <item text>');
        process.exit(1);
      }
      
      const newTodo = todoManager.addTodo(itemText, priority, dueDate, category);
      console.log(`Added: ${newTodo.text} (ID: ${newTodo.id}, Category: ${newTodo.category})${newTodo.dueDate ? `, Due: ${newTodo.dueDate}` : ''}`);
      break;

    case 'list':
    case 'show':
      // Check for category filter
      let filter = 'all';
      let categoryFilter = null;
      
      if (args.includes('--pending')) {
        filter = 'pending';
      } else if (args.includes('--completed')) {
        filter = 'completed';
      }
      
      const categoryIndex = args.indexOf('--category');
      if (categoryIndex !== -1 && args[categoryIndex + 1]) {
        categoryFilter = args[categoryIndex + 1];
      }
      
      const todos = todoManager.listTodos(filter, categoryFilter);
      
      if (todos.length === 0) {
        const filterText = filter === 'all' ? 'items' : filter;
        const categoryText = categoryFilter ? ` in category '${categoryFilter}'` : '';
        console.log(`No ${filterText} todos found${categoryText}.`);
      } else {
        let title = `${filter === 'all' ? 'All' : filter.charAt(0).toUpperCase() + filter.slice(1)} Todos`;
        if (categoryFilter) {
          title += ` in category '${categoryFilter}'`;
        }
        console.log(title + ':');
        
        todos.forEach(todo => {
          const status = todo.completed ? '[x]' : '[ ]';
          const priority = `[${todo.priority}]`;
          const dueInfo = todo.dueDate ? ` (Due: ${todo.dueDate})` : '';
          const categoryInfo = todo.category ? ` [${todo.category}]` : ' [no category]';
          console.log(`${status} #${todo.id} ${priority}${categoryInfo} ${todo.text}${dueInfo}`);
        });
      }
      break;

    case 'complete':
    case 'done':
      if (!args[0]) {
        console.log('Usage: todo complete <id>');
        process.exit(1);
      }
      
      const completed = todoManager.markComplete(args[0]);
      if (completed) {
        console.log(`Completed: ${completed.text}`);
      } else {
        console.log(`Todo with ID ${args[0]} not found.`);
      }
      break;

    case 'remove':
    case 'delete':
      if (!args[0]) {
        console.log('Usage: todo remove <id>');
        process.exit(1);
      }
      
      const removed = todoManager.removeTodo(args[0]);
      if (removed) {
        console.log(`Removed: ${removed.text}`);
      } else {
        console.log(`Todo with ID ${args[0]} not found.`);
      }
      break;

    case 'clear-completed':
      const remainingCount = todoManager.clearCompleted();
      console.log(`Cleared all completed todos. ${remainingCount} pending todos remain.`);
      break;

    case 'stats':
      const stats = todoManager.getStats();
      console.log('Todo Statistics:');
      console.log(`Total: ${stats.total}`);
      console.log(`Pending: ${stats.pending}`);
      console.log(`Completed: ${stats.completed}`);
      console.log(`Overdue: ${stats.overdue}`);
      console.log('By Priority:', stats.priorities);
      console.log('By Category:', stats.categories);
      break;

    case 'categories':
    case 'cats':
      const categories = todoManager.listCategories();
      if (categories.length === 0) {
        console.log('No categories defined.');
      } else {
        console.log('Categories:');
        categories.forEach((cat, index) => {
          console.log(`${index + 1}. ${cat}`);
        });
      }
      break;

    case 'add-category':
    case 'new-category':
      if (!args[0]) {
        console.log('Usage: todo add-category <category name>');
        process.exit(1);
      }
      
      const categoryName = args.join(' ');
      const added = todoManager.addCategory(categoryName);
      if (added) {
        console.log(`Added category: ${categoryName}`);
      } else {
        console.log(`Category '${categoryName}' already exists.`);
      }
      break;

    case 'remove-category':
    case 'del-category':
      if (!args[0]) {
        console.log('Usage: todo remove-category <category name>');
        process.exit(1);
      }
      
      const catToRemove = args.join(' ');
      const categoryRemoved = todoManager.removeCategory(catToRemove);
      if (categoryRemoved) {
        console.log(`Removed category: ${catToRemove}`);
      } else {
        console.log(`Category '${catToRemove}' not found.`);
      }
      break;

    case 'set-category':
    case 'assign-category':
      if (args.length < 2) {
        console.log('Usage: todo set-category <id> <category name>');
        process.exit(1);
      }
      
      const todoId = args[0];
      const newCategory = args.slice(1).join(' ');
      const updated = todoManager.updateTodoCategory(todoId, newCategory);
      if (updated) {
        console.log(`Updated category for todo ID ${todoId} to: ${newCategory}`);
      } else {
        console.log(`Todo with ID ${todoId} not found.`);
      }
      break;

    case 'remind':
    case 'schedule-reminder':
      if (args.length < 2) {
        console.log('Usage: todo remind <id> <minutes>');
        process.exit(1);
      }
      
      const remindTodoId = args[0];
      const minutes = parseInt(args[1], 10);
      
      if (isNaN(minutes) || minutes <= 0) {
        console.log('Please specify a valid number of minutes for the reminder.');
        process.exit(1);
      }
      
      const todo = todoManager.todos.find(t => t.id == remindTodoId);
      if (!todo) {
        console.log(`Todo with ID ${remindTodoId} not found.`);
        process.exit(1);
      }
      
      // Schedule the reminder using Clawdbot's cron functionality with WhatsApp channel
      const message = `⏰ Reminder: Please complete your task - ${todo.text}`;
      
      // Calculate the exact time for the cron expression
      const now = new Date();
      const futureTime = new Date(now.getTime() + minutes * 60000);
      const cronMinute = futureTime.getMinutes();
      const cronHour = futureTime.getHours();
      const cronDay = futureTime.getDate();
      const cronMonth = futureTime.getMonth() + 1; // Month is 0-indexed
      
      // Construct the cron command with the channel specification
      const cronCommand = `clawdbot cron add --name "todo-reminder-${todoId}" --cron "${cronMinute} ${cronHour} ${cronDay} ${cronMonth} *" --session isolated --message "${message}" --channel whatsapp --to "+85265432195" --deliver --delete-after-run`;
      
      console.log(`Scheduling reminder for todo ID ${todoId} (${todo.text}) in ${minutes} minute(s)...`);
      console.log(`Command to execute: ${cronCommand}`);
      
      break;

    default:
      console.log(`
Todo List Manager

Usage:
  todo add [--high|--low] [--due YYYY-MM-DD] [--category NAME] <item text>    Add a new todo
  todo list [all|pending|completed] [--category NAME]                        List todos with optional filters
  todo complete <id>                                                         Mark todo as complete
  todo remove <id>                                                           Remove a todo
  todo clear-completed                                                       Remove all completed todos
  todo stats                                                                 Show statistics
  todo categories                                                            List all categories
  todo add-category <name>                                                   Add a new category
  todo remove-category <name>                                                Remove a category
  todo set-category <id> <category>                                          Assign todo to category
  todo remind <id> <minutes>                                                 Schedule a reminder for a todo
      `);
  }
}