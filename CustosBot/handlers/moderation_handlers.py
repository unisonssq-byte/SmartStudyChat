from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from data.database import Database
from config import RANKS, RANK_NAMES, COMMAND_PERMISSIONS, RATE_LIMITS
from keyboards.main_keyboards import get_confirmation_keyboard
import re
from datetime import datetime, timedelta

router = Router()
db = Database()

# Rate limit storage (in production, use Redis or database)
rate_limits = {}

async def get_user_telegram_rank(message: Message, user_id: int) -> str:
    """Get user's real rank from Telegram chat and sync with database"""
    try:
        chat_member = await message.bot.get_chat_member(message.chat.id, user_id)
        
        if chat_member.status == "creator":
            # Chat creator (owner)
            await db.add_chat_member(user_id, message.chat.id)
            await db.update_user_rank(user_id, message.chat.id, "owner")
            return "owner"
        elif chat_member.status == "administrator":
            # Chat administrator
            await db.add_chat_member(user_id, message.chat.id)
            await db.update_user_rank(user_id, message.chat.id, "administrator")
            return "administrator"
        elif chat_member.status in ["member", "restricted"]:
            # Regular member - check if they have a rank in database
            db_rank = await db.get_user_rank(user_id, message.chat.id)
            if db_rank and db_rank in ["moderator"]:
                # Keep moderator rank from database
                return db_rank
            else:
                # Regular participant
                await db.add_chat_member(user_id, message.chat.id)
                await db.update_user_rank(user_id, message.chat.id, "participant")
                return "participant"
        else:
            # Left or kicked
            return "participant"
            
    except Exception as e:
        print(f"Error getting chat member: {e}")
        # Fallback to database rank if Telegram API fails
        db_rank = await db.get_user_rank(user_id, message.chat.id)
        return db_rank or "participant"

async def check_rate_limit(user_id: int, command: str, rank: str) -> bool:
    """Check if user is rate limited for command"""
    if rank in ['administrator', 'owner']:
        return True  # No rate limits for high ranks
    
    limit_key = f"{user_id}_{command}"
    current_time = datetime.now()
    
    if limit_key in rate_limits:
        last_used = rate_limits[limit_key]
        if command == 'warn' and rank == 'moderator':
            if current_time - last_used < timedelta(seconds=RATE_LIMITS['warn_moderator']):
                return False
        elif command == 'kick' and rank == 'moderator':
            if current_time - last_used < timedelta(seconds=RATE_LIMITS['kick_moderator']):
                return False
    
    rate_limits[limit_key] = current_time
    return True

async def get_target_user(message: Message, text: str) -> tuple[int, str]:
    """Extract target user from command"""
    # Check if it's a reply
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.first_name or user.username or str(user.id)
    
    # Parse username or user ID from text
    words = text.split()[2:]  # Skip command and number if present
    if words:
        target = words[0]
        if target.startswith('@'):
            # Username - in real implementation, you'd need to resolve this
            return 0, target  # Placeholder
        elif target.isdigit():
            return int(target), target
    
    return 0, ""

async def get_moderation_target_user(message: Message, text: str = None) -> tuple[int, str]:
    """Extract target user for ban/warn/kick commands"""
    # Check if it's a reply
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.first_name or user.username or str(user.id)
    
    # Use provided text or message.text
    command_text = text or message.text or ""
    print(f"DEBUG: Parsing target from: {command_text}")
    
    # Parse username or user ID from text for ban/warn/kick (target is at position 1)
    words = command_text.split()[1:]  # Skip command only
    print(f"DEBUG: Words after command: {words}")
    if words:
        target = words[0]
        print(f"DEBUG: Target string: {target}")
        if target.startswith('@'):
            # Username - try to find user in chat members
            print(f"DEBUG: Looking for username {target}")
            # For now return 0 as we don't have username resolution
            return 0, target
        elif target.isdigit():
            print(f"DEBUG: Found user ID: {target}")
            return int(target), target
        else:
            print(f"DEBUG: Invalid target format: {target}")
    
    print("DEBUG: No target found")
    return 0, ""

