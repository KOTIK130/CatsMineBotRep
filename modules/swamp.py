# modules/swamp.py - Болото (бывший город)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import users_collection
from modules.keyboards import main_menu_keyboard, swamp_main_keyboard

router = Router(name="swamp")

@router.message(F.text == "🌊 Болото")
async def swamp_handler(message: Message):
    await message.answer(
        "🌊 <b>Добро пожаловать в Болото</b>\n\n"
        "Здесь вы можете строить постройки, нанимать рабочих и получать достижения!",
        reply_markup=swamp_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "🏗 Постройки")
async def show_buildings(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    buildings = user.get("buildings", [])
    sea_stars = user.get("sea_stars", 0)
    
    text = f"🏗 <b>Постройки в болоте</b>\n\n⭐ Морские звёзды: <b>{sea_stars}</b>\n\n"
    
    if not buildings:
        text += "У вас нет построек.\n\n"
    else:
        for i, building in enumerate(buildings, 1):
            level = building.get("level", 1)
            building_type = building.get("type", "hut")
            name = {"hut": "🏚 Хижина", "dock": "🛥 Причал", "tower": "🗼 Башня"}.get(building_type, "🏗 Постройка")
            text += f"{name} {i} - Уровень {level}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏚 Построить хижину (10⭐)", callback_data="build:hut:10")],
        [InlineKeyboardButton(text="🛥 Построить причал (25⭐)", callback_data="build:dock:25")],
        [InlineKeyboardButton(text="🗼 Построить башню (50⭐)", callback_data="build:tower:50")],
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("build:"))
async def build_structure(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, building_type, cost_str = callback.data.split(":")
    cost = int(cost_str)
    
    user = await users_collection.find_one({"user_id": user_id})
    sea_stars = user.get("sea_stars", 0)
    
    if sea_stars < cost:
        await callback.answer("Недостаточно морских звёзд!")
        return
    
    buildings = user.get("buildings", [])
    if len(buildings) >= 5:
        await callback.answer("Максимум 5 построек!")
        return
    
    # Строим
    new_building = {"type": building_type, "level": 1}
    
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {"sea_stars": -cost},
            "$push": {"buildings": new_building}
        }
    )
    
    building_names = {"hut": "Хижина", "dock": "Причал", "tower": "Башня"}
    await callback.answer(f"{building_names[building_type]} построена!")
    
    # Обновляем сообщение
    await show_buildings(callback.message)

@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("Сначала напиши /start.")
        return

    achievements = user.get("achievements", [])
    total_fish = user.get("total_fish_caught", 0)
    rod_level = user.get("rod_level", 1)
    
    # Список всех достижений
    all_achievements = {
        "first_fish": {"name": "🐟 Первая рыба", "desc": "Поймать первую рыбу", "reward": "100$"},
        "fish_100": {"name": "🎣 Рыбак", "desc": "Поймать 100 рыб", "reward": "1,000$"},
        "fish_1000": {"name": "🏆 Мастер рыбалки", "desc": "Поймать 1,000 рыб", "reward": "5⭐"},
        "rod_10": {"name": "⚡ Улучшенная удочка", "desc": "Достичь 10 уровня удочки", "reward": "2⭐"},
        "rod_30": {"name": "🌟 Мастерская удочка", "desc": "Достичь 30 уровня удочки", "reward": "10⭐"},
        "first_boss": {"name": "⚔️ Первая победа", "desc": "Победить первого босса", "reward": "3⭐"},
    }
    
    text = "🏆 <b>Достижения</b>\n\n"
    
    for ach_id, ach_data in all_achievements.items():
        if ach_id in achievements:
            text += f"✅ {ach_data['name']} - {ach_data['desc']}\n"
        else:
            # Проверяем условия
            can_claim = False
            if ach_id == "first_fish" and total_fish >= 1:
                can_claim = True
            elif ach_id == "fish_100" and total_fish >= 100:
                can_claim = True
            elif ach_id == "fish_1000" and total_fish >= 1000:
                can_claim = True
            elif ach_id == "rod_10" and rod_level >= 10:
                can_claim = True
            elif ach_id == "rod_30" and rod_level >= 30:
                can_claim = True
            
            if can_claim:
                text += f"🎁 {ach_data['name']} - ГОТОВО К ПОЛУЧЕНИЮ!\n"
            else:
                text += f"🔒 {ach_data['name']} - {ach_data['desc']}\n"
    
    text += f"\n📊 Получено: {len(achievements)}/{len(all_achievements)}"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "◀️ В меню")
async def back_to_main_menu(message: Message):
    await message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())
