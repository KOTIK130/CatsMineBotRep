import asyncio
from datetime import datetime
from decimal import Decimal, getcontext

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.donate.panel import show_donation_shop_menu
from config import users_collection
from utils import format_progress_bar, get_user_data

getcontext().prec = 28

router = Router(name="autoclicker")

# ===== НАСТРОЙКИ =====
BASE_INTERVAL = 60
LEVEL_REDUCTION = 5
MAX_AUTOCLICKER_LEVEL = 10

# ===== АВТО-КЛИК =====
async def auto_click_task(user_id: int):
    while True:
        user = await get_user_data(user_id)
        if not user or not user.get("autoclicker_active"):
            break

        pickaxe_level = user.get("pickaxe_level", 1)
        ore_multiplier = Decimal(str(user.get("ore_multiplier", 1.0)))
        autoclicker_level = user.get("autoclicker_level", 0)

        base_ore = Decimal("1.0") + (Decimal(pickaxe_level - 1) * Decimal("0.50"))
        ore_mined = (base_ore * ore_multiplier).quantize(Decimal("1"))

        await users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "ore": float(ore_mined),
                    "total_ore_mined": float(ore_mined)
                },
                "$set": {"last_autoclick_time": datetime.utcnow()}
            }
        )

        interval = max(BASE_INTERVAL - autoclicker_level * LEVEL_REDUCTION, 5)
        await asyncio.sleep(interval)

# ===== ХЭНДЛЕРЫ =====
@router.message(F.text == "🛠 Авто-клик")
async def show_autoclicker_panel(message: Message):
    user_id = message.from_user.id
    await send_autoclicker_ui(user_id, message)

@router.callback_query(F.data == "upgrade_autoclicker")
async def upgrade_autoclicker_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)

    if not user:
        await callback.answer("Вы не зарегистрированы.", show_alert=True)
        return

    cookies = user.get("cookies", 0)
    autoclicker_level = user.get("autoclicker_level", 0)

    if autoclicker_level >= MAX_AUTOCLICKER_LEVEL:
        await callback.answer("Авто-кликер уже максимального уровня!", show_alert=True)
        return

    upgrade_cost = (autoclicker_level + 1) * 10

    if cookies < upgrade_cost:
        await callback.answer(f"Недостаточно печенек! Нужно {upgrade_cost}🍪", show_alert=True)
        return

    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "autoclicker_level": 1,
                "cookies": -upgrade_cost
            }
        }
    )

    await callback.answer("✅ Авто-кликер улучшен!")
    await send_autoclicker_ui(user_id, callback.message, edit=True)

@router.callback_query(F.data == "toggle_autoclicker")
async def toggle_autoclicker_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user_data(user_id)

    if not user:
        await callback.answer("Вы не зарегистрированы.", show_alert=True)
        return

    autoclicker_active = user.get("autoclicker_active", False)
    new_state = not autoclicker_active

    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"autoclicker_active": new_state}}
    )

    if new_state:
        asyncio.create_task(auto_click_task(user_id))
        await callback.answer("✅ Авто-клик включён!")
    else:
        await callback.answer("❌ Авто-клик выключен!")

    await send_autoclicker_ui(user_id, callback.message, edit=True)

@router.message(F.text == "🔄 Вкл/Выкл")
async def toggle_autoclicker_text_handler(message: Message):
    user_id = message.from_user.id
    user = await get_user_data(user_id)

    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start.")
        return

    autoclicker_active = user.get("autoclicker_active", False)
    new_state = not autoclicker_active

    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"autoclicker_active": new_state}}
    )

    if new_state:
        asyncio.create_task(auto_click_task(user_id))
        await message.answer("✅ Авто-клик включён!")
    else:
        await message.answer("❌ Авто-клик выключен!")

    await send_autoclicker_ui(user_id, message)

# ===== ОТПРАВКА ИНТЕРФЕЙСА =====
async def send_autoclicker_ui(user_id: int, target, edit=False):
    user = await get_user_data(user_id)

    if not user:
        if isinstance(target, Message):
            await target.answer("Вы не зарегистрированы. Напишите /start.")
        elif isinstance(target, CallbackQuery):
            await target.answer("Вы не зарегистрированы.", show_alert=True)
        return

    autoclicker_level = user.get("autoclicker_level", 0)
    autoclicker_active = user.get("autoclicker_active", False)
    cookies = user.get("cookies", 0)

    upgrade_cost = (autoclicker_level + 1) * 10
    current_interval = max(BASE_INTERVAL - autoclicker_level * LEVEL_REDUCTION, 5)

    text = (
        f"🛠 <b>Авто-кликер</b>\n\n"
        f"🍪 Ваши печеньки: <b>{cookies}</b>\n"
        f"⚡ Уровень авто-клика: <b>{autoclicker_level}/{MAX_AUTOCLICKER_LEVEL}</b>\n"
        f"⏳ Интервал копки: <b>{current_interval} секунд</b>\n\n"
    )

    progress_percentage = (autoclicker_level / MAX_AUTOCLICKER_LEVEL) * 100
    text += format_progress_bar(progress_percentage)

    if autoclicker_level < MAX_AUTOCLICKER_LEVEL:
        text += f"\n\n🔼 Улучшить за {upgrade_cost}🍪"
    else:
        text += "\n\n✅ Максимальный уровень авто-кликера!"

    text += f"\n\n🔘 Статус: {'Включён' if autoclicker_active else 'Выключен'}"

    builder = InlineKeyboardBuilder()

    if autoclicker_level < MAX_AUTOCLICKER_LEVEL:
        builder.button(text="⚙️ Улучшить", callback_data="upgrade_autoclicker")

    builder.button(text="🔄 Вкл/Выкл", callback_data="toggle_autoclicker")

    markup = builder.as_markup()

    if edit:
        await target.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)
