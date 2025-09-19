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