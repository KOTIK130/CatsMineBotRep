# modules/upgrades.py - Система улучшений

import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from decimal import Decimal, getcontext
from config import users_collection
from modules.keyboards import main_menu_keyboard
from datetime import datetime, timedelta

getcontext().prec = 28

router = Router(name="upgrades")

@router.message(F.text == "⚡ Улучшения")
async def show_upgrades_menu(message: Message):
    from modules.keyboards import upgrades_keyboard
    await message.answer("⚡ Выберите тип улучшения:", reply_markup=upgrades_keyboard())

@router.message(F.text == "🎣 Улучшить удочку")
async def show_rod_upgrade(message: Message):
    user_data = await get_user_data(message.from_user.id)
    await send_rod_upgrade_ui(user_data, message)

@router.message(F.text == "⭐ Шанс звёзд")
async def show_star_chance_upgrade(message: Message):
    user_data = await get_user_data(message.from_user.id)
    await send_star_chance_ui(user_data, message)

@router.message(F.text == "🍀 Удача на х2")
async def show_luck_upgrade(message: Message):
    user_data = await get_user_data(message.from_user.id)
    await send_luck_ui(user_data, message)

@router.message(F.text == "🚀 Бустеры")
async def show_boosters(message: Message):
    user_data = await get_user_data(message.from_user.id)
    await send_boosters_ui(user_data, message)

# ===== ПРОКАЧКА УДОЧКИ =====
async def send_rod_upgrade_ui(user_data: dict, target, edit=False):
    level = user_data["rod_level"]
    money = user_data["money"]
    
    # Новая сложная формула прокачки
    if level < 60:
        if level <= 10:
            cost = 100 * (level ** 2)
        elif level <= 30:
            cost = 1000 * (level ** 1.5)
        else:
            cost = 10000 * (level ** 1.2)
        
        cost = int(cost)
        
        text = (
            f"🎣 <b>Улучшение удочки</b>\n\n"
            f"🔧 Текущий уровень: <b>{level}/60</b>\n"
            f"💰 Стоимость улучшения: <b>{cost:,}$</b>\n"
            f"💰 Ваши деньги: <b>{money:,}$</b>\n\n"
            f"📈 Улов за тап: <b>{2**(level-1):,}</b> → <b>{2**level:,}</b>\n"
        )
        
        if level == 60:
            text += "\n🎉 Максимальный уровень достигнут!"
        
        kb = InlineKeyboardBuilder()
        if money >= cost and level < 60:
            kb.button(text="⬆️ Улучшить", callback_data="upgrade_rod")
        elif level < 60:
            kb.button(text="❌ Недостаточно денег", callback_data="no_money")
        
        markup = kb.as_markup() if kb.buttons else None
    else:
        # Система престижа для 60+ уровня
        prestige_level = user_data.get("prestige_level", 0)
        cookies_reward = 3 + (prestige_level * 2)  # 3, 5, 7, 9...
        next_target = 60 + (prestige_level * 5)    # 60, 65, 70, 75...
        
        if level >= next_target:
            text = (
                f"🎉 <b>Престиж доступен!</b>\n\n"
                f"🎣 Уровень удочки: <b>{level}</b>\n"
                f"🏆 Престиж: <b>{prestige_level}</b>\n\n"
                f"🍪 Награда: <b>{cookies_reward}</b> печенек\n"
                f"🔄 Следующий престиж на <b>{next_target + 5}</b> уровне\n\n"
                f"⚠️ Удочка сбросится до 1 уровня!"
            )
            
            kb = InlineKeyboardBuilder()
            kb.button(text="🎁 Получить престиж", callback_data="take_prestige")
            markup = kb.as_markup()
        else:
            text = (
                f"🎣 <b>Удочка максимального уровня</b>\n\n"
                f"🔧 Уровень: <b>{level}/60</b>\n"
                f"🏆 Престиж: <b>{prestige_level}</b>\n\n"
                f"🎯 До следующего престижа: <b>{next_target - level}</b> уровней\n"
                f"🍪 Награда за престиж: <b>{cookies_reward}</b> печенек"
            )
            markup = None

    if edit:
        await target.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "upgrade_rod")
