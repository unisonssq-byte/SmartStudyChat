# Bot configuration
import os

BOT_TOKEN = '8356598661:AAEkViCdVcJQFi-FKMEuP1oVtWU0oROKANM'
API_ID = 25534167
API_HASH = 'a03ad3366f412b5e881b5f9ffd551f75'

# Validate required environment variables
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is required!")
    print("Please set it using: export BOT_TOKEN='your-bot-token-here'")
if API_ID == 0:
    print("WARNING: API_ID environment variable is not set or invalid!")
    print("Please set it using: export API_ID='your-api-id-here'")
if not API_HASH:
    print("WARNING: API_HASH environment variable is not set!")
    print("Please set it using: export API_HASH='your-api-hash-here'")

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