# modules/cases.py - Система кейсов

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import users_collection, CASE_TYPES, MATERIALS
import random

router = Router(name="cases")

@router.message(F.text == "📦 Кейсы")
async def show_cases(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    cases = user.get("cases", {})
    total_cases = sum(cases.values())
    
    if total_cases == 0:
        await message.answer("📦 У вас нет кейсов. Ловите рыбу, чтобы найти их!")
        return

    text = "📦 <b>Ваши кейсы:</b>\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for case_type, data in CASE_TYPES.items():
        count = cases.get(case_type, 0)
        if count > 0:
            text += f"{data['name']}: <b>{count}</b> шт.\n"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"Открыть {data['name']} ({count})",
                    callback_data=f"open_case:{case_type}"
                )
            ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("open_case:"))
async def open_case(callback: CallbackQuery):
    user_id = callback.from_user.id
    case_type = callback.data.split(":")[1]
    
    user = await users_collection.find_one({"user_id": user_id})
    cases = user.get("cases", {})
    
    if cases.get(case_type, 0) <= 0:
        await callback.answer("У вас нет этого кейса!")
        return

    # Уменьшаем количество кейсов
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {f"cases.{case_type}": -1}}
    )

    # Определяем награду
    rewards = get_case_rewards(case_type, user.get("rod_level", 1))
    
    # Выдаем награды
    update_data = {}
    reward_text = f"📦 Открыт {CASE_TYPES[case_type]['name']}!\n\n🎁 <b>Награды:</b>\n"
    
    for reward_type, amount in rewards.items():
        if reward_type == "money":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["money"] = amount
            reward_text += f"💰 {amount}$\n"
        elif reward_type == "sea_stars":
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"]["sea_stars"] = amount
            reward_text += f"⭐ {amount} морских звёзд\n"
        elif reward_type in MATERIALS:
            update_data["$inc"] = update_data.get("$inc", {})
            update_data["$inc"][f"materials.{reward_type}"] = amount
            reward_text += f"{MATERIALS[reward_type]['emoji']} {amount} {MATERIALS[reward_type]['name']}\n"

    if update_data:
        await users_collection.update_one({"user_id": user_id}, update_data)

    await callback.message.edit_text(reward_text, parse_mode="HTML")
    await callback.answer("Кейс открыт!")

def get_case_rewards(case_type: str, rod_level: int) -> dict:
    """Генерирует награды для кейса"""
    rewards = {}
    
    if case_type == "can":
        rewards["money"] = random.randint(10, 50) * rod_level
        if random.randint(1, 100) <= 20:
            rewards["sea_stars"] = random.randint(1, 2)
    
    elif case_type == "chest":
        rewards["money"] = random.randint(50, 150) * rod_level
        rewards["sea_stars"] = random.randint(1, 3)
        if random.randint(1, 100) <= 30:
            material = random.choice(list(MATERIALS.keys()))
            rewards[material] = random.randint(1, 3)
    
    elif case_type == "star_box":
        rewards["sea_stars"] = random.randint(5, 15)
        rewards["money"] = random.randint(20, 80) * rod_level
    
    elif case_type == "material_bag":
        for material in MATERIALS.keys():
            if random.randint(1, 100) <= 60:
                rewards[material] = random.randint(2, 8)
        rewards["money"] = random.randint(30, 100) * rod_level
    
    elif case_type == "weapon_box":
        rewards["money"] = random.randint(100, 300) * rod_level
        rewards["sea_stars"] = random.randint(3, 8)
        for material in MATERIALS.keys():
            rewards[material] = random.randint(1, 5)
    
    elif case_type == "legendary_safe":
        rewards["money"] = random.randint(500, 1500) * rod_level
        rewards["sea_stars"] = random.randint(10, 25)
        for material in MATERIALS.keys():
            rewards[material] = random.randint(5, 15)
    
    return rewards
