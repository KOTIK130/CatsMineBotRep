# modules/profile.py - Новый профиль рыбака
from aiogram import Router, F
from aiogram.types import Message
from decimal import Decimal, getcontext
from config import users_collection
from modules.nick import get_nickname

getcontext().prec = 28

router = Router(name="profile")

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})

    if not user:
        await message.answer("Сначала напиши /start.")
        return

    nickname = await get_nickname(user_id, fallback_name=message.from_user.first_name)
    
    # Основные данные
    rod_level = user.get("rod_level", 1)
    money = user.get("money", 0)
    fish_inventory = user.get("fish_inventory", {})
    sea_stars = user.get("sea_stars", 0)
    cookies = user.get("cookies", 0)
    total_fish_caught = user.get("total_fish_caught", 0)
    
    # Подсчитываем общее количество рыбы в инвентаре
    from config import FISH_TYPES
    total_fish_in_inventory = sum(fish_inventory.values())
    total_fish_value = 0
    
    for fish_type, amount in fish_inventory.items():
        if fish_type in FISH_TYPES:
            total_fish_value += amount * FISH_TYPES[fish_type]["price"]
    
    # Навыки
    fish_multiplier = user.get("fish_multiplier", 1.0)
    star_chance = user.get("star_chance", 5.0)
    luck_x2 = user.get("luck_x2", 10.0)
    
    # Постройки и рабочие
    buildings = user.get("buildings", [])
    workers = user.get("workers", [])
    
    # Материалы
    materials = user.get("materials", {})
    wood = materials.get("wood", 0)
    rope = materials.get("rope", 0)
    metal = materials.get("metal", 0)
    crystal = materials.get("crystal", 0)
    
    # Достижения
    achievements = user.get("achievements", [])
    achievement_count = len(achievements)

    # Информация о гильдии
    guild_id = user.get("guild_id")
    guild_info = ""
    if guild_id:
        from modules.guilds import guilds_collection, GUILD_RANKS
        guild = await guilds_collection.find_one({"_id": guild_id})
        if guild:
            # Находим информацию о участнике
            member_info = None
            for member in guild.get("members", []):
                if member["user_id"] == user_id:
                    member_info = member
                    break
        
            if member_info:
                rank_info = GUILD_RANKS[member_info["rank"]]
                guild_info = (
                    f"┃ ⛵ Гильдия: <b>{guild['name']}</b>\n"
                    f"┃ 🏅 Ранг: {rank_info['name']}\n"
                    f"┃ 🐟 Вклад рыбой: <b>{member_info.get('contribution_fish', 0):,}</b>\n"
                    f"┃ ⭐ Вклад звёздами: <b>{member_info.get('contribution_stars', 0):,}</b>\n"
                )

    text = (
        f"👤 <b>Профиль рыбака — {nickname}</b>\n"
        f"┏━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 🆔 ID: <code>{user_id}</code>\n"
        f"┃ 🎣 Уровень удочки: <b>{rod_level}</b>\n"
        f"┃ 🏆 Престиж: <b>{user.get('prestige_level', 0)}</b>\n"
        f"┃ 🐟 Рыба: <b>{total_fish_in_inventory:,}</b> ({total_fish_value}$)\n"
        f"┃ 💰 Деньги: <b>{money:,}$</b>\n"
        f"┃ ⭐ Морские звёзды: <b>{sea_stars}</b>\n"
        f"┃ 🍪 Печеньки: <b>{cookies}</b>\n"
        f"┃ 🏆 Всего поймано: <b>{total_fish_caught:,}</b>\n"
        f"┣━━━━━━━━━━━━━━━━━━┫\n"
        f"┃ ⚡ Множитель рыбы: <b>{fish_multiplier}x</b>\n"
        f"┃ ⭐ Шанс звёзд: <b>{star_chance}%</b>\n"
        f"┃ 🍀 Удача на х2: <b>{luck_x2}%</b>\n"
        f"┣━━━━━━━━━━━━━━━━━━┫\n"
        f"{guild_info}"
        f"┃ 🏗️ Построек: <b>{len(buildings)}</b>\n"
        f"┃ 👷‍♂️ Рабочих: <b>{len(workers)}/3</b>\n"
        f"┃ 🏆 Достижений: <b>{achievement_count}</b>\n"
        f"┣━━━━━━━━━━━━━━━━━━┫\n"
        f"┃ 🪵 Дерево: <b>{wood}</b>\n"
        f"┃ 🪢 Верёвка: <b>{rope}</b>\n"
        f"┃ ⚙️ Металл: <b>{metal}</b>\n"
        f"┃ 💎 Кристалл: <b>{crystal}</b>\n"
        f"┗━━━━━━━━━━━━━━━━━━┛"
    )

    await message.answer(text, parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)
