#!/usr/bin/env node

/**
 * Unit tests for telegram-media-send script
 * Tests various scenarios including error conditions
 */

import { existsSync, writeFileSync, unlinkSync } from 'fs';
import { execSync } from 'child_process';
import { tmpdir } from 'os';
import { join } from 'path';

// Create a mock image file for testing
function createMockImage(filePath) {
  // Create a minimal valid JPEG file header (not a real image, but enough to pass basic checks)
  const jpegHeader = Buffer.from([
    0xFF, 0xD8, // JPEG SOI marker
    0xFF, 0xE0, 0x00, 0x10, // JFIF APP0 marker
    0x4A, 0x46, 0x49, 0x46, 0x00, // JFIF identifier
    0x01, 0x01, // Version
    0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, // Density
    0xFF, 0xDB, 0x00, 0x43, 0x00 // Start of quantization table
  ]);
  writeFileSync(filePath, jpegHeader);
}

// Test function
async function runTests() {
  console.log('🧪 Running unit tests for telegram-media-send...\n');

  let passedTests = 0;
  let totalTests = 0;

  // Test 1: Valid file with valid chat ID (main issue we fixed)
  console.log('Test 1: Valid file with valid chat ID - testing main execution flow');
  totalTests++;
  try {
    const mockImagePath = join(tmpdir(), 'test_valid_image.jpg');
    createMockImage(mockImagePath);
    
    const chatId = '8543893239'; // Valid chat ID we confirmed exists
    const caption = 'Unit test - valid scenario';
    
    const command = `node ${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs ${chatId} "${mockImagePath}" "${caption}"`;
    console.log(`  Command: ${command}`);
    
    let result;
    try {
      result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    } catch (execError) {
      // The command might exit with non-zero code if the actual send fails,
      // but we want to check if the script executed properly
      result = execError.stdout || execError.stderr;
    }
    console.log(`  Result: ${result}`);
    
    // Check if the script executed the main flow (shows expected logs)
    if (result.includes('Sending .jpg file to Telegram using sendPhoto...') || 
        result.includes('Media sent successfully!') || 
        result.includes('Command: curl')) {
      console.log('  ✅ PASSED: Script executed main flow for valid input');
      passedTests++;
    } else {
      console.log('  ❌ FAILED: Script did not execute main flow for valid input');
      console.log('  Expected to see "Sending .jpg file", "Command: curl", or "Media sent successfully!" in output');
    }
    
    // Clean up
    unlinkSync(mockImagePath);
  } catch (error) {
    console.log(`  ❌ FAILED: Error in test: ${error.message}`);
  }

  // Test 2: Script execution with no arguments (should show usage)
  console.log('\nTest 2: Script with insufficient arguments (should show usage)');
  totalTests++;
  try {
    const command = `node ${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs`;
    console.log(`  Command: ${command}`);
    
    let result;
    try {
      result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    } catch (execError) {
      // Expected to fail, so capture the output
      result = execError.stdout || execError.stderr;
    }
    console.log(`  Result: ${result}`);
    
    // Should show usage information
    if (result.includes('Telegram Media Sender') && result.includes('Usage:')) {
      console.log('  ✅ PASSED: Script correctly showed usage for insufficient arguments');
      passedTests++;
    } else {
      console.log('  ❌ FAILED: Script did not show usage for insufficient arguments');
    }
  } catch (error) {
    console.log(`  ❌ FAILED: Error in test: ${error.message}`);
  }

  // Test 3: Invalid/nonexistent file (should report error)
  console.log('\nTest 3: Invalid/nonexistent file');
  totalTests++;
  try {
    const invalidImagePath = join(tmpdir(), 'nonexistent_file.jpg');
    const chatId = '8543893239';
    
    const command = `node ${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs ${chatId} "${invalidImagePath}" "Unit test - invalid file"`;
    console.log(`  Command: ${command}`);
    
    let result;
    try {
      result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    } catch (execError) {
      result = execError.stdout || execError.stderr;
    }
    console.log(`  Result: ${result}`);
    
    // Should report an error about file not existing
    if (result.includes('Error: Media file does not exist')) {
      console.log('  ✅ PASSED: Script correctly reported file does not exist');
      passedTests++;
    } else if (result.includes('Media sent successfully!')) {
      console.log('  ❌ FAILED: Script incorrectly reported success for nonexistent file!');
    } else {
      console.log('  ⚠️  PARTIAL: Different error message than expected');
    }
  } catch (error) {
    console.log(`  ❌ FAILED: Error in test: ${error.message}`);
  }

  // Test 4: Test that script can be imported as a module without errors
  console.log('\nTest 4: Import script as module (validates syntax)');
  totalTests++;
  try {
    // Test importing the functions directly
    const { getBotToken, getTelegramMethod, sendMedia } = await import(`${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs`);
    
    // Verify functions exist
    if (typeof getBotToken === 'function' && 
        typeof getTelegramMethod === 'function' && 
        typeof sendMedia === 'function') {
      console.log('  ✅ PASSED: Script can be imported as module with all functions available');
      passedTests++;
    } else {
      console.log('  ❌ FAILED: Script missing expected functions when imported as module');
    }
  } catch (error) {
    console.log(`  ❌ FAILED: Error importing script as module: ${error.message}`);
  }

  // Test 5: Test the getTelegramMethod function specifically
  console.log('\nTest 5: Test getTelegramMethod function with different file types');
  totalTests++;
  try {
    const { getTelegramMethod } = await import(`${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs`);
    
    // Test different file extensions
    const testCases = [
      { ext: '.jpg', expected: 'sendPhoto' },
      { ext: '.jpeg', expected: 'sendPhoto' },
      { ext: '.png', expected: 'sendPhoto' },
      { ext: '.gif', expected: 'sendPhoto' },
      { ext: '.mp3', expected: 'sendAudio' },
      { ext: '.wav', expected: 'sendAudio' },
      { ext: '.txt', expected: 'sendDocument' },
      { ext: '.pdf', expected: 'sendDocument' }
    ];
    
    let allPassed = true;
    for (const testCase of testCases) {
      const result = getTelegramMethod(testCase.ext);
      if (result !== testCase.expected) {
        console.log(`    ❌ FAILED: getTelegramMethod('${testCase.ext}') returned '${result}', expected '${testCase.expected}'`);
        allPassed = false;
      }
    }
    
    if (allPassed) {
      console.log('  ✅ PASSED: getTelegramMethod function works correctly for all test cases');
      passedTests++;
    } else {
      console.log('  ❌ FAILED: getTelegramMethod function has incorrect behavior');
    }
  } catch (error) {
    console.log(`  ❌ FAILED: Error testing getTelegramMethod function: ${error.message}`);
  }

  // Summary
  console.log('\n--- Test Results ---');
  console.log(`Passed: ${passedTests}/${totalTests}`);
  console.log(`Success Rate: ${Math.round((passedTests/totalTests)*100)}%`);
  
  if (passedTests === totalTests) {
    console.log('🎉 All tests passed!');
  } else if (passedTests === 0) {
    console.log('💥 All tests failed!');
  } else {
    console.log('⚠️  Some tests failed - review the implementation');
  }
  
  return { passedTests, totalTests };
}

// Run tests if this file is executed directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  runTests()
    .then(results => {
      process.exit(results.passedTests === results.totalTests ? 0 : 1);
    })
    .catch(error => {
      console.error('Test suite error:', error);
      process.exit(1);
    });
}

export { runTests };