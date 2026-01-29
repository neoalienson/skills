#!/usr/bin/env node

import { readdirSync, mkdirSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import { join } from 'path';
import { randomUUID } from 'crypto';

/**
 * Function to get random video file from directory
 */
function getRandomVideoFile(directory) {
  const files = readdirSync(directory).filter(file => 
    file.endsWith('.mp4') && file.startsWith('nekochan_')
  );
  
  if (files.length === 0) {
    throw new Error('No nekochan video files found in directory');
  }
  
  const randomIndex = Math.floor(Math.random() * files.length);
  return files[randomIndex];
}

/**
 * Function to capture a random frame from video
 */
function captureRandomFrame(videoPath, outputPath) {
  // Get video duration
  const durationResult = execSync(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${videoPath}"`, { encoding: 'utf8' });
  const duration = parseFloat(durationResult.trim());
  
  // Generate random time within video duration (excluding first and last 2 seconds to avoid black frames)
  const startTime = 2;
  const endTime = Math.max(startTime, duration - 2);
  const randomTime = Math.random() * (endTime - startTime) + startTime;
  
  // Format time as HH:MM:SS
  const hours = Math.floor(randomTime / 3600);
  const minutes = Math.floor((randomTime % 3600) / 60);
  const seconds = Math.floor(randomTime % 60);
  const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${(seconds + (randomTime % 1)).toFixed(3).padStart(6, '0')}`;
  
  // Capture frame at random time
  const command = `ffmpeg -ss ${formattedTime} -i "${videoPath}" -vframes 1 -q:v 2 "${outputPath}" -y`;
  execSync(command, { stdio: 'pipe' });
  
  return outputPath;
}

/**
 * Main function to generate and send bonus picture
 */
function generateAndSendBonusPicture(chatId) {
  try {
    // Ensure the temp directory exists
    const tempDir = '/tmp/moltbot';
    if (!existsSync(tempDir)) {
      mkdirSync(tempDir, { recursive: true });
    }
    
    // Select random video
    const videoDir = 'assets/video/nekochan';
    const randomVideo = getRandomVideoFile(videoDir);
    const videoPath = join(process.cwd(), videoDir, randomVideo);
    
    // Create random filename for the captured frame
    const randomFilename = `bonus_${randomUUID()}.jpg`;
    const outputPath = join(tempDir, randomFilename);
    
    console.log(`Selecting random video: ${randomVideo}`);
    console.log(`Capturing frame to: ${outputPath}`);
    
    // Capture random frame from video
    captureRandomFrame(videoPath, outputPath);
    
    if (!existsSync(outputPath)) {
      throw new Error('Failed to capture frame from video');
    }
    
    console.log(`Successfully captured frame: ${outputPath}`);
    
    // Execute the send command directly
    const sendCommand = `node ${process.cwd()}/skills/telegram-media-send/scripts/send_telegram_media.mjs ${chatId} "${outputPath}" "Bonus nekochan picture! From: ${randomVideo}"`;
    execSync(sendCommand, { stdio: 'inherit' });
    
    console.log('Bonus picture sent successfully!');
    
    // Clean up the temporary file after sending
    setTimeout(() => {
      try {
        execSync(`rm "${outputPath}"`);
        console.log(`Cleaned up temporary file: ${outputPath}`);
      } catch (cleanupError) {
        console.error(`Failed to clean up temporary file: ${cleanupError.message}`);
      }
    }, 5000); // Wait 5 seconds before cleaning up
    
    return { success: true, videoUsed: randomVideo, imagePath: outputPath };
    
  } catch (error) {
    console.error('Error in bonus picture generation:', error.message);
    throw error;
  }
}

// Main execution
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [, , chatId] = process.argv;

  if (!chatId) {
    console.log(`
Bonus Picture Generator

Usage:
  bonus_picture <chat_id>

Examples:
  bonus_picture 123456789
    `);
    process.exit(1);
  }

  try {
    const result = generateAndSendBonusPicture(chatId);
    console.log('Bonus picture generated and sent successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Failed to generate and send bonus picture:', error.message);
    process.exit(1);
  }
}

export { generateAndSendBonusPicture, getRandomVideoFile, captureRandomFrame };