async def upgrade_rod_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    level = user["rod_level"]
    money = user["money"]
    
    if level >= 60:
        await callback.answer("Удочка уже максимального уровня!")
        return
    
    # Рассчитываем стоимость
    if level <= 10:
        cost = 100 * (level ** 2)
    elif level <= 30:
        cost = 1000 * (level ** 1.5)
    else:
        cost = 10000 * (level ** 1.2)
    
    cost = int(cost)
    
    if money < cost:
        await callback.answer("Недостаточно денег!")
        return
    
    # Улучшаем удочку
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "rod_level": 1,
                "money": -cost
            }
        }
    )
    
    await callback.answer(f"Удочка улучшена до {level + 1} уровня!")
    updated_user = await get_user_data(user_id)
    await send_rod_upgrade_ui(updated_user, callback.message, edit=True)

@router.callback_query(F.data == "take_prestige")
async def take_prestige_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    prestige_level = user.get("prestige_level", 0)
    cookies_reward = 3 + (prestige_level * 2)
    
    # Выдаем престиж
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "cookies": cookies_reward,
                "prestige_level": 1
            },
            "$set": {
                "rod_level": 1,
                "money": 0,
                "fish": 0
            }
        }
    )
    
    await callback.answer(f"Престиж получен! +{cookies_reward} печенек!")
    updated_user = await get_user_data(user_id)
    await send_rod_upgrade_ui(updated_user, callback.message, edit=True)

# ===== ШАНС МОРСКИХ ЗВЁЗД =====
async def send_star_chance_ui(user_data: dict, target, edit=False):
    star_chance = user_data.get("star_chance", 5.0)
    money = user_data["money"]
    
    # Максимум 50%
    if star_chance < 50:
        cost = int(1000 * (star_chance ** 1.5))
        next_chance = min(star_chance + 1, 50)
        
        text = (
            f"⭐ <b>Шанс морских звёзд</b>\n\n"
            f"🎯 Текущий шанс: <b>{star_chance}%</b>\n"
            f"💰 Стоимость улучшения: <b>{cost:,}$</b>\n"
            f"💰 Ваши деньги: <b>{money:,}$</b>\n\n"
            f"📈 Новый шанс: <b>{next_chance}%</b>"
        )
        
        kb = InlineKeyboardBuilder()
        if money >= cost:
            kb.button(text="⬆️ Улучшить", callback_data="upgrade_star_chance")
        else:
            kb.button(text="❌ Недостаточно денег", callback_data="no_money")
        
        markup = kb.as_markup()
    else:
        text = (
            f"⭐ <b>Шанс морских звёзд</b>\n\n"
            f"🎯 Шанс: <b>{star_chance}%</b>\n\n"
            f"🎉 Максимальный шанс достигнут!"
        )
        markup = None

    if edit:
        await target.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "upgrade_star_chance")
async def upgrade_star_chance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    star_chance = user.get("star_chance", 5.0)
    money = user["money"]
    
    if star_chance >= 50:
        await callback.answer("Максимальный шанс достигнут!")
        return
    
    cost = int(1000 * (star_chance ** 1.5))
    
    if money < cost:
        await callback.answer("Недостаточно денег!")
        return
    
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "star_chance": 1,
                "money": -cost
            }
        }
    )
    
    await callback.answer("Шанс морских звёзд увеличен!")
    updated_user = await get_user_data(user_id)
    await send_star_chance_ui(updated_user, callback.message, edit=True)

# ===== УДАЧА НА Х2 =====
async def send_luck_ui(user_data: dict, target, edit=False):
    luck_x2 = user_data.get("luck_x2", 10.0)
    money = user_data["money"]
    
    if luck_x2 < 75:
        cost = int(2000 * (luck_x2 ** 1.3))
        next_luck = min(luck_x2 + 1, 75)
        
        text = (
            f"🍀 <b>Удача на х2 улов</b>\n\n"
            f"🎯 Текущая удача: <b>{luck_x2}%</b>\n"
            f"💰 Стоимость улучшения: <b>{cost:,}$</b>\n"
            f"💰 Ваши деньги: <b>{money:,}$</b>\n\n"
            f"📈 Новая удача: <b>{next_luck}%</b>"
        )
        
        kb = InlineKeyboardBuilder()
        if money >= cost:
            kb.button(text="⬆️ Улучшить", callback_data="upgrade_luck")
        else:
            kb.button(text="❌ Недостаточно денег", callback_data="no_money")
        
        markup = kb.as_markup()
    else:
        text = (
            f"🍀 <b>Удача на х2 улов</b>\n\n"
            f"🎯 Удача: <b>{luck_x2}%</b>\n\n"
            f"🎉 Максимальная удача достигнута!"
        )
        markup = None

    if edit:
        await target.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "upgrade_luck")
