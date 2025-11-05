# modules/fishing.py - Обновленная рыбалка с учетом бустеров и событий

from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
from decimal import Decimal, getcontext
from config import users_collection, DAILY_EVENTS, CASE_TYPES, FISH_TYPES, RARITY_COLORS, RARITY_NAMES
import random

getcontext().prec = 28

router = Router(name="fishing")

@router.message(F.text == "🎣 Рыбачить")
async def fishing_handler(message: Message):
    user_id = message.from_user.id

    # Проверка бана
    if await is_banned(user_id):
        await message.answer("⛔ Ваш аккаунт заблокирован")
        return

    # Получаем данные пользователя
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    # Получаем бонусы гильдии
    from modules.guilds import get_guild_bonuses, add_guild_contribution
    guild_bonuses = await get_guild_bonuses(user_id)

    # Ограничение по времени между рыбалкой
    last_fish_time = user.get("last_fish_time")
    now = datetime.utcnow()
    if last_fish_time and (now - last_fish_time).total_seconds() < 0.8:
        return

    # Параметры удочки и множители
    rod_level = user.get("rod_level", 1)
    fish_multiplier = Decimal(str(user.get("fish_multiplier", 1.0)))
    luck_x2 = user.get("luck_x2", 10.0)
    star_chance = user.get("star_chance", 5.0)

    # Проверка активных бустеров
    boosters = user.get("boosters", {})
    fish_booster_active = False
    star_booster_active = False
    
    fish_booster_end = boosters.get("fish_x2_end")
    if fish_booster_end and fish_booster_end > now:
        fish_booster_active = True
        fish_multiplier *= 2
    
    star_booster_end = boosters.get("star_x2_end")
    if star_booster_end and star_booster_end > now:
        star_booster_active = True
        star_chance *= 2

    # Проверка дневного события
    today = datetime.now().weekday()
    daily_bonus = Decimal(str(1.0))  # Конвертируем в Decimal
    daily_star_bonus = 1.0
    
    if today in DAILY_EVENTS:
        event = DAILY_EVENTS[today]
        if event["bonus"] == "fish_x2":
            daily_bonus = Decimal(str(2.0))  # Конвертируем в Decimal
        elif event["bonus"] == "stars_x2":
            daily_star_bonus = 2.0

    # Определяем какую рыбу поймали
    caught_fish = get_random_fish(rod_level)
    if not caught_fish:
        await message.answer("🎣 Рыба сорвалась с крючка!")
        return

    fish_type = caught_fish["type"]
    fish_data = caught_fish["data"]
    
    # Расчет количества пойманной рыбы (базовое количество)
    base_amount = max(1, rod_level // 3 + 1)  # Убираем Decimal, используем обычные числа
    
    # Шанс на х2 улов
    luck_bonus = 1
    luck_message = ""
    if random.randint(1, 100) <= luck_x2:
        luck_bonus = 2
        luck_message = " 🍀"

    # Применяем все множители к количеству
    fish_multiplier_float = float(fish_multiplier)
    daily_bonus_float = float(daily_bonus)
    total_amount = int(base_amount * fish_multiplier_float * daily_bonus_float * luck_bonus)

    # Убеждаемся что поймали хотя бы 1 рыбу
    total_amount = max(1, total_amount)

    # Применяем гильдейские бонусы
    if guild_bonuses["fish_bonus"] > 0:
        guild_bonus_amount = int(total_amount * guild_bonuses["fish_bonus"])
        total_amount += guild_bonus_amount

    # Обновляем в базе - добавляем конкретный тип рыбы И общую рыбу
    fish_inventory = user.get("fish_inventory", {})
    current_amount = fish_inventory.get(fish_type, 0)

    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"fish_inventory.{fish_type}": current_amount + total_amount,
                "last_fish_time": now
            },
            "$inc": {
                "fish": total_amount,  # Добавляем к общему количеству рыбы
                "total_fish_caught": total_amount
            }
        }
    )

    # Определяем редкость для отображения
    rarity_color = RARITY_COLORS.get(fish_data["rarity"], "⚪")
    rarity_name = RARITY_NAMES.get(fish_data["rarity"], "Обычная")
    
    # Основное сообщение
    response = f"🎣 Поймано: <b>{total_amount}x {fish_data['emoji']} {fish_data['name']}</b>"
    
    # Добавляем информацию о редкости
    if fish_data["rarity"] != "common":
        response += f"\n{rarity_color} <i>{rarity_name} рыба!</i>"
    
    # Добавляем информацию о цене
    total_value = total_amount * fish_data["price"]
    response += f"\n💰 Стоимость: <b>{total_value}$</b> ({fish_data['price']}$ за шт.)"
    
    # Добавляем информацию о бонусах
    bonus_parts = []
    if fish_multiplier > 1:
        bonus_parts.append(f"{fish_multiplier}x")
    if daily_bonus > 1:
        bonus_parts.append(f"День x{daily_bonus}")
    if luck_bonus > 1:
        bonus_parts.append("Удача x2")
    if guild_bonuses["fish_bonus"] > 0:
        bonus_parts.append(f"Гильдия +{guild_bonuses['fish_bonus']*100:.0f}%")
    
    if bonus_parts:
        response += f"\n🎁 Бонусы: {' • '.join(bonus_parts)}"
    
    response += luck_message

    await message.answer(response, parse_mode="HTML")

    # Применяем гильдейский бонус к звёздам
    final_star_chance = star_chance * daily_star_bonus
    if guild_bonuses["star_bonus"] > 0:
        final_star_chance *= (1 + guild_bonuses["star_bonus"])

    # Шанс на морские звёзды
    if random.randint(1, 100) <= final_star_chance:
        stars_found = random.randint(1, 3)
        
        # Гильдейский бонус к количеству звёзд
        if guild_bonuses["star_bonus"] > 0 and random.randint(1, 100) <= 30:
            stars_found += 1
        
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"sea_stars": stars_found}}
        )
        
        # Добавляем вклад в гильдию
        if guild_bonuses["star_bonus"] > 0:
            await add_guild_contribution(user_id, stars=stars_found)
        
        star_message = f"⭐ Найдено {stars_found} морских звёзд!"
        if star_booster_active:
            star_message += " 🚀"
        if daily_star_bonus > 1:
            star_message += " 🌟"
        if guild_bonuses["star_bonus"] > 0:
            star_message += " ⛵"
            
        await message.answer(star_message)

    # Шанс на кейс
    case_chance = 15
    if random.randint(1, 100) <= case_chance:
        case_type = get_random_case()
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {f"cases.{case_type}": 1}}
        )
        case_name = CASE_TYPES[case_type]["name"]
        await message.answer(f"📦 Найден кейс: {case_name}!")

    # Проверка достижений
    await check_achievements(user_id, user)

    # Добавляем вклад в гильдию
    if guild_bonuses["fish_bonus"] > 0:
        await add_guild_contribution(user_id, fish=total_amount)

