# Custos Telegram Bot | Чат-менеджер

## Overview
This is a Python Telegram bot project called "Custos | Чат-менеджер" - a simplified chat management bot built with aiogram. The bot provides moderation features, user ranking system, and various administrative commands for Telegram group chats.

## Project Structure
```
CustosBot/
├── main.py                 # Main bot entry point
├── config.py               # Bot configuration and settings
├── requirements.txt        # Python dependencies
├── INSTALLATION.md        # Server installation guide
├── handlers/               # Command handlers
│   ├── __init__.py
│   ├── main_handlers.py
│   ├── moderation_handlers.py
│   └── user_handlers.py
├── keyboards/              # Bot keyboards and buttons
│   └── main_keyboards.py
├── data/                   # Database and data management
│   ├── database.py         # Database class and operations
│   └── custos.db          # SQLite database file
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── image_generator.py
└── images/                 # Bot UI images
    ├── bot_avatar.png
    ├── main_menu.png
    ├── commands.png
    ├── my_chats.png
    └── user_profile.png
```

## Current State
- ✅ Fresh GitHub import completed
- ✅ Security vulnerability in INSTALLATION.md resolved (removed hardcoded credentials)  
- ✅ Python environment and dependencies installed successfully
- ✅ Environment variable validation implemented with clear error messages
- ✅ Bot workflow configured and ready to run
- ⏳ **Ready for user to provide credentials**: The bot is fully set up and will start once environment variables are configured

## Dependencies
The bot requires the following Python packages:
- aiogram==3.22.0 (Telegram Bot API library)
- aiosqlite==0.21.0 (Async SQLite database)
- Pillow==11.3.0 (Image processing)
- matplotlib==3.10.6 (Graph generation)
- requests==2.32.5 (HTTP requests)
- aiofiles==24.1.0 (Async file operations)
- openai==1.54.4 (OpenAI API for image generation)

## Environment Variables Required
- BOT_TOKEN: Telegram bot token
- API_ID: Telegram API ID
- API_HASH: Telegram API hash
- OPENAI_API_KEY: OpenAI API key (optional, for image generation)

## Architecture
- **Backend only**: This is a console application that connects to Telegram API
- **Database**: Uses SQLite for storing user data, ranks, warnings, and chat information
- **No frontend**: The bot interface is entirely through Telegram
- **Async**: Built on asyncio and aiogram for handling multiple users simultaneously

## User Preferences
- Security-focused: Uses environment variables for sensitive credentials
- Following existing project structure and conventions
- Maintaining Russian language support in bot messages