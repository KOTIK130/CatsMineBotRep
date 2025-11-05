# modules/donate/upgrade_multiplier.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import users_collection
from modules.donate.panel import show_donation_shop_menu

router = Router(name="upgrade_multiplier")

async def get_user_data(user_id: int) -> dict:
    """Получение данных пользователя из базы."""
    return await users_collection.find_one({"user_id": user_id})

def format_progress_bar(percentage: float, length: int = 20) -> str:
    percentage = max(0, min(100, percentage))
    filled = round(percentage / 100 * length)
    empty = length - filled
    return "[" + "▓" * filled + "░" * empty + f"] {percentage:.1f}%"

@router.message(F.text == "🍪 Купить множитель")
async def show_cookie_boosters(message: Message):
    user_id = message.from_user.id
    await send_cookie_booster_ui(user_id, message)

@router.callback_query(F.data == "buy_multiplier")
async def handle_buy_multiplier(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        await callback.answer("Вы не зарегистрированы. Напишите /start.", show_alert=True)
        return

    cookies = user_data.get("cookies", 0)
    ore_multiplier = user_data.get("ore_multiplier", 1.0)
    multiplier_level = user_data.get("multiplier_level", 0)
    required_cookies = (multiplier_level + 1) * 20

    if multiplier_level >= 5:
        await callback.answer("У вас уже максимальный множитель!", show_alert=True)
        return

    if cookies < required_cookies:
        await callback.answer("Недостаточно печенек!", show_alert=True)
        return

    new_ore_multiplier = round(ore_multiplier + 0.2, 1)

    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {"cookies": -required_cookies},
            "$set": {
                "ore_multiplier": new_ore_multiplier,
                "multiplier_level": multiplier_level + 1
            }
        }
    )

    await callback.answer("✅ Множитель улучшен!")
    await send_cookie_booster_ui(user_id, callback.message, edit=True)

async def send_cookie_booster_ui(user_id: int, target, edit=False):
    user_data = await get_user_data(user_id)

    if not user_data:
        if isinstance(target, Message):
            await target.answer("Вы не зарегистрированы. Напишите /start.")
        else:
            await target.answer("Вы не зарегистрированы. Напишите /start.", show_alert=True)
        return

    cookies = user_data.get("cookies", 0)
    ore_multiplier = user_data.get("ore_multiplier", 1.0)
    multiplier_level = user_data.get("multiplier_level", 0)

    required_cookies = (multiplier_level + 1) * 20

    text = (
        f"🍪 Ваш баланс: {cookies}\n\n"
        f"⚡ Множитель руды:\n"
        f"├ Текущий: {ore_multiplier:.1f}x\n"
        f"└ Уровень: {multiplier_level}/5\n\n"
    )

    # Прогресс-бар прокачки множителя
    progress_percentage = (multiplier_level / 5) * 100
    text += format_progress_bar(progress_percentage)

    kb = None

    if multiplier_level < 5:
        text += f"\n\n🔼 Следующий: {ore_multiplier + 0.2:.1f}x за {required_cookies}🍪"
        kb = InlineKeyboardBuilder()
        if cookies >= required_cookies:
            kb.button(text="Купить множитель", callback_data="buy_multiplier")
        else:
            kb.button(text="Недостаточно печенек", callback_data="no_cookies")

    markup = kb.as_markup() if kb else None

    if edit:
        await target.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)
