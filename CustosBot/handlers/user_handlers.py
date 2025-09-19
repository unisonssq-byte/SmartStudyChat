from aiogram import F, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from data.database import Database
from utils.image_generator import image_gen
from config import RANK_NAMES
import os

router = Router()
db = Database()

async def get_target_user_for_profile(message: Message) -> tuple[int, str]:
    """Get target user for profile commands"""
    # Check if it's a reply
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.first_name or user.username or str(user.id)
    
    # Parse username from command
    text = message.text or ""
    parts = text.split()
    if len(parts) > 1:
        target = parts[1]
        if target.startswith('@'):
            # In real implementation, resolve username
            return 0, target
        elif target.isdigit():
            return int(target), target
    
    return 0, ""

@router.message(Command("me"))
@router.message(F.text.lower() == "кто я")
async def me_command(message: Message):
    """Handle /me and 'кто я' commands"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Generate user profile image if not exists
    image_path = "images/user_profile.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_user_profile_image()
        except Exception as e:
            print(f"Failed to generate user profile image: {e}")
    
    # Get user info
    user_info = await db.get_user_info(user.id)
    user_rank = await db.get_user_rank(user.id, chat.id)
    message_count = await db.get_user_message_count(user.id, chat.id)
    
    # Build profile text
    display_name = (user_info['nickname'] if user_info and user_info['nickname'] 
                   else user.first_name or user.username or str(user.id))
    
    profile_text = f"👤 **Описание чатера**\n\n"
    profile_text += f"**Имя:** {display_name}\n"
    profile_text += f"**Ссылка:** [Профиль](tg://user?id={user.id})\n"
    profile_text += f"**Сообщений:** {message_count}\n"
    profile_text += f"**Ранг:** {RANK_NAMES.get(user_rank, 'Неизвестен')}\n"
    
    if user_info and user_info['description']:
        profile_text += f"**Описание:** {user_info['description']}\n"
    else:
        profile_text += "**Описание:** не установлено\n"
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=profile_text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(profile_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(profile_text, parse_mode="Markdown")

@router.message(Command("you"))
@router.message(F.text.lower() == "кто ты")
async def you_command(message: Message):
    """Handle /you and 'кто ты' commands"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Get target user
    target_user_id, target_name = await get_target_user_for_profile(message)
    
    if not target_user_id:
        await message.answer("❌ Укажите пользователя: `/you @username` или ответьте на сообщение", parse_mode="Markdown")
        return
    
    # Generate user profile image if not exists
    image_path = "images/user_profile.png"
    if not os.path.exists(image_path):
        try:
            await image_gen.generate_user_profile_image()
        except Exception as e:
            print(f"Failed to generate user profile image: {e}")
    
    # Get user info
    user_info = await db.get_user_info(target_user_id)
    user_rank = await db.get_user_rank(target_user_id, chat.id)
    message_count = await db.get_user_message_count(target_user_id, chat.id)
    
    if not user_rank:
        await message.answer("❌ Пользователь не найден в чате!")
        return
    
    # Build profile text
    display_name = (user_info['nickname'] if user_info and user_info['nickname'] 
                   else target_name)
    
    profile_text = f"👤 **Описание чатера**\n\n"
    profile_text += f"**Имя:** {display_name}\n"
    profile_text += f"**Ссылка:** [Профиль](tg://user?id={target_user_id})\n"
    profile_text += f"**Сообщений:** {message_count}\n"
    profile_text += f"**Ранг:** {RANK_NAMES.get(user_rank, 'Неизвестен')}\n"
    
    if user_info and user_info['description']:
        profile_text += f"**Описание:** {user_info['description']}\n"
    else:
        profile_text += "**Описание:** не установлено\n"
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=profile_text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(profile_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(profile_text, parse_mode="Markdown")

@router.message(Command("nickname"))
@router.message(F.text.startswith("+ник "))
@router.message(F.text.startswith("+имя "))
async def nickname_command(message: Message):
    """Handle nickname setting commands"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    text = message.text or ""
    
    # Parse nickname from different command formats
    nickname = ""
    if text.startswith("/nickname "):
        nickname = text[10:].strip()
    elif text.startswith("+ник "):
        nickname = text[5:].strip()
    elif text.startswith("+имя "):
        nickname = text[5:].strip()
    
    if not nickname:
        await message.answer("❌ Укажите никнейм: `/nickname ВашНикнейм`", parse_mode="Markdown")
        return
    
    if len(nickname) > 50:
        await message.answer("❌ Никнейм не может быть длиннее 50 символов!")
        return
    
    # Set nickname
    await db.set_user_nickname(user.id, nickname)
    await message.answer(f"✅ Никнейм установлен: **{nickname}**", parse_mode="Markdown")

@router.message(Command("description"))
@router.message(F.text.startswith("+опис "))
@router.message(F.text.startswith("+описание "))
async def description_command(message: Message):
    """Handle description setting commands"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    text = message.text or ""
    
    # Parse description from different command formats
    description = ""
    if text.startswith("/description "):
        description = text[13:].strip()
    elif text.startswith("+опис "):
        description = text[6:].strip()
    elif text.startswith("+описание "):
        description = text[10:].strip()
    
    if not description:
        await message.answer("❌ Укажите описание: `/description Ваше описание`", parse_mode="Markdown")
        return
    
    if len(description) > 200:
        await message.answer("❌ Описание не может быть длиннее 200 символов!")
        return
    
    # Set description
    await db.set_user_description(user.id, description)
    await message.answer(f"✅ Описание установлено: **{description}**", parse_mode="Markdown")

# Message tracking is handled by main_handlers.py