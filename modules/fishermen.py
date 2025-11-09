from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import users_collection
from modules.keyboards import main_menu_keyboard, fishermen_menu_keyboard

router = Router(name="fishermen")

FISHERMAN_COST = 50_000
MAX_FISHERMEN = 10
FISHERMAN_UPGRADE_COST = [0, 1, 2, 4, 6]  # индекс = уровень

@router.message(F.text == "🎣 Рыбаки")
async def show_fishermen_menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=fishermen_menu_keyboard())

@router.message(F.text == "🎣 Мои рыбаки")
async def my_fishermen(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    fishermen = user.get("fishermen", [])

    if not fishermen:
        await message.answer("У вас ещё нет рыбаков.", reply_markup=fishermen_menu_keyboard())
        return

    text = "Ваши рыбаки:\n\n"
    for i, fisherman in enumerate(fishermen, start=1):
        level = fisherman.get("level", 1)
        status = "🎣 Работает" if fisherman.get("working", False) else "🛌 Отдыхает"
        text += f"🎣 Рыбак {i}: Уровень {level} — {status}\n"

    await message.answer(text, reply_markup=fishermen_menu_keyboard())

@router.message(F.text == "🤝 Нанять рыбака")
async def hire_fisherman(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    fishermen = user.get("fishermen", [])
    money = user.get("money", 0)

    if len(fishermen) >= MAX_FISHERMEN:
        await message.answer("Вы уже наняли максимум рыбаков.", reply_markup=fishermen_menu_keyboard())
        return

    if money < FISHERMAN_COST:
        await message.answer(f"Недостаточно средств. Нужно {FISHERMAN_COST:,}$", reply_markup=fishermen_menu_keyboard())
        return

    await users_collection.update_one(
        {"user_id": message.from_user.id},
        {
            "$inc": {"money": -FISHERMAN_COST},
            "$push": {"fishermen": {"level": 1, "working": False}}
        }
    )
    await message.answer("Новый рыбак принят на работу!", reply_markup=fishermen_menu_keyboard())

@router.message(F.text == "⚙️ Обучить рыбака")
async def upgrade_fisherman_menu(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    fishermen = user.get("fishermen", [])
    cookies = user.get("cookies", 0)

    if not fishermen:
        await message.answer("У вас нет рыбаков.", reply_markup=fishermen_menu_keyboard())
        return

    text = "Выберите рыбака для обучения:\n"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[])

    for i, f in enumerate(fishermen):
        level = f.get("level", 1)
        if level >= 5:
            btn_text = f"✅ Рыбак {i+1} — макс. уровень"
        else:
            cost = FISHERMAN_UPGRADE_COST[level]
            btn_text = f"⚙️ Рыбак {i+1} — {cost} 🍪"

        inline_kb.inline_keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"upgrade_fisherman:{i}")
        ])

    await message.answer(text, reply_markup=inline_kb)

@router.callback_query(F.data.startswith("upgrade_fisherman:"))
async def handle_fisherman_upgrade(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    user = await users_collection.find_one({"user_id": callback.from_user.id})
    fishermen = user.get("fishermen", [])
    cookies = user.get("cookies", 0)

    if index >= len(fishermen):
        await callback.answer("Рыбак не найден.")
        return

    fisherman = fishermen[index]
    level = fisherman.get("level", 1)

    if level >= 5:
        await callback.answer("Уже максимальный уровень.")
        return

    cost = FISHERMAN_UPGRADE_COST[level]
    if cookies < cost:
        await callback.answer("Недостаточно печенек.")
        return

    fishermen[index]["level"] += 1
    await users_collection.update_one(
        {"user_id": callback.from_user.id},
        {
            "$inc": {"cookies": -cost},
            "$set": {"fishermen": fishermen}
        }
    )
    await callback.message.answer(f"🎣 Рыбак {index+1} улучшен до уровня {level + 1} за {cost} 🍪", reply_markup=fishermen_menu_keyboard())
    await callback.answer()

@router.message(F.text == "◀️ В меню")
async def back_to_main_menu(message: Message):
    await message.answer("Вы вернулись в меню.", reply_markup=main_menu_keyboard())
