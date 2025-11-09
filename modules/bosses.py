# modules/bosses.py - Система боссов

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import users_collection, BOSS_RESPAWN_TIMES, DAILY_EVENTS
from datetime import datetime, timedelta
import random

router = Router(name="bosses")

BOSSES = {
    "pike": {
        "name": "🐟 Щука",
        "hp": 100,
        "min_level": 1,
        "rewards": {"money": (50, 150), "sea_stars": (2, 5), "materials": 2}
    },
    "shark": {
        "name": "🦈 Белая акула", 
        "hp": 250,
        "min_level": 5,
        "rewards": {"money": (100, 300), "sea_stars": (3, 8), "materials": 3}
    },
    "octopus": {
        "name": "🐙 Осьминог",
        "hp": 500,
        "min_level": 10,
        "rewards": {"money": (200, 500), "sea_stars": (5, 12), "materials": 4}
    },
    "whale": {
        "name": "🐋 Кит",
        "hp": 1000,
        "min_level": 15,
        "rewards": {"money": (400, 800), "sea_stars": (8, 15), "materials": 5}
    },
    "hunter": {
        "name": "🔱 Охотник на рыб",
        "hp": 2000,
        "min_level": 25,
        "rewards": {"money": (600, 1200), "sea_stars": (10, 20), "materials": 6}
    },
    "cthulhu": {
        "name": "🐙 Ктулху",
        "hp": 5000,
        "min_level": 35,
        "rewards": {"money": (1000, 2000), "sea_stars": (15, 30), "materials": 8}
    },
    "poseidon": {
        "name": "🔱 Посейдон",
        "hp": 10000,
        "min_level": 50,
        "rewards": {"money": (2000, 5000), "sea_stars": (25, 50), "materials": 10}
    }
}

@router.message(F.text == "🐉 Боссы")
async def show_bosses(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    rod_level = user.get("rod_level", 1)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    text = "🐉 <b>Морские боссы</b>\n\nВыберите босса для битвы:\n\n"
    
    for boss_id, boss_data in BOSSES.items():
        if rod_level >= boss_data["min_level"]:
            status = await get_boss_status(user_id, boss_id)
            button_text = f"{boss_data['name']} {status}"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=button_text, callback_data=f"boss:{boss_id}")
            ])
            text += f"{boss_data['name']} (мин. ур. {boss_data['min_level']}) - {status}\n"
        else:
            text += f"🔒 {boss_data['name']} (треб. ур. {boss_data['min_level']})\n"
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📋 Список боссов", callback_data="boss_list")
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text.startswith("/bl"))
async def boss_list_command(message: Message):
    await show_boss_timers(message)

