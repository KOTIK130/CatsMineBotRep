from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import users_collection
from modules.keyboards import swamp_main_keyboard, workers_menu_keyboard

router = Router(name="workers")

WORKER_COST = 50_000
MAX_WORKERS = 10
WORKER_UPGRADE_COST = [0, 1, 2, 4, 6]  # индекс = уровень

@router.message(F.text == "👷 Работники")
async def show_workers_menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=workers_menu_keyboard())

@router.message(F.text == "👷 Мои работники")
async def my_workers(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    workers = user.get("workers", [])

    if not workers:
        await message.answer("У вас ещё нет рабочих.", reply_markup=workers_menu_keyboard())
        return

    text = "Ваши рабочие:\n\n"
    for i, worker in enumerate(workers, start=1):
        level = worker.get("level", 1)
        status = "⛏ Работает" if worker.get("working", False) else "🛌 Отдыхает"
        text += f"👷 Рабочий {i}: Уровень {level} — {status}\n"

    await message.answer(text, reply_markup=workers_menu_keyboard())

@router.message(F.text == "🤝 Принять сотрудника")
async def hire_worker(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    workers = user.get("workers", [])
    money = user.get("money", 0)

    if len(workers) >= MAX_WORKERS:
        await message.answer("Вы уже наняли максимум рабочих.", reply_markup=workers_menu_keyboard())
        return

    if money < WORKER_COST:
        await message.answer(f"Недостаточно средств. Нужно {WORKER_COST:,}$", reply_markup=workers_menu_keyboard())
        return

    await users_collection.update_one(
        {"user_id": message.from_user.id},
        {
            "$inc": {"money": -WORKER_COST},
            "$push": {"workers": {"level": 1, "working": False}}
        }
    )
    await message.answer("Новый сотрудник принят на работу!", reply_markup=workers_menu_keyboard())

@router.message(F.text == "⚙️ Обучить рабочего")
async def upgrade_worker_menu(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})
    workers = user.get("workers", [])
    cookies = user.get("cookies", 0)

    if not workers:
        await message.answer("У вас нет рабочих.", reply_markup=workers_menu_keyboard())
        return

    text = "Выберите рабочего для обучения:\n"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[])

    for i, w in enumerate(workers):
        level = w.get("level", 1)
        if level >= 5:
            btn_text = f"✅ Рабочий {i+1} — макс. уровень"
        else:
            cost = WORKER_UPGRADE_COST[level]
            btn_text = f"⚙️ Рабочий {i+1} — {cost} 🍪"

        inline_kb.inline_keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"upgrade_worker:{i}")
        ])

    await message.answer(text, reply_markup=inline_kb)

@router.callback_query(F.data.startswith("upgrade_worker:"))
async def handle_worker_upgrade(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    user = await users_collection.find_one({"user_id": callback.from_user.id})
    workers = user.get("workers", [])
    cookies = user.get("cookies", 0)

    if index >= len(workers):
        await callback.answer("Рабочий не найден.")
        return

    worker = workers[index]
    level = worker.get("level", 1)

    if level >= 5:
        await callback.answer("Уже максимальный уровень.")
        return

    cost = WORKER_UPGRADE_COST[level]
    if cookies < cost:
        await callback.answer("Недостаточно печенек.")
        return

    workers[index]["level"] += 1
    await users_collection.update_one(
        {"user_id": callback.from_user.id},
        {
            "$inc": {"cookies": -cost},
            "$set": {"workers": workers}
        }
    )
    await callback.message.answer(f"👷 Рабочий {index+1} улучшен до уровня {level + 1} за {cost} 🍪", reply_markup=workers_menu_keyboard())
    await callback.answer()

@router.message(F.text == "◀️ В болото")
async def back_to_swamp(message: Message):
    await message.answer("Вы вернулись в болото.", reply_markup=swamp_main_keyboard())
