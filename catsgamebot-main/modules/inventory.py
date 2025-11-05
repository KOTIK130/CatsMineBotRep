# modules/inventory.py - Переделанный инвентарь для рыбалки
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import users_collection, MATERIALS
from utils import format_value
from modules.keyboards import main_menu_keyboard
from datetime import datetime

router = Router(name="inventory")

def inventory_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Продать рыбу"), KeyboardButton(text="📦 Мои кейсы")],
            [KeyboardButton(text="🛠 Материалы"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🎒 Инвентарь")
async def inventory_handler(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    fish_inventory = user.get("fish_inventory", {})
    money = user.get("money", 0)
    sea_stars = user.get("sea_stars", 0)
    cookies = user.get("cookies", 0)

    # Подсчитываем общую стоимость рыбы
    from config import FISH_TYPES, RARITY_COLORS
    total_fish_count = 0
    total_fish_value = 0
    
    fish_text = ""
    for fish_type, amount in fish_inventory.items():
        if amount > 0 and fish_type in FISH_TYPES:
            fish_data = FISH_TYPES[fish_type]
            value = amount * fish_data["price"]
            total_fish_count += amount
            total_fish_value += value
            
            rarity_color = RARITY_COLORS.get(fish_data["rarity"], "⚪")
            fish_text += f"{rarity_color} {fish_data['emoji']} {amount}x ({value}$)\n"

    if not fish_text:
        fish_text = "Нет рыбы"

    # Проверяем активные бустеры
    boosters = user.get("boosters", {})
    active_boosters = []
    
    fish_booster = boosters.get("fish_x2_end")
    if fish_booster and fish_booster > datetime.utcnow():
        remaining = (fish_booster - datetime.utcnow()).total_seconds() / 3600
        active_boosters.append(f"🐟 х2 Рыба ({remaining:.1f}ч)")
    
    star_booster = boosters.get("star_x2_end")
    if star_booster and star_booster > datetime.utcnow():
        remaining = (star_booster - datetime.utcnow()).total_seconds() / 60
        active_boosters.append(f"⭐ х2 Звёзды ({remaining:.0f}м)")

    booster_text = "\n".join(active_boosters) if active_boosters else "Нет активных бустеров"

    text = (
        f"🎒 <b>Инвентарь рыбака</b>\n\n"
        f"🐟 <b>Рыба ({total_fish_count} шт.):</b>\n{fish_text}\n"
        f"💰 Общая стоимость рыбы: <b>{total_fish_value}$</b>\n"
        f"💰 Деньги: <b>{format_value(money)}$</b>\n"
        f"⭐ Морские звёзды: <b>{sea_stars}</b>\n"
        f"🍪 Печеньки: <b>{cookies}</b>\n\n"
        f"🚀 <b>Активные бустеры:</b>\n{booster_text}"
    )

    await message.answer(text, reply_markup=inventory_keyboard(), parse_mode="HTML")

@router.message(F.text == "💰 Продать рыбу")
async def sell_fish_handler(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    fish_inventory = user.get("fish_inventory", {})
    
    # Подсчитываем общую стоимость
    from config import FISH_TYPES
    total_earned = 0
    total_fish_sold = 0
    sale_details = []
    
    for fish_type, amount in fish_inventory.items():
        if amount > 0 and fish_type in FISH_TYPES:
            fish_data = FISH_TYPES[fish_type]
            fish_value = amount * fish_data["price"]
            total_earned += fish_value
            total_fish_sold += amount
            sale_details.append(f"{fish_data['emoji']} {amount}x = {fish_value}$")
    
    if total_fish_sold == 0:
        await message.answer("❌ Нет рыбы для продажи!", reply_markup=inventory_keyboard())
        return

    # Подсчёт бонуса от рабочих
    workers = user.get("workers", [])
    total_workers = len(workers)
    bonus_multiplier = 1 + (total_workers * 0.05)  # 5% за каждого рабочего

    # Проверяем дневной бонус
    from config import DAILY_EVENTS
    today = datetime.now().weekday()
    daily_bonus = 1.0
    if today in DAILY_EVENTS and DAILY_EVENTS[today]["bonus"] == "sell_x2":
        daily_bonus = 2.0

    final_earned = int(total_earned * bonus_multiplier * daily_bonus)

    # Очищаем инвентарь рыбы и добавляем деньги
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"fish_inventory": {}},
            "$inc": {"money": final_earned}
        }
    )

    # Формируем детальный отчет
    details_text = "\n".join(sale_details[:5])  # Показываем первые 5 типов
    if len(sale_details) > 5:
        details_text += f"\n... и ещё {len(sale_details) - 5} типов"

    bonus_text = ""
    if daily_bonus > 1:
        bonus_text += f"\n🌟 Дневной бонус: x{daily_bonus}"
    if total_workers > 0:
        bonus_text += f"\n👷 Бонус от рабочих: x{bonus_multiplier:.2f}"

    await message.answer(
        f"💰 <b>Продажа завершена!</b>\n\n"
        f"🐟 Продано рыбы: <b>{total_fish_sold}</b> шт.\n"
        f"💵 Базовая стоимость: <b>{total_earned}$</b>\n"
        f"💰 Получено с бонусами: <b>{final_earned}$</b>{bonus_text}\n\n"
        f"📋 <b>Детали продажи:</b>\n{details_text}",
        reply_markup=inventory_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📦 Мои кейсы")
async def show_my_cases(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    from config import CASE_TYPES
    cases = user.get("cases", {})
    total_cases = sum(cases.values())
    
    if total_cases == 0:
        await message.answer("📦 У вас нет кейсов.", reply_markup=inventory_keyboard())
        return

    text = "📦 <b>Ваши кейсы:</b>\n\n"
    for case_type, data in CASE_TYPES.items():
        count = cases.get(case_type, 0)
        if count > 0:
            text += f"{data['name']}: <b>{count}</b> шт.\n"

    text += f"\n📊 Всего кейсов: <b>{total_cases}</b>"
    await message.answer(text, reply_markup=inventory_keyboard(), parse_mode="HTML")

@router.message(F.text == "🛠 Материалы")
async def show_materials(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    materials = user.get("materials", {})
    text = "🛠 <b>Материалы:</b>\n\n"
    
    total_materials = 0
    for material_id, material_data in MATERIALS.items():
        count = materials.get(material_id, 0)
        text += f"{material_data['emoji']} {material_data['name']}: <b>{count}</b>\n"
        total_materials += count

    if total_materials == 0:
        text += "\nУ вас нет материалов."
    
    await message.answer(text, reply_markup=inventory_keyboard(), parse_mode="HTML")

@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())
