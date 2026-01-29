---
name: bonus-picture
description: Capture a random video frame from nekochan videos and send to user via Telegram
user-invocable: true
---

# Bonus Picture Skill

A skill for capturing random frames from nekochan videos and sending them via Telegram.

## Description

This skill randomly selects a video from the assets/video/nekochan directory, captures a frame from it, saves it to a temporary folder with a random filename, and then sends it to the user via Telegram.

## Implementation

When the user requests a bonus picture:
1. Randomly select a video file from assets/video/nekochan
2. Capture a random frame from the selected video
3. Save the frame to /tmp/moltbot with a random filename
4. Use telegram-media-send skill to send the image to the user

## Usage

When the user says "send me a bonus picture" or similar:
- Find all video files in assets/video/nekochan
- Randomly select one
- Extract a frame using ffmpeg
- Save to /tmp/moltbot with random filename
- Send via telegram-media-send

The skill should handle file cleanup after successful sending.