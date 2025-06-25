# Pyrogram Forward Bot

## Description
This is a Pyrogram-based Telegram bot that forwards media (videos, documents, photos, audio) from source channels to destination channels. Admins can manage channel pairs using simple commands.

## Features
- Forward media without quote using `copy_message`
- Add/remove source-destination chat pairs
- MongoDB for persistent storage
- Delay between forwarding to multiple destinations to avoid FloodWait
- Admin-only access
- Simple start and help commands

## Commands
- `/start` - Start message for admins
- `/help` - Shows help with all commands
- `/addchat <source> <destination>` - Add a source-destination channel pair
- `/delchat <source> <destination>` - Remove a source-destination channel pair

## Setup
1. Set the following environment variables:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `MONGO_URI`
   - `ADMINS` (comma-separated user IDs)
2. Run the bot with Python 3.10+.

## Example
```
/addchat -1002390143579 -1002255996946
/delchat -1002390143579 -1002255996946
```