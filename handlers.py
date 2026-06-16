"""
Обработчики команд и callback-запросов.
- Умное сохранение языка пользователя
- Typing-индикатор "печатает..."
- Обработка всех типов не-текстовых сообщений
- Защита от всех крашей
"""
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

# 🧠 Хранилище предпочтений пользователей (запоминание языка)
# В продакшене замени на Redis/PostgreSQL
user_preferences: dict[int, dict] = {}


class TranslationStates(StatesGroup):
    """Состояния FSM для многошагового диалога."""
    choosing_target = State()
    waiting_for_text = State()
    correcting_language = State()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """Безопасное редактирование сообщения — не падает на ошибках."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.debug(f"safe_edit: {e}")
    except Exception as e:
        logger.error(f"Ошибка редактирования: {e}")


async def typing_indicator(message: Message, stop_event: asyncio.Event) -> None:
    """
    Фоновая задача: показывает 'печатает...' под именем бота.
    Telegram typing длится 5 секунд, обновляем каждые 4.
    """
    while not stop_event.is_set():
        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(4)
        except Exception:
            break


# ===== ГЛАВНЫЕ КОМАНДЫ =====

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Приветствие с сохранённым языком, если есть."""
    await state.clear()
    
    saved_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
    saved_text = f"\n\n💾 <b>Твой последний язык:</b> {LANGUAGES.get(saved_lang)}" if saved_lang else ""
    
    welcome_text = (
        "👋 <b>Привет!</b> Я — <b>TranslatorBot</b> 🌐\n\n"
        "🤖 Умный переводчик с <b>автоопределением языка</b>\n\n"
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
    """Быстрый возврат в меню."""
    await state.clear()
    saved_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
    saved_text = f"\n💾 Язык: <b>{LANGUAGES.get(saved_lang)}</b>" if saved_lang else ""
    await message.answer(f"🏠 <b>Главное меню</b>{saved_text}", reply_markup=get_main_keyboard())


# ===== ГЛАВНОЕ МЕНЮ =====

@router.callback_query(F.data == "start_translate")
async def start_translation(callback: CallbackQuery, state: FSMContext) -> None:
    """
    🧠 УМНО: если язык уже выбран — сразу ждём текст.
    Иначе — показываем выбор языка.
    """
    await callback.answer()
    
    saved_lang = user_preferences.get(callback.from_user.id, {}).get("target_lang")
    
    if saved_lang and saved_lang in LANGUAGES:
        await state.update_data(target_lang=saved_lang)
        await state.set_state(TranslationStates.waiting_for_text)
        await safe_edit(
            callback,
            f"✍️ <b>Отправь текст для перевода</b>\n\n"
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
    """Смена языка."""
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
    """Возврат в меню."""
    await callback.answer()
    await state.clear()
    
    saved_lang = user_preferences.get(callback.from_user.id, {}).get("target_lang")
    saved_text = f"\n\n💾 Текущий язык: <b>{LANGUAGES.get(saved_lang)}</b>" if saved_lang else ""
    
    await safe_edit(
        callback,
        f"🏠 <b>Главное меню</b>{saved_text}\n\n"
        f"Выбери действие 👇",
        get_main_keyboard()
    )


@router.callback_query(F.data == "languages")
async def show_languages(callback: CallbackQuery) -> None:
    """Список поддерживаемых языков."""
    await callback.answer()
    await safe_edit(
        callback,
        f"🌍 <b>Поддерживаемые языки</b>\n\n{get_languages_list_text()}\n\n"
        f"💡 <i>Язык оригинала определяется автоматически!</i>",
        get_main_keyboard()
    )


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery) -> None:
    """Экран помощи."""
    await callback.answer()
    help_text = (
        "📖 <b>Как пользоваться</b>\n\n"
        "1️⃣ Нажми <b>«Начать перевод»</b>\n"
        "2️⃣ Выбери язык (1 раз — сохранится!)\n"
        "3️⃣ Отправь текст\n"
        "4️⃣ Получи перевод! 🎉\n\n"
        "🔄 <b>Быстрые переводы:</b>\n"
        "После первого выбора языка — сразу отправляй текст!\n\n"
        "❓ <b>Неверный язык?</b>\n"
        "После перевода нажми «Неверный язык» — выбери вручную\n\n"
        "💡 <b>Совет:</b> максимум 500 символов за раз"
    )
    await safe_edit(callback, help_text, get_main_keyboard())


# ===== ВЫБОР ЯЗЫКА =====

@router.callback_query(TranslationStates.choosing_target, F.data.startswith("target_"))
async def process_target_language(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохраняем выбор и переходим к вводу текста."""
    await callback.answer()
    target_lang = callback.data.replace("target_", "")
    
    if target_lang not in LANGUAGES:
        await callback.answer("❌ Неизвестный язык", show_alert=True)
        return
    
    # 💾 СОХРАНЯЕМ выбор пользователя
    user_id = callback.from_user.id
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    user_preferences[user_id]["target_lang"] = target_lang
    
    await state.update_data(target_lang=target_lang)
    await state.set_state(TranslationStates.waiting_for_text)
    await safe_edit(
        callback,
        f"✍️ <b>Отправь текст для перевода</b>\n\n"
        f"🎯 Перевожу на: <b>{LANGUAGES[target_lang]}</b>\n"
        f"🕵️ Язык оригинала определю сам!\n\n"
        f"✅ <i>Язык сохранён — в следующий раз сразу к вводу!</i>"
    )


# ===== ОСНОВНОЙ ПЕРЕВОД =====

@router.message(TranslationStates.waiting_for_text, F.text)
async def process_translation(message: Message, state: FSMContext) -> None:
    """Основная логика: перевод + typing индикатор."""
    data = await state.get_data()
    text = message.text.strip()
    target_lang = data.get("target_lang")
    
    if not target_lang:
        target_lang = user_preferences.get(message.from_user.id, {}).get("target_lang")
        if not target_lang:
            await message.answer(
                "⚠️ <b>Сначала выбери язык</b> 🎯",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
    
    # Валидация
    if len(text) > 500:
        await message.answer(
            "⚠️ <b>Текст слишком длинный</b>\n\n"
            "Максимум <b>500 символов</b> за раз.\n"
            f"У тебя: <b>{len(text)}</b> символов"
        )
        return
    
    if len(text) < 2:
        await message.answer("⚠️ <b>Слишком короткий текст</b> (минимум 2 символа)")
        return
    
    # Сохраняем текст для функции "Неверный язык"
    await state.update_data(last_text=text, target_lang=target_lang)
    
    # ⌨️ ЗАПУСКАЕМ TYPING-ИНДИКАТОР
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(typing_indicator(message, stop_event))
    
    try:
        # 🌐 Делаем перевод
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
            await message.answer(
                f"❌ <b>Ошибка перевода</b>\n\n{translated}\n\n"
                f"Попробуй ещё раз 🔄",
                reply_markup=get_main_keyboard()
            )
    finally:
        # 🛑 Останавливаем typing
        stop_event.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Сбрасываем состояние, но не очищаем данные
    await state.set_state(None)


# ===== ИСПРАВЛЕНИЕ ЯЗЫКА =====

@router.callback_query(F.data == "wrong_language")
async def wrong_language_clicked(callback: CallbackQuery, state: FSMContext) -> None:
    """Ручной выбор языка оригинала."""
    await callback.answer()
    data = await state.get_data()
    
    last_text = data.get("last_text")
    if not last_text:
        await callback.answer(
            "⚠️ Начни перевод заново — я забыл текст",
            show_alert=True
        )
        await state.clear()
        await callback.message.answer(
            "🔄 <b>Начни новый перевод</b>",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.update_data(
        pending_text=last_text,
        pending_target=data.get("target_lang")
    )
    await state.set_state(TranslationStates.correcting_language)
    await safe_edit(
        callback,
        "🔧 <b>Выбери язык оригинала вручную</b>\n\n"
        "На каком языке написан текст?",
        get_source_language_keyboard()
    )


@router.callback_query(TranslationStates.correcting_language, F.data.startswith("manual_source_"))
async def process_manual_source(callback: CallbackQuery, state: FSMContext) -> None:
    """Повторный перевод с ручным языком."""
    await callback.answer()
    source_lang = callback.data.replace("manual_source_", "")
    data = await state.get_data()
    
    text = data.get("pending_text")
    target_lang = data.get("pending_target")
    
    if not text or not target_lang:
        await callback.answer("⚠️ Сессия устарела", show_alert=True)
        await state.clear()
        await callback.message.answer(
            "🔄 <b>Начни перевод заново</b>",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Typing indicator
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(typing_indicator(callback.message, stop_event))
    
    try:
        wait_msg = await callback.message.answer("🔄 Перевожу с указанным языком...")
        translated, status, _, _ = await translate_text(text, target_lang, source_lang)
        
        if status == "success":
            result_text = (
                f"✅ <b>Готово!</b>\n\n"
                f"🔄 <b>{LANGUAGES[source_lang]}</b> ➜ <b>{LANGUAGES[target_lang]}</b>\n\n"
                f"<code>{translated}</code>"
            )
            await wait_msg.edit_text(result_text, reply_markup=get_result_keyboard())
        else:
            await wait_msg.edit_text(
                f"❌ {translated}",
                reply_markup=get_main_keyboard()
            )
    finally:
        stop_event.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    await state.set_state(None)


# ===== ОБРАБОТКА НЕ-ТЕКСТОВЫХ СООБЩЕНИЙ =====

@router.message(F.content_type.in_({
    "photo", "sticker", "voice", "video", "audio",
    "document", "animation", "location", "contact"
}))
async def handle_non_text_message(message: Message, state: FSMContext) -> None:
    """
    Умный обработчик не-текстовых сообщений.
    Определяет тип контента и даёт понятный ответ.
    """
    await state.clear()
    
    content_map = {
        "photo": ("📸 Фото", "Отправь текстом — я переведу!"),
        "sticker": ("🎭 Стикер", "Стикеры не перевожу 😄 Отправь текст!"),
        "voice": ("🎤 Голосовое", "Голос не перевожу. Отправь текстом!"),
        "video": ("🎥 Видео", "Видео не перевожу. Напиши текстом!"),
        "audio": ("🎵 Аудио", "Аудио не перевожу. Отправь текстом!"),
        "document": ("📎 Файл", "Файлы не перевожу. Отправь текст!"),
        "animation": ("🎬 GIF", "GIF не перевожу. Напиши текстом!"),
        "location": ("📍 Геолокация", "Локацию не перевожу. Отправь текст!"),
        "contact": ("👤 Контакт", "Контакты не перевожу. Напиши текстом!"),
    }
    
    emoji_title, hint = content_map.get(message.content_type, ("⚠️ Контент", "Отправь текст!"))
    
    response = (
        f"{emoji_title}\n\n"
        f"❌ <b>Я не могу это перевести</b>\n\n"
        f"✍️ <b>Введи текст для перевода</b>\n\n"
        f"💡 {hint}"
    )
    
    await message.answer(response, reply_markup=get_main_keyboard())


@router.message(~F.text)
async def handle_unknown_content(message: Message, state: FSMContext) -> None:
    """Ловит всё, что не текст и не в списке выше."""
    await state.clear()
    await message.answer(
        "⚠️ <b>Неизвестный тип сообщения</b>\n\n"
        "✍️ <b>Введи текст для перевода</b> 📝",
        reply_markup=get_main_keyboard()
    )


# ===== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК =====

@router.error()
async def error_handler(event: Exception) -> bool:
    """Ловит все необработанные ошибки."""
    logger.error(f"Unhandled error: {event}", exc_info=True)
    return True