async def can_moderate_target(message: Message, user_rank: str, target_user_id: int) -> bool:
    """Check if user can moderate target (prevent acting on equal/higher ranks)"""
    try:
        target_rank = await get_user_telegram_rank(message, target_user_id)
        
        # Rank hierarchy: owner (3) > administrator (2) > moderator (1) > participant (0)
        user_level = RANKS.get(user_rank, 0)
        target_level = RANKS.get(target_rank, 0)
        
        # Cannot moderate equal or higher ranks
        return user_level > target_level
    except Exception as e:
        # SECURITY: If we can't determine target rank, DENY moderation (fail-closed)
        print(f"Error determining target rank for user {target_user_id}: {e}")
        return False

@router.message(Command("upstaff"))
async def upstaff_command(message: Message):
    """Handle /upstaff command for rank promotion"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Get user rank from Telegram and sync with database
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['upstaff']:
        await message.answer("❌ Слишком низкий ранг для использования этой команды!")
        return
    
    # Parse command: /upstaff [число] [пользователь]
    text = message.text or ""
    parts = text.split()
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `/upstaff [число] [пользователь]`", parse_mode="Markdown")
        return
    
    try:
        rank_increase = int(parts[1])
    except ValueError:
        await message.answer("❌ Укажите корректное число для повышения ранга!")
        return
    
    # Get target user
    target_user_id, target_name = await get_target_user(message, text)
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Get target user current rank
    target_rank = await db.get_user_rank(target_user_id, chat.id)
    if not target_rank:
        await message.answer("❌ Пользователь не найден в чате!")
        return
    
    current_rank_level = RANKS[target_rank]
    new_rank_level = min(current_rank_level + rank_increase, 3)  # Max is owner (3)
    
    # Find new rank name
    new_rank = None
    for rank_name, level in RANKS.items():
        if level == new_rank_level:
            new_rank = rank_name
            break
    
    if not new_rank or new_rank == target_rank:
        await message.answer("❌ Невозможно повысить до указанного ранга!")
        return
    
    # Permission check - only owner can promote to owner
    if new_rank == 'owner' and user_rank != 'owner':
        await message.answer("❌ Только владелец может назначать нового владельца!")
        return
    
    # Administrator cannot promote owners
    if user_rank == 'administrator' and target_rank == 'owner':
        await message.answer("❌ Администратор не может повышать владельца!")
        return
    
    # Special confirmation for promoting to owner
    if new_rank == 'owner' and user_rank == 'owner':
        keyboard = get_confirmation_keyboard("promote_owner", target_user_id)
        await message.answer(
            f"⚠️ Вы собираетесь передать права владельца пользователю {target_name}. Подтвердите действие:",
            reply_markup=keyboard
        )
        return
    
    # Perform promotion
    await db.update_user_rank(target_user_id, chat.id, new_rank)
    
    await message.answer(
        f"✅ {target_name} повышен в ранге, теперь он {RANK_NAMES[new_rank]}!"
    )

@router.callback_query(F.data.startswith("confirm_promote_owner_"))
async def confirm_owner_promotion(callback: CallbackQuery):
    """Handle owner promotion confirmation"""
    user = callback.from_user
    chat = callback.message.chat if callback.message else None
    
    if not user or not chat:
        return
    
    # Check if user is owner
    user_rank = await get_user_telegram_rank(callback.message, user.id)
    if user_rank != 'owner':
        await callback.answer("🚫 Эта кнопка не для вас ^-^", show_alert=True)
        return
    
    # Extract target user ID
    if callback.data:
        target_user_id = int(callback.data.split("_")[-1])
    else:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    # Perform promotion
    await db.update_user_rank(target_user_id, chat.id, 'owner')
    await db.update_user_rank(user.id, chat.id, 'administrator')  # Demote current owner
    
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text("✅ Права владельца успешно переданы!")
    await callback.answer()

@router.message(Command("ban"))
async def ban_command(message: Message):
    """Handle /ban command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['ban']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    text = message.text or ""
    parts = text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `/ban [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя забанить пользователя с равным или высшим рангом!")
        return
    
    try:
        # Try to ban user from chat
        await message.chat.ban(target_user_id)
        await message.answer(f"🚫 {target_name} исключен из чата.\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Не удалось забанить пользователя: {str(e)}")

@router.message(Command("warn"))
async def warn_command(message: Message):
    """Handle /warn command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['warn']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    # Check rate limit
    if not await check_rate_limit(user.id, 'warn', user_rank):
        await message.answer("⏰ Вы можете использовать эту команду раз в час!")
        return
    
    text = message.text or ""
    parts = text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `/warn [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя выдать варн пользователю с равным или высшим рангом!")
        return
    
    # Add warning
    await db.add_warning(target_user_id, chat.id, reason, user.id)
    
    # Check warning count
    warning_count = await db.get_warning_count(target_user_id, chat.id)
    
    if warning_count >= 5:
        try:
            await message.chat.ban(target_user_id)
            await message.answer(f"🚫 {target_name} получил 5-й варн и автоматически забанен!")
        except Exception as e:
            await message.answer(f"⚠️ {target_name} получил {warning_count}-й варн! Причина: {reason}")
    else:
        await message.answer(f"⚠️ {target_name} получил варн ({warning_count}/5). Причина: {reason}")

@router.message(Command("kick"))
async def kick_command(message: Message):
    """Handle /kick command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['kick']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    # Check rate limit
    if not await check_rate_limit(user.id, 'kick', user_rank):
        await message.answer("⏰ Модератор может использовать эту команду раз в 15 минут!")
        return
    
    text = message.text or ""
    parts = text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `/kick [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя кикнуть пользователя с равным или высшим рангом!")
        return
    
    try:
        # Kick user (unban immediately after ban)
        await message.chat.ban(target_user_id)
        await message.chat.unban(target_user_id)
        await message.answer(f"👢 {target_name} исключен из чата временно.\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Не удалось кикнуть пользователя: {str(e)}")

@router.message(Command("staff"))
async def staff_command(message: Message):
    """Handle /staff command"""
    chat = message.chat
    
    if chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    print(f"DEBUG: Getting staff for chat {chat.id}")
    # Get staff list
    staff = await db.get_staff_list(chat.id)
    print(f"DEBUG: Staff result: {staff}")
    
    staff_text = "👥 **Персонал чата:**\n\n"
    
    # Owners
    if staff['owner']:
        staff_text += "👑 **Владельцы:**\n"
        for member in staff['owner']:
            name = member['nickname'] or member['first_name'] or member['username'] or str(member['user_id'])
            staff_text += f"• {name}\n"
        staff_text += "\n"
    
    # Administrators
    if staff['administrator']:
        staff_text += "⭐ **Администраторы:**\n"
        for member in staff['administrator']:
            name = member['nickname'] or member['first_name'] or member['username'] or str(member['user_id'])
            staff_text += f"• {name}\n"
        staff_text += "\n"
    
    # Moderators
    if staff['moderator']:
        staff_text += "🛡 **Модераторы:**\n"
        for member in staff['moderator']:
            name = member['nickname'] or member['first_name'] or member['username'] or str(member['user_id'])
            staff_text += f"• {name}\n"
    
    if not any(staff.values()):
        staff_text += "Персонал не назначен."
    
    print(f"DEBUG: Final staff text: {staff_text}")
    await message.answer(staff_text, parse_mode="Markdown")

@router.message(Command("stats"))
async def stats_command(message: Message):
    """Handle /stats command for chat statistics"""
    chat = message.chat
    
    if chat.type == 'private':
        await message.answer("❌ Команда доступна только в групповых чатах!")
        return
    
    # Get chat statistics from database
    results = await db.get_chat_stats(chat.id, 20)
    
    if not results:
        await message.answer("📊 **Статистика чата**\n\nСтатистика пока не собрана. Начните общаться в чате!")
        return
    
    stats_text = "📊 **Статистика активности чата**\n\n"
    stats_text += "🏆 **Самые активные участники:**\n\n"
    
    for i, row in enumerate(results, 1):
        user_id, nickname, first_name, username, message_count = row
        # Use nickname if available, otherwise first_name, then username, then user_id
        display_name = nickname or first_name or username or str(user_id)
        
        if i == 1:
            emoji = "🥇"
        elif i == 2:
            emoji = "🥈"
        elif i == 3:
            emoji = "🥉"
        else:
            emoji = f"{i}."
        
        stats_text += f"{emoji} {display_name} — {message_count} сообщений\n"
    
    await message.answer(stats_text, parse_mode="Markdown")

# Alternative text commands (without slash)
@router.message(F.text.in_(["стафф", "админы", "стаф", "кто админ"]))
async def staff_text_command(message: Message):
    """Handle text alternatives for /staff command"""
    if message.chat.type != 'private':
        await staff_command(message)

@router.message(F.text.in_(["стата"]))
async def stats_text_command(message: Message):
    """Handle text alternatives for /stats command"""
    if message.chat.type != 'private':
        await stats_command(message)

@router.message(F.text.regexp(r"^бан\s+.+"))
async def ban_text_command(message: Message):
    """Handle text alternatives for /ban command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['ban']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    text = message.text or ""
    # Convert: "бан пользователь причина" -> "/ban пользователь причина"
    command_text = "/ban " + text[4:]  # Replace "бан " with "/ban "
    parts = command_text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `бан [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, command_text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя забанить пользователя с равным или высшим рангом!")
        return
    
    try:
        # Try to ban user from chat
        await message.chat.ban(target_user_id)
        await message.answer(f"🚫 {target_name} исключен из чата.\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Не удалось забанить пользователя: {str(e)}")

@router.message(F.text.regexp(r"^кик\s+.+"))
async def kick_text_command(message: Message):
    """Handle text alternatives for /kick command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['kick']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    # Check rate limit
    if not await check_rate_limit(user.id, 'kick', user_rank):
        await message.answer("⏰ Модератор может использовать эту команду раз в 15 минут!")
        return
    
    text = message.text or ""
    command_text = "/kick " + text[4:]  # Replace "кик " with "/kick "
    parts = command_text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `кик [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, command_text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя кикнуть пользователя с равным или высшим рангом!")
        return
    
    try:
        # Kick user (unban immediately after ban)
        await message.chat.ban(target_user_id)
        await message.chat.unban(target_user_id)
        await message.answer(f"👢 {target_name} исключен из чата временно.\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Не удалось кикнуть пользователя: {str(e)}")

@router.message(F.text.regexp(r"^варн\s+.+"))
async def warn_text_command(message: Message):
    """Handle text alternatives for /warn command"""
    user = message.from_user
    chat = message.chat
    
    if not user or chat.type == 'private':
        return
    
    # Check permissions
    user_rank = await get_user_telegram_rank(message, user.id)
    if not user_rank or user_rank not in COMMAND_PERMISSIONS['warn']:
        await message.answer("❌ Недостаточно прав для использования этой команды!")
        return
    
    # Check rate limit
    if not await check_rate_limit(user.id, 'warn', user_rank):
        await message.answer("⏰ Вы можете использовать эту команду раз в час!")
        return
    
    text = message.text or ""
    command_text = "/warn " + text[5:]  # Replace "варн " with "/warn "
    parts = command_text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("❌ Использование: `варн [пользователь] [причина]`", parse_mode="Markdown")
        return
    
    target_user_id, target_name = await get_moderation_target_user(message, command_text)
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"
    
    if not target_user_id:
        await message.answer("❌ Не удалось найти указанного пользователя!")
        return
    
    # Check if user can moderate target
    if not await can_moderate_target(message, user_rank, target_user_id):
        await message.answer("❌ Нельзя выдать варн пользователю с равным или высшим рангом!")
        return
    
    # Add warning
    await db.add_warning(target_user_id, chat.id, reason, user.id)
    
    # Check warning count
    warning_count = await db.get_warning_count(target_user_id, chat.id)
    
    if warning_count >= 5:
        try:
            await message.chat.ban(target_user_id)
            await message.answer(f"🚫 {target_name} получил 5-й варн и автоматически забанен!")
        except Exception as e:
            await message.answer(f"⚠️ {target_name} получил {warning_count}-й варн! Причина: {reason}")
    else:
        await message.answer(f"⚠️ {target_name} получил варн ({warning_count}/5). Причина: {reason}")