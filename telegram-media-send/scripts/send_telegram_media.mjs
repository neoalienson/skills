#!/usr/bin/env node

/**
 * Script to send media (images/audio) to Telegram using the Telegram Bot API
 */

import { existsSync, readFileSync } from 'fs';
import { execSync } from 'child_process';
import { join, extname } from 'path';

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

// Function to determine the appropriate Telegram API method based on file type
function getTelegramMethod(fileExtension) {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
  const audioExtensions = ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a'];
  
  if (imageExtensions.includes(fileExtension.toLowerCase())) {
    return 'sendPhoto';
  } else if (audioExtensions.includes(fileExtension.toLowerCase())) {
    return 'sendAudio';
  } else {
    // For other file types, use sendDocument
    return 'sendDocument';
  }
}

// Function to send media to Telegram
function sendMedia(chatId, mediaPath, caption = '', fileName = '') {
  // Get the bot token
  const botToken = getBotToken();
  
  if (!botToken) {
    console.error('Error: Could not find Telegram bot token in configuration');
    return false;
  }

  // Validate media file exists
  if (!existsSync(mediaPath)) {
    console.error(`Error: Media file does not exist: ${mediaPath}`);
    return false;
  }

  try {
    // Determine the file extension and appropriate API method
    const fileExt = extname(mediaPath).toLowerCase();
    const method = getTelegramMethod(fileExt);

    // Construct the curl command based on the media type
    let curlCommand;
    
    if (method === 'sendPhoto') {
      // For photos, use the photo parameter
      curlCommand = `curl -F "chat_id=${chatId}" -F "photo=@${mediaPath}" ${caption ? `-F "caption=${caption}"` : ''} "https://api.telegram.org/bot${botToken}/${method}"`;
    } else if (method === 'sendAudio') {
      // For audio, use the audio parameter
      curlCommand = `curl -F "chat_id=${chatId}" -F "audio=@${mediaPath}" ${caption ? `-F "caption=${caption}"` : ''} "https://api.telegram.org/bot${botToken}/${method}"`;
    } else {
      // For other documents, use the document parameter
      curlCommand = `curl -F "chat_id=${chatId}" -F "document=@${mediaPath}" ${fileName ? `-F "filename=${fileName}"` : ''} ${caption ? `-F "caption=${caption}"` : ''} "https://api.telegram.org/bot${botToken}/sendDocument"`;
    }
    
    console.log(`Sending ${fileExt} file to Telegram using ${method}...`);
    console.log(`Command: ${curlCommand}`);
    
    // Execute the curl command
    const result = execSync(curlCommand, { encoding: 'utf8' });
    const response = JSON.parse(result);
    
    if (response.ok) {
      console.log(`Media sent successfully! Message ID: ${response.result.message_id}`);
      return true;
    } else {
      console.error(`Error sending media: ${response.description}`);
      return false;
    }
  } catch (error) {
    console.error(`Error executing curl command: ${error.message}`);
    return false;
  }
}

// Main execution
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [, , chatId, mediaPath, ...args] = process.argv;
  const caption = args.join(' ');

  if (!chatId || !mediaPath) {
    console.log(`
Telegram Media Sender

Usage:
  send_telegram_media <chat_id> <media_path> [caption]

Examples:
  send_telegram_media 123456789 /path/to/image.jpg
  send_telegram_media 123456789 /path/to/audio.mp3 "My audio message"
  send_telegram_media 123456789 /path/to/document.pdf "Check out this document"
    `);
    process.exit(1);
  }

  const success = sendMedia(chatId, mediaPath, caption);
  process.exit(success ? 0 : 1);
}

export { sendMedia, getBotToken, getTelegramMethod };