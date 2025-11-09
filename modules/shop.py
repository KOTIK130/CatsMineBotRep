# modules/shop.py - Система магазинов
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import users_collection, MATERIALS
from modules.keyboards import main_menu_keyboard, shop_keyboard, daily_shop_keyboard
from datetime import datetime, timedelta
import random

router = Router(name="shop")

# Товары дневного магазина
DAILY_SHOP_STARS = {
    "fish_multiplier": {"name": "🐟 Множитель рыбы +0.1", "cost": 10, "effect": "fish_multiplier", "value": 0.1},
    "star_chance": {"name": "⭐ Шанс звёзд +1%", "cost": 15, "effect": "star_chance", "value": 1},
    "luck_boost": {"name": "🍀 Удача +2%", "cost": 20, "effect": "luck_x2", "value": 2},
    "materials_pack": {"name": "🛠 Набор материалов", "cost": 25, "effect": "materials", "value": "random"}
}

DAILY_SHOP_COOKIES = {
    "mega_multiplier": {"name": "🌟 Мега множитель +0.5", "cost": 5, "effect": "fish_multiplier", "value": 0.5},
    "super_luck": {"name": "🎰 Супер удача +5%", "cost": 8, "effect": "luck_x2", "value": 5},
    "star_rain": {"name": "🌠 Дождь звёзд +10%", "cost": 12, "effect": "star_chance", "value": 10},
    "premium_materials": {"name": "💎 Премиум материалы", "cost": 15, "effect": "materials", "value": "premium"}
}

@router.message(F.text == "🏪 Магазин")
async def show_shop_menu(message: Message):
    await message.answer("🏪 Добро пожаловать в магазин!", reply_markup=shop_keyboard())

@router.message(F.text == "🌅 Дневной магазин")
async def show_daily_shop(message: Message):
    await message.answer("🌅 Выберите валюту для покупок:", reply_markup=daily_shop_keyboard())

@router.message(F.text == "⭐ За морские звёзды")
async def show_star_shop(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    sea_stars = user.get("sea_stars", 0)
    text = f"⭐ <b>Магазин за морские звёзды</b>\n\n💰 Ваши звёзды: <b>{sea_stars}</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for item_id, item_data in DAILY_SHOP_STARS.items():
        text += f"{item_data['name']} - {item_data['cost']}⭐\n"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{item_data['name']} ({item_data['cost']}⭐)",
                callback_data=f"buy_star:{item_id}"
            )
        ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "🍪 За печеньки")
async def show_cookie_shop(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    cookies = user.get("cookies", 0)
    text = f"🍪 <b>Магазин за печеньки</b>\n\n🍪 Ваши печеньки: <b>{cookies}</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for item_id, item_data in DAILY_SHOP_COOKIES.items():
        text += f"{item_data['name']} - {item_data['cost']}🍪\n"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{item_data['name']} ({item_data['cost']}🍪)",
                callback_data=f"buy_cookie:{item_id}"
            )
        ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("buy_star:"))
async def buy_star_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split(":")[1]
    
    if item_id not in DAILY_SHOP_STARS:
        await callback.answer("Товар не найден!")
        return
    
    user = await users_collection.find_one({"user_id": user_id})
    item_data = DAILY_SHOP_STARS[item_id]
    
    if user.get("sea_stars", 0) < item_data["cost"]:
        await callback.answer("Недостаточно морских звёзд!")
        return
    
    # Применяем эффект
    update_data = {"$inc": {"sea_stars": -item_data["cost"]}}
    
    if item_data["effect"] == "materials":
        # Случайные материалы
        for material in MATERIALS.keys():
            amount = random.randint(3, 8)
            update_data["$inc"][f"materials.{material}"] = amount
    else:
        update_data["$inc"][item_data["effect"]] = item_data["value"]
    
    await users_collection.update_one({"user_id": user_id}, update_data)
    await callback.answer(f"Куплено: {item_data['name']}!")
    
    # Обновляем сообщение
    await show_star_shop(callback.message)

@router.callback_query(F.data.startswith("buy_cookie:"))
async def buy_cookie_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split(":")[1]
    
    if item_id not in DAILY_SHOP_COOKIES:
        await callback.answer("Товар не найден!")
        return
    
    user = await users_collection.find_one({"user_id": user_id})
    item_data = DAILY_SHOP_COOKIES[item_id]
    
    if user.get("cookies", 0) < item_data["cost"]:
        await callback.answer("Недостаточно печенек!")
        return
    
    # Применяем эффект
    update_data = {"$inc": {"cookies": -item_data["cost"]}}
    
    if item_data["effect"] == "materials":
        # Премиум материалы
        for material in MATERIALS.keys():
            amount = random.randint(10, 20)
            update_data["$inc"][f"materials.{material}"] = amount
    else:
        update_data["$inc"][item_data["effect"]] = item_data["value"]
    
    await users_collection.update_one({"user_id": user_id}, update_data)
    await callback.answer(f"Куплено: {item_data['name']}!")
    
    # Обновляем сообщение
    await show_cookie_shop(callback.message)

@router.message(F.text == "◀️ В магазин")
async def back_to_shop(message: Message):
    await message.answer("🏪 Магазин", reply_markup=shop_keyboard())

@router.message(F.text == "◀️ В меню")
async def back_to_main_menu(message: Message):
    await message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())
