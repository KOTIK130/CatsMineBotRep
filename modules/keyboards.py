# modules/keyboards.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎣 Рыбачить"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🏪 Магазин")],
            [KeyboardButton(text="⛵ Кланы"), KeyboardButton(text="🏆 Рейтинги")],
            [KeyboardButton(text="🐉 Боссы"), KeyboardButton(text="🎁 Донат")]
        ],
        resize_keyboard=True
    )

def guild_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⛵ Мой клан"), KeyboardButton(text="🔍 Найти клан")],
            [KeyboardButton(text="🏗️ Создать клан"), KeyboardButton(text="🏆 Рейтинг кланов")],
            [KeyboardButton(text="💬 Клан-чат"), KeyboardButton(text="◀️ В меню")]
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

def fishermen_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎣 Мои рыбаки"), KeyboardButton(text="🤝 Нанять рыбака")],
            [KeyboardButton(text="⚙️ Обучить рыбака"), KeyboardButton(text="◀️ В меню")]
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

