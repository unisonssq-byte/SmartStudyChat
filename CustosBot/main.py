import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import main_handlers, moderation_handlers, user_handlers
from data.database import Database
from config import BOT_TOKEN

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    # Check if BOT_TOKEN is available
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set! Please configure environment variables.")
        logger.error("Required environment variables:")
        logger.error("- BOT_TOKEN: Your Telegram bot token")
        logger.error("- API_ID: Your Telegram API ID")
        logger.error("- API_HASH: Your Telegram API hash")
        logger.error("- OPENAI_API_KEY: Your OpenAI API key (optional)")
        return
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Initialize database
    db = Database()
    await db.init_db()
    
    # Register routers
    dp.include_router(main_handlers.router)
    dp.include_router(moderation_handlers.router)
    dp.include_router(user_handlers.router)
    
    # Create images directory
    os.makedirs("CustosBot/images", exist_ok=True)
    
    logger.info("Custos Bot is starting...")
    
    # Start polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())