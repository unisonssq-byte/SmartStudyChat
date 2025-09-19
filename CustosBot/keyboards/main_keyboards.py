from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard with 'Add to chat' button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить в чат", url="https://t.me/custoschatbot?startgroup=true")]
    ])
    return keyboard

def get_menu_buttons_keyboard() -> ReplyKeyboardMarkup:
    """Regular keyboard with menu buttons"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Мои чаты")],
            [KeyboardButton(text="📋 Команды")]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard

def get_confirmation_keyboard(action: str, target_user_id: int) -> InlineKeyboardMarkup:
    """Confirmation keyboard for sensitive actions like promoting to owner"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}_{target_user_id}")]
    ])
    return keyboard

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard