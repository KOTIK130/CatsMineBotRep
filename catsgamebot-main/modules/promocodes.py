# modules/promocodes.py - Система промокодов
from aiogram import Router, F
from aiogram.types import Message
from config import users_collection, db
from datetime import datetime

router = Router(name="promocodes")

promocodes_collection = db["promocodes"]

@router.message(F.text == "🎫 Промокоды")
async def show_promocode_menu(message: Message):
    await message.answer(
        "🎫 <b>Промокоды</b>\n\n"
        "Введите промокод для получения награды:\n"
        "Пример: <code>FISH2024</code>",
        parse_mode="HTML"
    )

@router.message(F.text.startswith("/promo "))
async def use_promocode(message: Message):
    user_id = message.from_user.id
    code = message.text[7:].strip().upper()
    
    if not code:
        await message.answer("❌ Введите промокод после команды /promo")
        return
    
    # Проверяем промокод в базе
    promo = await promocodes_collection.find_one({"code": code})
    
    if not promo:
        await message.answer("❌ Промокод не найден или недействителен!")
        return
    
    # Проверяем срок действия
    if promo.get("expires_at") and promo["expires_at"] < datetime.utcnow():
        await message.answer("❌ Срок действия промокода истёк!")
        return
    
    # Проверяем лимит использований
    if promo.get("max_uses") and promo.get("used_count", 0) >= promo["max_uses"]:
        await message.answer("❌ Промокод исчерпан!")
        return
    
    # Проверяем, использовал ли пользователь этот промокод
    user = await users_collection.find_one({"user_id": user_id})
    used_promos = user.get("used_promocodes", [])
    
    if code in used_promos:
        await message.answer("❌ Вы уже использовали этот промокод!")
        return
    
    # Выдаем награды
    rewards = promo.get("rewards", {})
    update_data = {"$push": {"used_promocodes": code}}
    
    reward_text = f"🎉 Промокод <b>{code}</b> активирован!\n\n🎁 <b>Получено:</b>\n"
    
    for reward_type, amount in rewards.items():
        if reward_type == "money":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["money"] = amount
            reward_text += f"💰 {amount}$\n"
        elif reward_type == "sea_stars":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["sea_stars"] = amount
            reward_text += f"⭐ {amount} морских звёзд\n"
        elif reward_type == "cookies":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["cookies"] = amount
            reward_text += f"🍪 {amount} печенек\n"
        elif reward_type == "fish":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["fish"] = amount
            reward_text += f"🐟 {amount} рыбы\n"
    
    # Обновляем пользователя
    await users_collection.update_one({"user_id": user_id}, update_data)
    
    # Увеличиваем счетчик использований промокода
    await promocodes_collection.update_one(
        {"code": code},
        {"$inc": {"used_count": 1}}
    )
    
    await message.answer(reward_text, parse_mode="HTML")

# Альтернативный способ ввода промокода
@router.message(lambda message: message.text and len(message.text) <= 20 and message.text.isupper() and not message.text.startswith('/'))
async def check_promocode_text(message: Message):
    # Проверяем, может ли это быть промокодом
    code = message.text.strip()
    promo = await promocodes_collection.find_one({"code": code})
    
    if promo:
        # Перенаправляем на обработку промокода
        message.text = f"/promo {code}"
        await use_promocode(message)