async def upgrade_luck_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    luck_x2 = user.get("luck_x2", 10.0)
    money = user["money"]
    
    if luck_x2 >= 75:
        await callback.answer("Максимальная удача достигнута!")
        return
    
    cost = int(2000 * (luck_x2 ** 1.3))
    
    if money < cost:
        await callback.answer("Недостаточно денег!")
        return
    
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "luck_x2": 1,
                "money": -cost
            }
        }
    )
    
    await callback.answer("Удача увеличена!")
    updated_user = await get_user_data(user_id)
    await send_luck_ui(updated_user, callback.message, edit=True)

# ===== БУСТЕРЫ =====
async def send_boosters_ui(user_data: dict, target, edit=False):
    boosters = user_data.get("boosters", {})
    sea_stars = user_data.get("sea_stars", 0)
    
    text = (
        f"🚀 <b>Бустеры</b>\n\n"
        f"⭐ Ваши морские звёзды: <b>{sea_stars}</b>\n\n"
        f"Доступные бустеры:\n"
    )
    
    kb = InlineKeyboardBuilder()
    
    # Бустер рыбы (х2 на 1 час)
    fish_booster = boosters.get("fish_x2_end")
    if not fish_booster or fish_booster < datetime.utcnow():
        text += "🐟 х2 Рыба (1 час) - 5⭐\n"
        if sea_stars >= 5:
            kb.button(text="🐟 Купить х2 Рыба", callback_data="buy_fish_booster")
    else:
        remaining = (fish_booster - datetime.utcnow()).total_seconds() / 3600
        text += f"🐟 х2 Рыба активен ({remaining:.1f}ч)\n"
    
    # Бустер звёзд (х2 на 30 мин)
    star_booster = boosters.get("star_x2_end")
    if not star_booster or star_booster < datetime.utcnow():
        text += "⭐ х2 Звёзды (30 мин) - 3⭐\n"
        if sea_stars >= 3:
            kb.button(text="⭐ Купить х2 Звёзды", callback_data="buy_star_booster")
    else:
        remaining = (star_booster - datetime.utcnow()).total_seconds() / 60
        text += f"⭐ х2 Звёзды активен ({remaining:.0f}м)\n"

    markup = kb.as_markup() if kb.buttons else None

    if edit:
        await target.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "buy_fish_booster")
async def buy_fish_booster(callback: CallbackQuery):
    from datetime import datetime, timedelta
    
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    if user.get("sea_stars", 0) < 5:
        await callback.answer("Недостаточно морских звёзд!")
        return
    
    end_time = datetime.utcnow() + timedelta(hours=1)
    
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {"sea_stars": -5},
            "$set": {"boosters.fish_x2_end": end_time}
        }
    )
    
    await callback.answer("Бустер х2 Рыба активирован на 1 час!")
    updated_user = await get_user_data(user_id)
    await send_boosters_ui(updated_user, callback.message, edit=True)

@router.callback_query(F.data == "buy_star_booster")
async def buy_star_booster(callback: CallbackQuery):
    from datetime import datetime, timedelta
    
    user_id = callback.from_user.id
    user = await get_user_data(user_id)
    
    if user.get("sea_stars", 0) < 3:
        await callback.answer("Недостаточно морских звёзд!")
        return
    
    end_time = datetime.utcnow() + timedelta(minutes=30)
    
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {"sea_stars": -3},
            "$set": {"boosters.star_x2_end": end_time}
        }
    )
    
    await callback.answer("Бустер х2 Звёзды активирован на 30 минут!")
    updated_user = await get_user_data(user_id)
    await send_boosters_ui(updated_user, callback.message, edit=True)



# ===== УТИЛИТЫ =====
async def get_user_data(user_id: int) -> dict:
    default_user = {
        "user_id": user_id,
        "rod_level": 1,
        "money": 0,
        "fish": 0,
        "total_fish_caught": 0,
        "sea_stars": 0,
        "cookies": 0,
        "fish_multiplier": 1.0,
        "star_chance": 5.0,
        "luck_x2": 10.0,
        "prestige_level": 0,
        "boosters": {},
        "banned": False,
    }

    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        await users_collection.insert_one(default_user)
        return default_user

    update = {k: v for k, v in default_user.items() if k not in user}
    if update:
        await users_collection.update_one({"user_id": user_id}, {"$set": update})
        user.update(update)

    return user
