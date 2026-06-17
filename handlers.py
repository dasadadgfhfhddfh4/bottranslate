"""Обработчики команд."""
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from keyboards import (
    get_main_keyboard, get_target_language_keyboard,
    get_result_keyboard, get_source_language_keyboard
)
from translator import translate_text, LANGUAGES, get_languages_list_text

router = Router()
logger = logging.getLogger(__name__)

user_preferences: dict[int, dict] = {}


class TranslationStates(StatesGroup):
    choosing_target = State()
    waiting_for_text = State()
    correcting_language = State()


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.debug(f"safe_edit: {e}")
    except Exception as e:
        logger.error(f"Ошибка редактирования: {e}")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    saved_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
    saved_text = f"\n\n💾 Твой последний язык: {LANGUAGES.get(saved_lang)}" if saved_lang else ""

    welcome_text = (
        "👋 <b>Привет!</b> Я — <b>TranslatorBot</b> \n\n"
        " Умный переводчик с <b>автоопределением языка</b>\n\n"
        "✨ <b>Как работать:</b>\n"
        "1️⃣ Выбери <b>целевой язык</b>\n"
        "2️⃣ Отправь <b>текст</b>\n"
        "3️⃣ Получи перевод! 🎉\n\n"
        "💡 <i>Язык сохраняется — не нужно выбирать каждый раз!</i>"
        f"{saved_text}"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    saved_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
    saved_text = f"\n💾 Язык: <b>{LANGUAGES.get(saved_lang)}</b>" if saved_lang else ""
    await message.answer(f"🏠 <b>Главное меню</b>{saved_text}", reply_markup=get_main_keyboard())


@router.callback_query(F.data == "start_translate")
async def start_translation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    saved_lang = user_preferences.get(callback.from_user.id, {}).get("target_lang")

    if saved_lang and saved_lang in LANGUAGES:
        await state.update_data(target_lang=saved_lang)
        await state.set_state(TranslationStates.waiting_for_text)
        await safe_edit(
            callback,
            f"️ <b>Отправь текст для перевода</b>\n\n"
            f"🎯 Перевожу на: <b>{LANGUAGES[saved_lang]}</b>\n"
            f"🕵️ Язык оригинала определю автоматически!\n\n"
            f"💡 <i>Хочешь другой язык? Кнопка «Сменить язык»</i>"
        )
    else:
        await state.set_state(TranslationStates.choosing_target)
        await safe_edit(
            callback,
            "🎯 <b>Выбери целевой язык</b>\n\n"
            "На какой язык переводить?\n\n"
            "💡 <i>Выбор сохранится для следующих переводов</i>",
            get_target_language_keyboard()
        )


@router.callback_query(F.data == "change_target")
async def change_target_language(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    saved_lang = user_preferences.get(callback.from_user.id, {}).get("target_lang")
    current = LANGUAGES.get(saved_lang, "не выбран")
    await state.set_state(TranslationStates.choosing_target)
    await safe_edit(
        callback,
        f"🔄 <b>Сменить целевой язык</b>\n\n"
        f"Текущий: <b>{current}</b>\n\n"
        "Выбери новый:",
        get_target_language_keyboard()
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    saved_lang = user_preferences.get(callback.from_user.id, {}).get("target_lang")
    saved_text = f"\n\n💾 Текущий язык: <b>{LANGUAGES.get(saved_lang)}</b>" if saved_lang else ""

    await safe_edit(
        callback,
        f" <b>Главное меню</b>{saved_text}\n\n"
        f"Выбери действие 👇",
        get_main_keyboard()
    )


@router.callback_query(F.data == "languages")
async def show_languages(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit(
        callback,
        f"🌍 <b>Поддерживаемые языки</b>\n\n{get_languages_list_text()}\n\n"
        f"💡 <i>Язык оригинала определяется автоматически!</i>",
        get_main_keyboard()
    )


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery) -> None:
    await callback.answer()
    help_text = (
        "📖 <b>Как пользоваться</b>\n\n"
        "1️⃣ Нажми <b>«Начать перевод»</b>\n"
        "2️⃣ Выбери язык (1 раз — сохранится!)\n"
        "3️ Отправь текст\n"
        "4️⃣ Получи перевод! 🎉\n\n"
        "🔄 <b>Быстрые переводы:</b>\n"
        "После первого выбора языка — сразу отправляй текст!\n\n"
        "❓ <b>Неверный язык?</b>\n"
        "После перевода нажми «Неверный язык» — выбери вручную\n\n"
        " <b>Совет:</b> максимум 500 символов за раз"
    )
    await safe_edit(callback, help_text, get_main_keyboard())


@router.callback_query(TranslationStates.choosing_target, F.data.startswith("target_"))
async def process_target_language(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    target_lang = callback.data.replace("target_", "")
    if target_lang not in LANGUAGES:
        await callback.answer("❌ Неизвестный язык", show_alert=True)
        return

    user_id = callback.from_user.id
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    user_preferences[user_id]["target_lang"] = target_lang

    await state.update_data(target_lang=target_lang)
    await state.set_state(TranslationStates.waiting_for_text)
    await safe_edit(
        callback,
        f"✍️ <b>Отправь текст для перевода</b>\n\n"
        f" Перевожу на: <b>{LANGUAGES[target_lang]}</b>\n"
        f"🕵️ Язык оригинала определю сам!\n\n"
        f"✅ <i>Язык сохранён — в следующий раз сразу к вводу!</i>"
    )


@router.message(TranslationStates.waiting_for_text, F.text)
async def process_translation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = message.text.strip()
    target_lang = data.get("target_lang")
    
    if not target_lang:
        target_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
        if not target_lang:
            await message.answer("⚠️ <b>Сначала выбери язык</b> 🎯", reply_markup=get_main_keyboard())
            await state.clear()
            return

    if len(text) > 500:
        await message.answer(f"⚠️ <b>Текст слишком длинный</b>\n\nМаксимум <b>500 символов</b> за раз.\nУ тебя: <b>{len(text)}</b> символов")
        return

    if len(text) < 2:
        await message.answer("⚠️ <b>Слишком короткий текст</b> (минимум 2 символа)")
        return

    await state.update_data(last_text=text, target_lang=target_lang)

    try:
        translated, status, detected_lang, _ = await translate_text(text, target_lang)
        
        if status == "success":
            source_name = LANGUAGES.get(detected_lang, detected_lang or "авто")
            target_name = LANGUAGES[target_lang]
            
            result_text = (
                f"✅ <b>Готово!</b>\n\n"
                f"🔄 <b>{source_name}</b> ➜ <b>{target_name}</b>\n\n"
                f"<code>{translated}</code>"
            )
            await message.answer(result_text, reply_markup=get_result_keyboard())
        else:
            await message.answer(f"❌ <b>Ошибка перевода</b>\n\n{translated}\n\nПопробуй ещё раз 🔄", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await message.answer("❌ Произошла ошибка. Попробуй ещё раз.", reply_markup=get_main_keyboard())

    await state.set_state(None)


@router.callback_query(F.data == "wrong_language")
async def wrong_language_clicked(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    last_text = data.get("last_text")
    
    if not last_text:
        await callback.answer("⚠️ Начни перевод заново — я забыл текст", show_alert=True)
        await state.clear()
        await callback.message.answer("🔄 <b>Начни новый перевод</b>", reply_markup=get_main_keyboard())
        return

    await state.update_data(pending_text=last_text, pending_target=data.get("target_lang"))
    await state.set_state(TranslationStates.correcting_language)
    await safe_edit(
        callback,
        "🔧 <b>Выбери язык оригинала вручную</b>\n\nНа каком языке написан текст?",
        get_source_language_keyboard()
    )


@router.callback_query(TranslationStates.correcting_language, F.data.startswith("manual_source_"))
async def process_manual_source(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    source_lang = callback.data.replace("manual_source_", "")
    data = await state.get_data()
    text = data.get("pending_text")
    target_lang = data.get("pending_target")

    if not text or not target_lang:
        await callback.answer("⚠️ Сессия устарела", show_alert=True)
        await state.clear()
        await callback.message.answer("🔄 <b>Начни перевод заново</b>", reply_markup=get_main_keyboard())
        return

    try:
        wait_msg = await callback.message.answer("🔄 Перевожу с указанным языком...")
        translated, status, _, _ = await translate_text(text, target_lang, source_lang)
        
        if status == "success":
            result_text = (
                f"✅ <b>Готово!</b>\n\n"
                f" <b>{LANGUAGES[source_lang]}</b> ➜ <b>{LANGUAGES[target_lang]}</b>\n\n"
                f"<code>{translated}</code>"
            )
            await wait_msg.edit_text(result_text, reply_markup=get_result_keyboard())
        else:
            await wait_msg.edit_text(f"❌ {translated}", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Manual translation error: {e}")
        await callback.message.answer("❌ Ошибка перевода.", reply_markup=get_main_keyboard())

    await state.set_state(None)


@router.message(F.content_type.in_({"photo", "sticker", "voice", "video", "audio", "document", "animation", "location", "contact"}))
async def handle_non_text_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("️ Я работаю только с текстом. Отправь текст для перевода!", reply_markup=get_main_keyboard())


@router.message(~F.text)
async def handle_unknown_content(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("⚠️ Неизвестный тип сообщения. Отправь текст!", reply_markup=get_main_keyboard())


@router.error()
async def error_handler(event: Exception) -> bool:
    logger.error(f"Unhandled error: {event}", exc_info=True)
    return True