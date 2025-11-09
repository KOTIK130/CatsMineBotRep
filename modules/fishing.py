# modules/fishing.py - Новая, упрощенная и сбалансированная рыбалка

from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime, timedelta
from config import users_collection, FISH_TYPES, RARITY_COLORS, RARITY_NAMES, CASE_TYPES
import random

router = Router(name="fishing")

# Кулдаун на рыбалку в секундах
FISHING_COOLDOWN = 1.0

@router.message(F.text == "🎣 Рыбачить")
async def fishing_handler(message: Message):
    user_id = message.from_user.id

    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    if user.get("banned", False):
        await message.answer("⛔ Ваш аккаунт заблокирован.")
        return

    # Проверка кулдауна
    now = datetime.utcnow()
    last_fish_time = user.get("last_fish_time")
    if last_fish_time and (now - last_fish_time).total_seconds() < FISHING_COOLDOWN:
        # Можно добавить сообщение о кулдауне, но для скорости лучше просто игнорировать
        return

    # --- Логика рыбалки ---

    rod_level = user.get("rod_level", 1)

    # 1. Определяем, какую рыбу поймали
    caught_fish_info = get_random_fish(rod_level)
    if not caught_fish_info:
        await message.answer("🎣 Рыба сорвалась с крючка!")
        return

    fish_type = caught_fish_info["type"]
    fish_data = caught_fish_info["data"]

    # 2. Расчет количества улова
    # Базовое количество зависит от уровня удочки
    base_amount = 1 + rod_level // 5
    
    # Применяем множители (пока только базовый, в будущем добавим от бустеров и т.д.)
    fish_multiplier = user.get("fish_multiplier", 1.0)
    total_amount = int(base_amount * fish_multiplier)
    total_amount = max(1, total_amount) # Гарантируем, что поймали хотя бы 1 рыбу

    # 3. Обновляем данные пользователя
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"last_fish_time": now},
            "$inc": {
                f"fish_inventory.{fish_type}": total_amount,
                "total_fish_caught": total_amount
            }
        }
    )

    # 4. Формируем красивый ответ
    rarity_color = RARITY_COLORS.get(fish_data["rarity"], "⚪")
    rarity_name = RARITY_NAMES.get(fish_data["rarity"], "Обычная")
    
    response = (
        f"🎣 Поймано: <b>{total_amount}x {fish_data['emoji']} {fish_data['name']}</b>\n"
        f"{rarity_color} <i>{rarity_name}</i>"
    )
    await message.answer(response, parse_mode="HTML")

    # --- Дополнительные события ---

    # 5. Шанс на морские звёзды
    star_chance = user.get("star_chance", 5.0)
    if random.random() * 100 < star_chance:
        stars_found = random.randint(1, 3)
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"sea_stars": stars_found}}
        )
        await message.answer(f"⭐ Найдено <b>{stars_found}</b> морских звёзд!")

    # 6. Шанс на кейс (упрощенный)
    if random.random() < 0.05: # 5% шанс на кейс
        case_type = "can" # Пока только самый простой кейс
        case_name = CASE_TYPES[case_type]["name"]
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {f"cases.{case_type}": 1}}
        )
        await message.answer(f"📦 Найден кейс: <b>{case_name}</b>!")


def get_random_fish(rod_level: int) -> dict | None:
    """
    Определяет, какую рыбу поймал игрок, на основе уровня удочки и шансов.
    """
    available_fish = [
        {"type": f_type, "data": f_data}
        for f_type, f_data in FISH_TYPES.items()
        if rod_level >= f_data["min_level"]
    ]
    
    if not available_fish:
        return None

    # Используем веса (шансы) для выбора рыбы
    chances = [fish["data"]["chance"] for fish in available_fish]
    chosen_fish = random.choices(available_fish, weights=chances, k=1)[0]
    
    return chosen_fish
