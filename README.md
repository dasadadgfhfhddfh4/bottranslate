# 🌍 TranslatorBot - Умный Telegram Переводчик

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

<div align="center">
  <img src="https://img.shields.io/badge/Translation-Multiple%20APIs-red?style=for-the-badge" alt="Translation APIs">
  <br>
  <strong>🤖 Мощный бот с автоопределением языка и 6 fallback API</strong>
</div>

---

## 📋 Оглавление

- [✨ Особенности](#-особенности)
- [🚀 Быстрый старт](#-быстрый-старт)
- [📖 Документация](#-документация)
- [🏗 Структура проекта](#-структура-проекта)
- [⚙️ Конфигурация](#️-конфигурация)
- [🔧 API Переводчиков](#-api-переводчиков)
- [📊 Поддерживаемые языки](#-поддерживаемые-языки)
- [💡 Примеры использования](#-примеры-использования)
- [🛠 Расширение функционала](#-расширение-функционала)
- [📝 Roadmap](#-roadmap)
- [🤝 Вклад](#-вклад)
- [📜 Лицензия](#-лицензия)
- [👨‍ Автор](#-автор)

---

## ✨ Особенности

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://img.icons8.com/color/96/000000/translate.png" width="64" alt="Auto Translate"/>
        <br><strong>🔄 Автоопределение</strong><br>
        <small>Язык определяется автоматически</small>
      </td>
      <td align="center">
        <img src="https://img.icons8.com/color/96/000000/api-settings.png" width="64" alt="Multiple APIs"/>
        <br><strong>🌐 6 API</strong><br>
        <small>Fallback система переводчиков</small>
      </td>
      <td align="center">
        <img src="https://img.icons8.com/color/96/000000/save.png" width="64" alt="Save Preferences"/>
        <br><strong>💾 Сохранение</strong><br>
        <small>Язык сохраняется для удобства</small>
      </td>
      <td align="center">
        <img src="https://img.icons8.com/color/96/000000/smartphone.png" width="64" alt="Async"/>
        <br><strong>⚡ Async</strong><br>
        <small>Асинхронная архитектура</small>
      </td>
    </tr>
  </table>
</div>

### 🔥 Ключевые преимущества

✅ **Умная система fallback** — если один API не работает, автоматически используется следующий  
✅ **Pydantic Settings** — типизированная конфигурация с валидацией  
✅ **FSM (Finite State Machine)** — корректное управление состояниями диалога  
✅ **Inline клавиатуры** — удобный интерфейс выбора языков  
✅ **Обработка ошибок** — логирование и graceful degradation  
✅ **Production Ready** — готов к деплою на продакшен  

---

## 🚀 Быстрый старт

### 📥 Установка за 2 минуты

```bash
# 1. Клонируй репозиторий
git clone https://github.com/dasadadgfhfhddfh4/bottranslate.git
cd bottranslate

# 2. Создай виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Установи зависимости
pip install -r requirements.txt

# 4. Настрой токен
echo "BOT_TOKEN=your_token_here" > .env

# 5. Запусти бота
python -m bot.main
