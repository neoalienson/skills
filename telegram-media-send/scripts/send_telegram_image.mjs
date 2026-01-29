#!/usr/bin/env node

/**
 * Script to send images to Telegram using the Telegram Bot API
 */

import { existsSync, readFileSync } from 'fs';
import { execSync } from 'child_process';
import { join } from 'path';

// Function to read bot token from Clawdbot config
function getBotToken() {
  // Attempt to read from the clawdbot config file
  const configPath = process.env.HOME + '/.clawdbot/clawdbot.json';
  
  if (existsSync(configPath)) {
    try {
      const config = JSON.parse(readFileSync(configPath, 'utf8'));
      return config.channels?.telegram?.botToken;
    } catch (error) {
      console.error('Error reading config file:', error.message);
      return null;
    }
  }
  
  return null;
}

// Function to send image to Telegram
function sendImage(chatId, imagePath, caption = '') {
  // Get the bot token
  const botToken = getBotToken();
  
  if (!botToken) {
    console.error('Error: Could not find Telegram bot token in configuration');
    return false;
  }

  // Validate image file exists
  if (!existsSync(imagePath)) {
    console.error(`Error: Image file does not exist: ${imagePath}`);
    return false;
  }

  try {
    // Construct the curl command
    const curlCommand = `curl -F "chat_id=${chatId}" -F "photo=@${imagePath}" ${caption ? `-F "caption=${caption}"` : ''} "https://api.telegram.org/bot${botToken}/sendPhoto"`;
    
    console.log(`Sending image to Telegram...`);
    console.log(`Command: ${curlCommand}`);
    
    // Execute the curl command
    const result = execSync(curlCommand, { encoding: 'utf8' });
    const response = JSON.parse(result);
    
    if (response.ok) {
      console.log(`Image sent successfully! Message ID: ${response.result.message_id}`);
      return true;
    } else {
      console.error(`Error sending image: ${response.description}`);
      return false;
    }
  } catch (error) {
    console.error(`Error executing curl command: ${error.message}`);
    return false;
  }
}

// Main execution
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [, , chatId, imagePath, ...captionParts] = process.argv;
  const caption = captionParts.join(' ');

  if (!chatId || !imagePath) {
    console.log(`
Telegram Image Sender

Usage:
  send_telegram_image <chat_id> <image_path> [caption]

Examples:
  send_telegram_image 123456789 /path/to/image.jpg
  send_telegram_image 123456789 /path/to/image.jpg "My beautiful photo"
    `);
    process.exit(1);
  }

  const success = sendImage(chatId, imagePath, caption);
  process.exit(success ? 0 : 1);
}

export { sendImage, getBotToken };