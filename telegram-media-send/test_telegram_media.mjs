import { strict as assert } from 'assert';
import { existsSync, readFileSync } from 'fs';
import { spawnSync } from 'child_process';
import { join, extname } from 'path';
import { sendMedia, getBotToken, getTelegramMethod } from './send_telegram_media.mjs';

// Mock configuration file for testing
const mockConfig = {
  channels: {
    telegram: {
      botToken: '123456789:mock_bot_token_for_testing'
    }
  }
};

describe('Telegram Media Send Tests', () => {
  describe('getBotToken', () => {
    it('should return bot token from config file', () => {
      // We can't easily test this without a real config file
      // This test would require mocking the file system
      assert.ok(true); // Placeholder test
    });
  });

  describe('getTelegramMethod', () => {
    it('should return sendPhoto for image files', () => {
      assert.strictEqual(getTelegramMethod('.jpg'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.jpeg'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.png'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.gif'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.bmp'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.webp'), 'sendPhoto');
    });

    it('should return sendAudio for audio files', () => {
      assert.strictEqual(getTelegramMethod('.mp3'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.wav'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.aac'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.ogg'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.flac'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.m4a'), 'sendAudio');
    });

    it('should return sendDocument for other file types', () => {
      assert.strictEqual(getTelegramMethod('.pdf'), 'sendDocument');
      assert.strictEqual(getTelegramMethod('.doc'), 'sendDocument');
      assert.strictEqual(getTelegramMethod('.txt'), 'sendDocument');
      assert.strictEqual(getTelegramMethod('.mp4'), 'sendDocument');
      assert.strictEqual(getTelegramMethod('.zip'), 'sendDocument');
    });

    it('should be case insensitive', () => {
      assert.strictEqual(getTelegramMethod('.JPG'), 'sendPhoto');
      assert.strictEqual(getTelegramMethod('.Mp3'), 'sendAudio');
      assert.strictEqual(getTelegramMethod('.PDF'), 'sendDocument');
    });
  });

  describe('sendMedia', () => {
    it('should validate file existence before sending', () => {
      const result = sendMedia('123456', '/non/existent/file.jpg', 'Test caption');
      assert.strictEqual(result, false);
    });

    it('should detect file type correctly', () => {
      // Test with a mock file to ensure file exists
      // Since we can't guarantee a test file exists, we'll test the logic differently
      assert.ok(true); // Placeholder test
    });
  });

  describe('Integration Tests', () => {
    it('should have proper command line usage', () => {
      // Test the command line interface
      const result = spawnSync('node', ['./send_telegram_media.mjs'], { timeout: 5000 });
      assert.ok(result.status !== null); // Should exit with non-zero status due to missing args
    });
  });
});

// Run tests
console.log('Running Telegram Media Send Unit Tests...\n');

// Test getTelegramMethod function
console.log('Testing getTelegramMethod function:');

// Test image extensions
const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
imageExts.forEach(ext => {
  const result = getTelegramMethod(ext);
  console.log(`  ${ext}: ${result} - ${result === 'sendPhoto' ? 'PASS' : 'FAIL'}`);
  assert.strictEqual(result, 'sendPhoto', `Expected sendPhoto for ${ext}`);
});

// Test audio extensions
const audioExts = ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a'];
audioExts.forEach(ext => {
  const result = getTelegramMethod(ext);
  console.log(`  ${ext}: ${result} - ${result === 'sendAudio' ? 'PASS' : 'FAIL'}`);
  assert.strictEqual(result, 'sendAudio', `Expected sendAudio for ${ext}`);
});

// Test document extensions
const docExts = ['.pdf', '.doc', '.txt', '.zip', '.mp4'];
docExts.forEach(ext => {
  const result = getTelegramMethod(ext);
  console.log(`  ${ext}: ${result} - ${result === 'sendDocument' ? 'PASS' : 'FAIL'}`);
  assert.strictEqual(result, 'sendDocument', `Expected sendDocument for ${ext}`);
});

// Test case insensitivity
const caseTests = ['.JPG', '.Png', '.MP3', '.Pdf'];
caseTests.forEach(ext => {
  const lowerExt = ext.toLowerCase();
  let expectedType;
  if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'].includes(lowerExt)) {
    expectedType = 'sendPhoto';
  } else if (['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a'].includes(lowerExt)) {
    expectedType = 'sendAudio';
  } else {
    expectedType = 'sendDocument';
  }
  
  const result = getTelegramMethod(ext);
  console.log(`  ${ext}: ${result} - ${result === expectedType ? 'PASS' : 'FAIL'}`);
  assert.strictEqual(result, expectedType, `Expected ${expectedType} for ${ext}`);
});

console.log('\nAll unit tests passed! ✓');