def get_random_case():
    """Получить случайный тип кейса с учетом шансов"""
    rand = random.randint(1, 100)
    cumulative = 0
    
    for case_type, data in CASE_TYPES.items():
        cumulative += data["chance"]
        if rand <= cumulative:
            return case_type
    
    return "can"  # Fallback

async def check_achievements(user_id: int, user: dict):
    """Проверка и выдача достижений"""
    achievements = user.get("achievements", [])
    total_fish = user.get("total_fish_caught", 0)
    rod_level = user.get("rod_level", 1)
    
    new_achievements = []
    
    # Проверяем достижения
    if "first_fish" not in achievements and total_fish >= 1:
        new_achievements.append("first_fish")
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"money": 100}}
        )
    
    if "fish_100" not in achievements and total_fish >= 100:
        new_achievements.append("fish_100")
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"money": 1000}}
        )
    
    if "fish_1000" not in achievements and total_fish >= 1000:
        new_achievements.append("fish_1000")
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"sea_stars": 5}}
        )
    
    if "rod_10" not in achievements and rod_level >= 10:
        new_achievements.append("rod_10")
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"sea_stars": 2}}
        )
    
    if "rod_30" not in achievements and rod_level >= 30:
        new_achievements.append("rod_30")
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"sea_stars": 10}}
        )
    
    # Добавляем новые достижения
    if new_achievements:
        await users_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"achievements": {"$each": new_achievements}}}
        )

async def is_banned(user_id: int) -> bool:
    user = await users_collection.find_one({"user_id": user_id})
    return user.get("banned", False) if user else False

def register_handlers(dp):
    dp.include_router(router)

def get_random_fish(rod_level: int):
    """Определяет какую рыбу поймал игрок"""
    from config import FISH_TYPES
    
    # Фильтруем рыбу по уровню удочки
    available_fish = []
    for fish_type, fish_data in FISH_TYPES.items():
        if rod_level >= fish_data["min_level"]:
            available_fish.append({
                "type": fish_type,
                "data": fish_data,
                "chance": fish_data["chance"]
            })
    
    if not available_fish:
        return None
    
    # Определяем рыбу по шансам
    total_chance = sum(fish["chance"] for fish in available_fish)
    rand = random.uniform(0, total_chance)
    
    current_chance = 0
    for fish in available_fish:
        current_chance += fish["chance"]
        if rand <= current_chance:
            return fish
    
    # Fallback - возвращаем первую доступную рыбу
    return available_fish[0]
