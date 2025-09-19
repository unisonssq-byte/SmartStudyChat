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
        image_path = "images/main_menu.png"
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
    image_path = "images/commands.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_commands_image()
        except Exception as e:
            print(f"Failed to generate commands image: {e}")
    
    # Different help text for private chat vs group chat
    if message.chat.type == 'private':
        help_text = """
📋 **Команды бота**

**Модерация (только в чатах):**
• `/upstaff [число] [пользователь]` - повысить ранг
• `/ban [пользователь] [причина]` или `бан [пользователь] [причина]` - забанить
• `/warn [пользователь] [причина]` или `варн [пользователь] [причина]` - выдать варн
• `/kick [пользователь] [причина]` или `кик [пользователь] [причина]` - кикнуть
• `/staff` или `стафф`, `админы`, `стаф`, `кто админ` - список персонала
• `/stats` или `стата` - статистика активности чата

**Информация:**
• `/help` или `помощь` - эта справка

**Профиль:**
• `/me` или `кто я` - моя информация
• `/you [пользователь]` или `кто ты` - информация о пользователе
• `/nickname +имя` - установить никнейм
• `/description +описание` - установить описание

Полный список команд в нашей [статье](https://teletype.in/@unisonqq/custoscommands)
"""
    else:
        help_text = """
📋 Команды бота

Модерация (только в чатах):
• /upstaff [число] [пользователь] - повысить ранг
• /ban [пользователь] [причина] или бан [пользователь] [причина] - забанить
• /warn [пользователь] [причина] или варн [пользователь] [причина] - выдать варн
• /kick [пользователь] [причина] или кик [пользователь] [причина] - кикнуть
• /staff или стафф, админы, стаф, кто админ - список персонала
• /stats или стата - статистика активности чата

Информация:
• /help или помощь - эта справка

Профиль:
• /me или кто я - моя информация
• /you [пользователь] или кто ты - информация о пользователе
• /nickname +имя - установить никнейм
• /description +описание - установить описание

Полный список команд: https://teletype.in/@unisonqq/custoscommands
"""
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            if message.chat.type == 'private':
                from keyboards.main_keyboards import get_back_keyboard
                await message.answer_photo(
                    photo=photo,
                    caption=help_text,
                    parse_mode="Markdown",
                    reply_markup=get_back_keyboard()
                )
            else:
                await message.answer_photo(
                    photo=photo,
                    caption=help_text
                )
        else:
            if message.chat.type == 'private':
                from keyboards.main_keyboards import get_back_keyboard
                await message.answer(help_text, parse_mode="Markdown", reply_markup=get_back_keyboard())
            else:
                await message.answer(help_text)
    except Exception as e:
        if message.chat.type == 'private':
            from keyboards.main_keyboards import get_back_keyboard
            await message.answer(help_text, parse_mode="Markdown", reply_markup=get_back_keyboard())
        else:
            await message.answer(help_text)

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
    image_path = "images/my_chats.png"
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
        from keyboards.main_keyboards import get_back_keyboard
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=chat_text,
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
        else:
            await message.answer(chat_text, parse_mode="Markdown", reply_markup=get_back_keyboard())
    except Exception as e:
        from keyboards.main_keyboards import get_back_keyboard
        await message.answer(chat_text, parse_mode="Markdown", reply_markup=get_back_keyboard())

@router.message(F.text == "📋 Команды")
async def commands_button(message: Message):
    """Handle 'Commands' button"""
    await help_command(message)

@router.message(F.text.in_(["помощь"]))
async def help_text_command(message: Message):
    """Handle text alternatives for /help command"""
    await help_command(message)

@router.message(F.new_chat_members)
async def new_chat_members(message: Message):
    """Handle when bot is added to a chat"""
    if not message.new_chat_members:
        return
    
    # Check if bot was added
    bot_info = await message.bot.get_me()
    for member in message.new_chat_members:
        if member.id == bot_info.id:
            # Bot was added to chat
            await message.answer(
                "🤖 **Добро пожаловать!**\n\n"
                "Я Custos - ваш помощник по управлению чатом!\n\n"
                "⚠️ **Важно:** Для полноценной работы мне необходимы права администратора чата.\n"
                "Пожалуйста, дайте мне права администратора для использования всех функций модерации.\n\n"
                "Используйте команду /help для просмотра доступных команд.",
                parse_mode="Markdown"
            )
            
            # Add chat to database
            chat = message.chat
            await db.add_chat(chat.id, chat.title or "Unknown Chat", chat.type)
            break

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    """Handle 'Back' button press"""
    user = callback.from_user
    if not user:
        return
    
    # Generate main menu image if not exists
    image_path = "images/main_menu.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_main_menu_image()
        except Exception as e:
            print(f"Failed to generate main menu image: {e}")
    
    # Send new main menu message (simpler and more reliable)
    try:
        from config import BOT_DESCRIPTION
        from keyboards.main_keyboards import get_main_menu_keyboard, get_menu_buttons_keyboard
        
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=BOT_DESCRIPTION,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await callback.message.answer(
                BOT_DESCRIPTION,
                reply_markup=get_main_menu_keyboard()
            )
            
        # Send menu buttons
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_menu_buttons_keyboard()
        )
        
        # Try to delete the previous message
        try:
            await callback.message.delete()
        except:
            pass  # Ignore if can't delete
            
    except Exception as e:
        print(f"Error in back_to_menu_handler: {e}")
    
    await callback.answer()

@router.message(F.content_type.in_(["text"]))
async def track_messages(message: Message):
    """Track messages for statistics - this handler should be last"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        return
    
    # Add user and update message count
    await db.add_user(user.id, user.username, user.first_name, user.last_name)
    await db.add_chat_member(user.id, chat.id)
    await db.increment_message_count(user.id, chat.id)