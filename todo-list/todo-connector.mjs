#!/usr/bin/env node

/**
 * Connector script for the Todo List skill
 * This script processes commands received from Clawdbot's /todo command
 */

import { execSync } from 'child_process';
import { join } from 'path';

// Get the command arguments passed from Clawdbot
const [, , ...args] = process.argv;

if (args.length === 0) {
  console.log(`
Todo List Manager

Usage:
  /todo add [--high|--low] [--due YYYY-MM-DD] [--category NAME] <item text>    Add a new todo
  /todo list [all|pending|completed] [--category NAME]                        List todos with optional filters
  /todo complete <id>                                                         Mark todo as complete
  /todo remove <id>                                                           Remove a todo
  /todo clear-completed                                                       Remove all completed todos
  /todo stats                                                                 Show statistics
  /todo categories                                                            List all categories
  /todo add-category <name>                                                   Add a new category
  /todo remove-category <name>                                                Remove a category
  /todo set-category <id> <category>                                          Assign todo to category
  `);
  process.exit(0);
}

try {
  // Execute the main todo script with the provided arguments
  const todoScriptPath = join(process.cwd(), 'skills/todo-list/todo.mjs');
  const command = `node "${todoScriptPath}" ${args.join(' ')}`;
  
  const result = execSync(command, { encoding: 'utf8' });
  console.log(result.trim());
} catch (error) {
  console.error(`Error executing todo command: ${error.message}`);
  process.exit(1);
}