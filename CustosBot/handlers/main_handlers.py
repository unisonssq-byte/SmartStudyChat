from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command, CommandStart
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyboards.main_keyboards import get_main_menu_keyboard, get_menu_buttons_keyboard
from data.database import Database
from utils.image_generator import image_gen
from config import BOT_DESCRIPTION

router = Router()
db = Database()

@router.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    user = message.from_user
    if not user:
        return
    
    # Add user to database
    await db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if it's a private chat
    if message.chat.type == 'private':
        # Generate main menu image if not exists
        image_path = "CustosBot/images/main_menu.png"
        if not os.path.exists(image_path):
            try:
                await image_gen.generate_main_menu_image()
            except Exception as e:
                print(f"Failed to generate main menu image: {e}")
        
        # Send main menu with image
        try:
            if os.path.exists(image_path):
                photo = FSInputFile(image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=BOT_DESCRIPTION,
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await message.answer(
                    BOT_DESCRIPTION,
                    reply_markup=get_main_menu_keyboard()
                )
        except Exception as e:
            await message.answer(
                BOT_DESCRIPTION,
                reply_markup=get_main_menu_keyboard()
            )
        
        # Send menu buttons
        await message.answer(
            "Выберите действие:",
            reply_markup=get_menu_buttons_keyboard()
        )
    else:
        # In group chat - add chat and user as member
        chat = message.chat
        await db.add_chat(chat.id, chat.title or "Unknown Chat", chat.type)
        await db.add_chat_member(user.id, chat.id)
        
        await message.answer(
            "👋 Привет! Я Custos - ваш чат-менеджер. Используйте команды для управления чатом!"
        )

@router.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command"""
    # Generate commands image if not exists
    image_path = "CustosBot/images/commands.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_commands_image()
        except Exception as e:
            print(f"Failed to generate commands image: {e}")
    
    help_text = """
📋 **Команды бота**

**Модерация (только в чатах):**
• `/upstaff [число] [пользователь]` - повысить ранг
• `/ban [пользователь] [причина]` - забанить
• `/warn [пользователь] [причина]` - выдать варн
• `/kick [пользователь] [причина]` - кикнуть
• `/staff` - список персонала

**Профиль:**
• `/me` или `кто я` - моя информация
• `/you [пользователь]` или `кто ты` - информация о пользователе
• `/nickname +имя` - установить никнейм
• `/description +описание` - установить описание

Полный список команд в нашей [статье](https://teletype.in/@unisonqq/custoscommands)
"""
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=help_text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(help_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text == "💬 Мои чаты")
async def my_chats_command(message: Message):
    """Handle 'My Chats' button"""
    user = message.from_user
    if not user:
        return
    
    # Only work in private chat
    if message.chat.type != 'private':
        return
    
    # Generate my chats image if not exists
    image_path = "CustosBot/images/my_chats.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_my_chats_image()
        except Exception as e:
            print(f"Failed to generate my chats image: {e}")
    
    # Get user's chats
    chats = await db.get_user_chats(user.id)
    
    if not chats:
        await message.answer("📭 Вы не состоите ни в одном чате с ботом.")
        return
    
    # Build chat list
    chat_text = "💬 **Мои чаты:**\n\n"
    for chat in chats:
        chat_id = chat['chat_id']
        title = chat['title']
        rank = chat['rank']
        
        # Create chat link (negative ID for groups)
        if chat_id < 0:
            chat_link = f"https://t.me/c/{str(chat_id)[4:]}/1"  # Remove -100 prefix
        else:
            chat_link = f"https://t.me/{chat_id}"
        
        chat_text += f"• [{title}]({chat_link}) - {rank}\n"
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=chat_text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(chat_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(chat_text, parse_mode="Markdown")

@router.message(F.text == "📋 Команды")
async def commands_button(message: Message):
    """Handle 'Commands' button"""
    await help_command(message)