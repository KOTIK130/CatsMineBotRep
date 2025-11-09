# modules/profile.py - Новый, чистый и красивый профиль

from aiogram import Router, F
from aiogram.types import Message
from config import users_collection, FISH_TYPES
from modules.nick import get_nickname
from utils import format_value # Используем наш новый форматер

router = Router(name="profile")

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})

    if not user:
        await message.answer("Сначала напиши /start.")
        return

    nickname = await get_nickname(user_id, fallback_name=message.from_user.first_name)
    
    # --- Сбор данных ---
    rod_level = user.get("rod_level", 1)
    prestige_level = user.get("prestige_level", 0)
    
    money = user.get("money", 0)
    sea_stars = user.get("sea_stars", 0)
    cookies = user.get("cookies", 0)
    
    total_fish_caught = user.get("total_fish_caught", 0)
    
    # Подсчитываем общее количество и стоимость рыбы в инвентаре
    fish_inventory = user.get("fish_inventory", {})
    total_fish_in_inventory = sum(fish_inventory.values())
    
    total_fish_value = 0
    for fish_type, amount in fish_inventory.items():
        if fish_type in FISH_TYPES:
            total_fish_value += amount * FISH_TYPES[fish_type]["price"]
            
    # Навыки
    fish_multiplier = user.get("fish_multiplier", 1.0)
    star_chance = user.get("star_chance", 5.0)
    luck_x2 = user.get("luck_x2", 10.0)

    # --- Формирование текста профиля ---
    
    # Блок основной информации
    profile_header = (
        f"<b>👤 Профиль: {nickname}</b>\n"
        f"ID: <code>{user_id}</code>\n"
    )

    # Блок статистики
    stats_block = (
        f"<b>📊 Статистика</b>\n"
        f"├ Уровень удочки: <b>{rod_level}</b>\n"
        f"├ Престиж: <b>{prestige_level}</b>\n"
        f"└ Всего поймано: <b>{format_value(total_fish_caught)}</b> рыбы\n"
    )

    # Блок инвентаря
    inventory_block = (
        f"<b>🎒 Инвентарь</b>\n"
        f"├ Рыба в садке: <b>{format_value(total_fish_in_inventory)}</b> шт.\n"
        f"└ Стоимость: <b>{format_value(total_fish_value)}</b> $\n"
    )

    # Блок валют
    currency_block = (
        f"<b>💎 Валюты</b>\n"
        f"├ Деньги: <b>{format_value(money)}</b> $\n"
        f"├ Морские звёзды: <b>{format_value(sea_stars)}</b> ⭐\n"
        f"└ Печеньки: <b>{format_value(cookies)}</b> 🍪\n"
    )
    
    # Блок навыков
    skills_block = (
        f"<b>🚀 Навыки</b>\n"
        f"├ Множитель рыбы: <b>x{fish_multiplier:.2f}</b>\n"
        f"├ Шанс звёзд: <b>{star_chance:.1f}%</b>\n"
        f"└ Шанс удачи: <b>{luck_x2:.1f}%</b>\n"
    )
    
    # Собираем все блоки вместе
    full_profile = (
        f"{profile_header}\n"
        f"{stats_block}\n"
        f"{inventory_block}\n"
        f"{currency_block}\n"
        f"{skills_block}"
    )

    await message.answer(full_profile, parse_mode="HTML")
