"""Инлайн-клавиатуры."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.translator import LANGUAGES


def get_main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🌍 Начать перевод", callback_data="start_translate")],
        [
            InlineKeyboardButton(text="📋 Языки", callback_data="languages"),
            InlineKeyboardButton(text="🔄 Сменить язык", callback_data="change_target")
        ],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_target_language_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    lang_items = list(LANGUAGES.items())
    for i in range(0, len(lang_items), 2):
        row = []
        for code, name in lang_items[i:i+2]:
            row.append(InlineKeyboardButton(text=name, callback_data=f"target_{code}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_result_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Новый перевод", callback_data="start_translate"),
            InlineKeyboardButton(text="❓ Неверный язык", callback_data="wrong_language")
        ],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_source_language_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    lang_items = list(LANGUAGES.items())
    for i in range(0, len(lang_items), 2):
        row = []
        for code, name in lang_items[i:i+2]:
            row.append(InlineKeyboardButton(text=name, callback_data=f"manual_source_{code}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)