# Bot configuration
import os

# Get credentials from environment variables (stored in Replit Secrets)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH')

# Validate required environment variables
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is required!")
    print("Please set it in Replit Secrets")
if API_ID == 0:
    print("WARNING: API_ID environment variable is not set or invalid!")
    print("Please set it in Replit Secrets")
if not API_HASH:
    print("WARNING: API_HASH environment variable is not set!")
    print("Please set it in Replit Secrets")


# Bot commands help text
BOT_DESCRIPTION = """
🤖 **Custos | Чат-менеджер** — ваш помощник для управления чатами

**Основные функции:**
• Система рангов (участник → модератор → администратор → владелец)
• Модерация чата (баны, варны, кики)
• Персональные профили пользователей
• Статистика активности чата

**Команды доступны только в групповых чатах!**
"""

# Rank system
RANKS = {
    'participant': 0,
    'moderator': 1,
    'administrator': 2,
    'owner': 3
}

RANK_NAMES = {
    'participant': 'Участник',
    'moderator': 'Модератор', 
    'administrator': 'Администратор',
    'owner': 'Владелец'
}

# Command permissions
COMMAND_PERMISSIONS = {
    'upstaff': ['administrator', 'owner'],
    'ban': ['administrator', 'owner'],
    'warn': ['moderator', 'administrator', 'owner'],
    'kick': ['moderator', 'administrator', 'owner']
}

# Rate limits (in seconds)
RATE_LIMITS = {
    'warn_moderator': 3600,  # 1 hour for moderators
    'kick_moderator': 900    # 15 minutes for moderators
}