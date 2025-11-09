# modules/user_stats.py - Статистика рыбака

from aiogram import Router, F
from aiogram.types import Message
from decimal import Decimal, getcontext
from config import users_collection
from modules.nick import get_nickname

getcontext().prec = 28

router = Router(name="user_statistic")

async def get_user_data(user_id: int) -> dict:
    return await users_collection.find_one({"user_id": user_id})

def create_progress_bar(current: int, maximum: int, length: int = 12) -> str:
    filled_length = int(length * current // maximum)
    bar = "█" * filled_length + "─" * (length - filled_length)
    percent = int((current / maximum) * 100)
    return f"[{bar}] {percent}%"

@router.message(F.text == "📊 Статистика")
async def statistics_handler(message: Message):
    await show_statistics(message)

async def show_statistics(message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        await message.answer("Вы не зарегистрированы в системе. Напишите /start, чтобы начать.")
        return

    nickname = await get_nickname(user_id, fallback_name=message.from_user.first_name)

    # Данные рыбака
    rod_level = user_data.get("rod_level", 1)
    fish_inventory = user_data.get("fish_inventory", {})
    money = user_data.get("money", 0)
    total_fish_caught = user_data.get("total_fish_caught", 0)
    sea_stars = user_data.get("sea_stars", 0)
    cookies = user_data.get("cookies", 0)
    fish_multiplier = user_data.get("fish_multiplier", 1.0)
    star_chance = user_data.get("star_chance", 5.0)
    luck_x2 = user_data.get("luck_x2", 10.0)
    prestige_level = user_data.get("prestige_level", 0)
    
    # Подсчитываем общее количество рыбы
    from config import FISH_TYPES
    total_fish_in_inventory = sum(fish_inventory.values())
    total_fish_value = 0
    
    for fish_type, amount in fish_inventory.items():
        if fish_type in FISH_TYPES:
            total_fish_value += amount * FISH_TYPES[fish_type]["price"]

    # Постройки и рабочие
    buildings = user_data.get("buildings", [])
    workers = user_data.get("workers", [])
    achievements = user_data.get("achievements", [])

    progress_bar = create_progress_bar(rod_level, 60)

    text = (
        f"📊 <b>Статистика рыбака — {nickname}</b>\n"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 🆔 ID: <code>{user_id}</code>\n"
        f"┃ 🎣 Уровень удочки: <b>{rod_level}/60</b>\n"
        f"┃ 🏆 Престиж: <b>{prestige_level}</b>\n"
        f"┃ 🛠 Прогресс: {progress_bar}\n"
        f"┃ 🐟 Рыба: <b>{total_fish_in_inventory:,}</b> ({total_fish_value}$)\n"
        f"┃ 💰 Деньги: <b>{money:,}$</b>\n"
        f"┃ ⭐ Морские звёзды: <b>{sea_stars}</b>\n"
        f"┃ 🍪 Печеньки: <b>{cookies}</b>\n"
        f"┃ 🏆 Всего поймано: <b>{total_fish_caught:,}</b>\n"
        f"┃ ⚡ Множитель рыбы: <b>{fish_multiplier}x</b>\n"
        f"┃ ⭐ Шанс звёзд: <b>{star_chance}%</b>\n"
        f"┃ 🍀 Удача на х2: <b>{luck_x2}%</b>\n"
        f"┃ 🏗 Построек: <b>{len(buildings)}</b>\n"
        f"┃ 👷 Рабочих: <b>{len(workers)}/3</b>\n"
        f"┃ 🏆 Достижений: <b>{len(achievements)}</b>\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━┛"
    )

    await message.answer(text, parse_mode="HTML")
