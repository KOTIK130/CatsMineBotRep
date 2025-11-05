# modules/keyboards.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎣 Рыбачить"), KeyboardButton(text="🎒 Инвентарь")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="⚡ Улучшения")],
            [KeyboardButton(text="🏆 Топы"), KeyboardButton(text="🐉 Боссы")],
            [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="⛵ Гильдии")],
            [KeyboardButton(text="🌊 Болото"), KeyboardButton(text="📦 Кейсы")],
            [KeyboardButton(text="🎁 Донат"), KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True
    )

def guild_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⛵ Моя гильдия"), KeyboardButton(text="🔍 Найти гильдию")],
            [KeyboardButton(text="🏗️ Создать гильдию"), KeyboardButton(text="🏆 Рейтинг гильдий")],
            [KeyboardButton(text="💬 Гильд-чат"), KeyboardButton(text="◀️ В меню")]
        ],
        resize_keyboard=True
    )

def guild_management_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Участники"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="📢 Объявление"), KeyboardButton(text="🎯 Задания")],
            [KeyboardButton(text="💰 Казна"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="💬 Модерация чата"), KeyboardButton(text="◀️ К гильдии")]
        ],
        resize_keyboard=True
    )

def swamp_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏗 Постройки"), KeyboardButton(text="👷 Работники")],
            [KeyboardButton(text="🏆 Достижения"), KeyboardButton(text="◀️ В меню")],
        ],
        resize_keyboard=True
    )

def shop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌅 Дневной магазин"), KeyboardButton(text="🛍️ Донат магазин")],
            [KeyboardButton(text="🎫 Промокоды"), KeyboardButton(text="◀️ В меню")],
        ],
        resize_keyboard=True
    )

def daily_shop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ За морские звёзды"), KeyboardButton(text="🍪 За печеньки")],
            [KeyboardButton(text="◀️ В магазин")],
        ],
        resize_keyboard=True
    )

def upgrades_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎣 Улучшить удочку"), KeyboardButton(text="⭐ Шанс звёзд")],
            [KeyboardButton(text="🍀 Удача на х2"), KeyboardButton(text="🚀 Бустеры")],
            [KeyboardButton(text="◀️ В меню")],
        ],
        resize_keyboard=True
    )

def workers_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👷 Мои работники"), KeyboardButton(text="🤝 Принять сотрудника")],
            [KeyboardButton(text="⚙️ Обучить рабочего"), KeyboardButton(text="◀️ В болото")]
        ],
        resize_keyboard=True
    )
