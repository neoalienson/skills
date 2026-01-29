#!/usr/bin/env node

/**
 * Cover Letter Generator Connector
 * Provides an interface to the cover letter generation skill
 */

import { execSync } from 'child_process';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get the base directory of the clawd workspace
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const baseDir = resolve(__dirname, '..');

// Get command line arguments
const [, , command, ...args] = process.argv;

try {
  // Execute the main cover letter script with the provided arguments
  const cmd = `node "${baseDir}/cover-letter-generator/cover-letter.mjs" ${command} ${args.join(' ')}`;
  const result = execSync(cmd, { encoding: 'utf8' });
  
  console.log(result);
} catch (error) {
  console.error('Error executing cover letter generator:', error.message);
  process.exit(1);
}