async def show_boss_timers(message: Message):
    user_id = message.from_user.id
    text = "📋 <b>Статус боссов:</b>\n\n"
    
    for boss_id, boss_data in BOSSES.items():
        status = await get_boss_status(user_id, boss_id)
        text += f"{boss_data['name']} - {status}\n"
    
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("boss:"))
async def boss_battle(callback: CallbackQuery):
    user_id = callback.from_user.id
    boss_id = callback.data.split(":")[1]
    
    user = await users_collection.find_one({"user_id": user_id})
    boss_data = BOSSES[boss_id]
    
    # Проверяем доступность босса
    if user.get("rod_level", 1) < boss_data["min_level"]:
        await callback.answer("Недостаточный уровень удочки!")
        return
    
    # Проверяем респавн
    boss_battles = user.get("boss_battles", {})
    last_kill = boss_battles.get(f"{boss_id}_last_kill")
    
    if last_kill:
        respawn_time = BOSS_RESPAWN_TIMES[boss_id]
        time_passed = (datetime.utcnow() - last_kill).total_seconds()
        
        if time_passed < respawn_time:
            remaining = respawn_time - time_passed
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await callback.answer(f"Босс был убит. Респавн через {hours}ч {minutes}м")
            return
    
    # Начинаем битву
    current_hp = boss_battles.get(f"{boss_id}_hp", boss_data["hp"])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data=f"attack:{boss_id}")],
        [InlineKeyboardButton(text="⏳ Ждать", callback_data=f"wait:{boss_id}")],
        [InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_to_bosses")]
    ])
    
    text = (
        f"⚔️ <b>Битва с {boss_data['name']}</b>\n\n"
        f"❤️ HP: {current_hp}/{boss_data['hp']}\n"
        f"🎣 Ваш уровень: {user.get('rod_level', 1)}\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("attack:"))
async def attack_boss(callback: CallbackQuery):
    user_id = callback.from_user.id
    boss_id = callback.data.split(":")[1]
    
    user = await users_collection.find_one({"user_id": user_id})
    boss_data = BOSSES[boss_id]
    boss_battles = user.get("boss_battles", {})
    
    # Рассчитываем урон
    rod_level = user.get("rod_level", 1)
    base_damage = rod_level * random.randint(5, 15)
    
    # Проверяем дневной бонус
    today = datetime.now().weekday()
    if today in DAILY_EVENTS and DAILY_EVENTS[today]["bonus"] == "boss_drop_x2":
        base_damage = int(base_damage * 1.5)
    
    current_hp = boss_battles.get(f"{boss_id}_hp", boss_data["hp"])
    new_hp = max(0, current_hp - base_damage)
    
    # Обновляем HP босса
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {f"boss_battles.{boss_id}_hp": new_hp}}
    )
    
    if new_hp <= 0:
        # Босс побежден
        await boss_defeated(callback, boss_id, user)
    else:
        # Продолжаем битву
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Атаковать", callback_data=f"attack:{boss_id}")],
            [InlineKeyboardButton(text="⏳ Ждать", callback_data=f"wait:{boss_id}")],
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_to_bosses")]
        ])
        
        text = (
            f"⚔️ Урон: <b>{base_damage}</b>\n\n"
            f"⚔️ <b>Битва с {boss_data['name']}</b>\n\n"
            f"❤️ HP: {new_hp}/{boss_data['hp']}\n"
            f"🎣 Ваш уровень: {user.get('rod_level', 1)}\n\n"
            f"Выберите действие:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def boss_defeated(callback: CallbackQuery, boss_id: str, user: dict):
    """Обработка победы над боссом"""
    boss_data = BOSSES[boss_id]
    rod_level = user.get("rod_level", 1)
    
    # Генерируем награды
    money_reward = random.randint(*boss_data["rewards"]["money"]) * rod_level
    stars_reward = random.randint(*boss_data["rewards"]["sea_stars"])
    
    # Проверяем дневной бонус
    today = datetime.now().weekday()
    if today in DAILY_EVENTS and DAILY_EVENTS[today]["bonus"] == "boss_drop_x2":
        money_reward *= 2
        stars_reward *= 2
    
    # Выдаем награды
    await users_collection.update_one(
        {"user_id": callback.from_user.id},
        {
            "$inc": {
                "money": money_reward,
                "sea_stars": stars_reward
            },
            "$set": {
                f"boss_battles.{boss_id}_last_kill": datetime.utcnow(),
                f"boss_battles.{boss_id}_hp": boss_data["hp"]  # Сбрасываем HP
            }
        }
    )
    
    text = (
        f"🎉 <b>{boss_data['name']} побежден!</b>\n\n"
        f"🎁 <b>Награды:</b>\n"
        f"💰 {money_reward}$\n"
        f"⭐ {stars_reward} морских звёзд\n\n"
        f"⏰ Респавн через {BOSS_RESPAWN_TIMES[boss_id] // 3600} часов"
    )
    
    await callback.message.edit_text(text, parse_mode="HTML")

async def get_boss_status(user_id: int, boss_id: str) -> str:
    """Получить статус босса"""
    user = await users_collection.find_one({"user_id": user_id})
    boss_battles = user.get("boss_battles", {}) if user else {}
    
    last_kill = boss_battles.get(f"{boss_id}_last_kill")
    if not last_kill:
        return "🟢 Активен"
    
    respawn_time = BOSS_RESPAWN_TIMES[boss_id]
    time_passed = (datetime.utcnow() - last_kill).total_seconds()
    
    if time_passed >= respawn_time:
        return "🟢 Активен"
    else:
        remaining = respawn_time - time_passed
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"🔴 {hours}ч {minutes}м"

@router.callback_query(F.data == "back_to_bosses")
async def back_to_bosses(callback: CallbackQuery):
    await show_bosses(callback.message)

@router.callback_query(F.data == "boss_list")
async def boss_list_callback(callback: CallbackQuery):
    await show_boss_timers(callback.message)
    await callback.answer()
