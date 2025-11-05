# modules/top.py - Переделанные топы для рыбалки

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import users_collection
from modules.keyboards import main_menu_keyboard

router = Router(name="top")

# Клавиатура для выбора топа
top_selection_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐟 Топ рыбы"), KeyboardButton(text="💰 Топ денег")],
        [KeyboardButton(text="⭐ Топ звёзд"), KeyboardButton(text="🎣 Топ удочек")],
        [KeyboardButton(text="🍪 Топ печенек"), KeyboardButton(text="🔙 Назад")],
    ],
    resize_keyboard=True
)

def format_number(value):
    """Форматирует число без десятичных знаков и научной нотации"""
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        else:
            return f"{value:.0f}"
    return str(value)

@router.message(F.text == "🏆 Топы")
async def top_menu(message: Message):
    await message.answer(
        text="🏆 Выберите топ для просмотра:",
        reply_markup=top_selection_keyboard
    )

@router.message(F.text == "🐟 Топ рыбы")
async def top_fish(message: Message):
    users = await users_collection.find().sort("total_fish_caught", -1).limit(10).to_list(length=10)
    if not users:
        text = "Пока нет данных для топа по рыбе."
    else:
        text = "🏆 Топ-10 рыбаков по улову:\n\n"
        for i, u in enumerate(users, start=1):
            nick = u.get("nickname") or u.get("name") or f"Рыбак {u.get('user_id')}"
            fish_count = u.get('total_fish_caught', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {nick} — {format_number(fish_count)} рыб\n"
    await message.answer(text=text, reply_markup=top_selection_keyboard)

@router.message(F.text == "💰 Топ денег")
async def top_money(message: Message):
    users = await users_collection.find().sort("money", -1).limit(10).to_list(length=10)
    if not users:
        text = "Пока нет данных для топа по деньгам."
    else:
        text = "🏆 Топ-10 богачей:\n\n"
        for i, u in enumerate(users, start=1):
            nick = u.get("nickname") or u.get("name") or f"Рыбак {u.get('user_id')}"
            money = u.get('money', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {nick} — {format_number(money)}$\n"
    await message.answer(text=text, reply_markup=top_selection_keyboard)

@router.message(F.text == "⭐ Топ звёзд")
async def top_stars(message: Message):
    users = await users_collection.find().sort("sea_stars", -1).limit(10).to_list(length=10)
    if not users:
        text = "Пока нет данных для топа по морским звёздам."
    else:
        text = "🏆 Топ-10 звёздных рыбаков:\n\n"
        for i, u in enumerate(users, start=1):
            nick = u.get("nickname") or u.get("name") or f"Рыбак {u.get('user_id')}"
            stars = u.get('sea_stars', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {nick} — {stars} ⭐\n"
    await message.answer(text=text, reply_markup=top_selection_keyboard)

@router.message(F.text == "🎣 Топ удочек")
async def top_rods(message: Message):
    users = await users_collection.find().sort("rod_level", -1).limit(10).to_list(length=10)
    if not users:
        text = "Пока нет данных для топа по удочкам."
    else:
        text = "🏆 Топ-10 мастеров удочки:\n\n"
        for i, u in enumerate(users, start=1):
            nick = u.get("nickname") or u.get("name") or f"Рыбак {u.get('user_id')}"
            rod_level = u.get('rod_level', 1)
            prestige = u.get('prestige_level', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            prestige_text = f" (П{prestige})" if prestige > 0 else ""
            text += f"{medal} {nick} — Ур.{rod_level}{prestige_text}\n"
    await message.answer(text=text, reply_markup=top_selection_keyboard)

@router.message(F.text == "🍪 Топ печенек")
async def top_cookies(message: Message):
    users = await users_collection.find().sort("cookies", -1).limit(10).to_list(length=10)
    if not users:
        text = "Пока нет данных для топа по печенкам."
    else:
        text = "🏆 Топ-10 сладкоежек:\n\n"
        for i, u in enumerate(users, start=1):
            nick = u.get("nickname") or u.get("name") or f"Рыбак {u.get('user_id')}"
            cookies = u.get('cookies', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {nick} — {cookies} 🍪\n"
    await message.answer(text=text, reply_markup=top_selection_keyboard)

@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())
