---
name: telegram-media-send
description: Send media (images, audio, documents) to Telegram using the Telegram Bot API
user-invocable: true
---

# Telegram Media Send Skill

A skill for sending various types of media (images, audio, documents) to Telegram using the Telegram Bot API.

## Description

This skill allows users to send different types of media to Telegram by using the Telegram Bot API directly. It uses a dedicated script that automatically detects the file type and uses the appropriate API method (sendPhoto for images, sendAudio for audio files, sendDocument for other files).

## Configuration Requirements

This skill requires the Telegram bot token to be available in the Clawdbot configuration. The token is automatically read from `~/.clawdbot/clawdbot.json` in the `channels.telegram.botToken` field.

## Usage

When the user wants to send media to Telegram, execute the appropriate command using the exec tool:

- Use `exec command="node {baseDir}/scripts/send_telegram_media.mjs [CHAT_ID] [MEDIA_PATH] [CAPTION]"` to send media to Telegram

## Implementation

The skill uses the Telegram Bot API sendPhoto, sendAudio, or sendDocument methods to send media based on file type. It requires:
1. A valid Telegram bot token (obtained from @BotFather and configured in Clawdbot)
2. The recipient's chat ID
3. The path to the media file to be sent
4. An optional caption for the media

Supported file types:
- Images: .jpg, .jpeg, .png, .gif, .bmp, .webp
- Audio: .mp3, .wav, .aac, .ogg, .flac, .m4a
- Other: All other file types are sent as documents

## Examples

When the user says "Send image /path/to/photo.jpg to Telegram":
- Parse the request and execute: `exec command="node {baseDir}/scripts/send_telegram_media.mjs [CHAT_ID] /path/to/photo.jpg \"Image sent via Clawdbot\""`

When the user says "Send music /path/to/song.mp3 to Telegram with caption 'My favorite song'":
- Execute: `exec command="node {baseDir}/scripts/send_telegram_media.mjs [CHAT_ID] /home/neo/clawd/song.mp3 \"My favorite song\""`

When the user says "Send document /path/to/file.pdf to Telegram":
- Execute: `exec command="node {baseDir}/scripts/send_telegram_media.mjs [CHAT_ID] /home/neo/clawd/file.pdf \"Check out this document\""`

## Error Handling

The skill should handle potential errors such as:
- Invalid file paths
- Network connectivity issues
- Invalid bot tokens
- Incorrect chat IDs
- File size limitations (Telegram has limits for different file types)