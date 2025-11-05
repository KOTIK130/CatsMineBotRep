# modules/donate/replenish_balance.py - Обновленная система покупки за Telegram Stars

import json
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import bot, STARS, users_collection
from modules.keyboards import main_menu_keyboard
from datetime import datetime

router = Router(name="replenish_balance")

class TopUpError(Exception):
    pass

# Пакеты покупки звезд с бонусами
STAR_PACKAGES = {
    "1": {"stars": 1, "cookies": 5, "label": "⭐ Базовый", "description": "1 звезда = 5 печенек"},
    "3": {"stars": 3, "cookies": 18, "label": "⭐⭐⭐ Стандарт", "description": "3 звезды = 18 печенек (+20% бонус)"},
    "5": {"stars": 5, "cookies": 35, "label": "⭐⭐⭐⭐⭐ Премиум", "description": "5 звезд = 35 печенек (+40% бонус)"},
    "10": {"stars": 10, "cookies": 80, "label": "🌟 VIP", "description": "10 звезд = 80 печенек (+60% бонус)"}
}

async def get_user_data(user_id: int) -> dict:
    return await users_collection.find_one({"user_id": user_id})

# Меню покупки Telegram Звёзд
@router.message(F.text == "🎁 Донат")
async def donate_handler(message: Message):
    await show_donate_menu(message)

@router.message(F.text == "🎁 Донат")
async def show_donate_menu(message: Message):
    kb = InlineKeyboardBuilder()
    
    kb.button(text="⭐ Купить Telegram Stars", callback_data="show_stars_info")
    kb.button(text="🍪 Что дают печеньки?", callback_data="cookies_info")
    kb.button(text="🎁 Бонусы доната", callback_data="donate_bonuses")
    kb.adjust(1)
    
    await message.answer(
        "🎁 <b>Донат-система</b>\n\n"
        "Поддержите разработку бота и получите особые преимущества!\n\n"
        "• Покупайте Telegram Stars и получайте печеньки\n"
        "• Печеньки можно тратить на мощные улучшения\n"
        "• Донатеры получают эксклюзивные возможности\n\n"
        "Выберите опцию ниже:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "show_stars_info")
async def show_stars_info(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    
    for package_id, package in STAR_PACKAGES.items():
        kb.button(
            text=f"{package['label']} ({package_id}⭐)",
            callback_data=f"topup_{package_id}"
        )
    
    kb.button(text="🔙 Назад", callback_data="back_to_donate")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "⭐ <b>Пополнение баланса через Telegram Stars</b>\n\n"
        "Выберите пакет звезд для покупки:\n\n"
        "🔹 <b>Базовый:</b> 1⭐ = 5🍪\n"
        "🔹 <b>Стандарт:</b> 3⭐ = 18🍪 (+20%)\n"
        "🔹 <b>Премиум:</b> 5⭐ = 35🍪 (+40%)\n"
        "🔹 <b>VIP:</b> 10⭐ = 80🍪 (+60%)\n\n"
        "💡 Чем больше пакет, тем больше бонус!",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cookies_info")
async def show_cookies_info(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Купить Telegram Stars", callback_data="show_stars_info")
    kb.button(text="🔙 Назад", callback_data="back_to_donate")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "🍪 <b>Что дают печеньки?</b>\n\n"
        "Печеньки - это донат-валюта, которую можно потратить на:\n\n"
        "🔸 <b>Мощные множители рыбы</b> (+0.5 за раз)\n"
        "🔸 <b>Премиум бустеры</b> (х2 рыба, х2 звёзды)\n"
        "🔸 <b>Найм премиум рабочего</b> (+15% к продаже)\n"
        "🔸 <b>Элитные товары</b> в донат-магазине\n"
        "🔸 <b>Улучшение удочки</b> после престижа\n"
        "🔸 <b>Особые возможности</b> в болоте\n\n"
        "💡 Печеньки также можно получить через престиж удочки и промокоды!",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "donate_bonuses")
async def show_donate_bonuses(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Купить Telegram Stars", callback_data="show_stars_info")
    kb.button(text="🔙 Назад", callback_data="back_to_donate")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "🎁 <b>Бонусы доната</b>\n\n"
        "Игроки, поддержавшие бота, получают:\n\n"
        "🔹 <b>Премиум статус</b> в профиле\n"
        "🔹 <b>Доступ к VIP боссу</b> с особыми наградами\n"
        "🔹 <b>Эксклюзивные промокоды</b> в канале\n"
        "🔹 <b>Увеличенный лимит</b> построек в болоте\n"
        "🔹 <b>Особые предметы</b> для крафта\n"
        "🔹 <b>Приоритетная поддержка</b> от разработчиков\n\n"
        "💎 Поддержите разработку бота и получите все эти преимущества!",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_donate")
async def back_to_donate(callback: CallbackQuery):
    await show_donate_menu(callback.message)

# Отправка счёта на пополнение
async def send_topup_invoice(user_id: int, option: str):
    if option not in STAR_PACKAGES:
        raise TopUpError("Неверный выбор пакета звёзд.")

    package = STAR_PACKAGES[option]
    amount = int(option)
    
    title = "Пополнение баланса"
    description = f"{package['label']} - {package['description']}"

    payload = json.dumps({
        "user_id": user_id, 
        "amount": amount, 
        "currency": STARS, 
        "type": "topup",
        "package": option
    })
    
    prices = [LabeledPrice(label=f"{package['label']}", amount=amount)]  # Telegram Stars нельзя умножить так как в ней нету копеек.

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Telegram сам обрабатывает Stars
            currency="XTR",
            prices=prices,
            start_parameter="topup_balance",
            need_email=False
        )
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке счета: {e}")
        raise TopUpError(f"Не удалось создать счет: {e}")

@router.callback_query(F.data.startswith("topup_"))
async def topup_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    option = callback_query.data.split("_")[1]

    try:
        await send_topup_invoice(user_id, option)
        await callback_query.answer("Счет на оплату создан!", show_alert=True)
    except TopUpError as e:
        await callback_query.answer(f"Ошибка: {e}", show_alert=True)
        logging.error("Ошибка пополнения от %d: %s", user_id, e)

# Обработка предварительной проверки платежа
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    try:
        # Всегда подтверждаем предварительную проверку
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        logging.info(f"Pre-checkout query {pre_checkout_query.id} confirmed")
    except Exception as e:
        logging.error(f"Error in pre_checkout_query: {e}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, 
            ok=False,
            error_message="Произошла ошибка при обработке платежа. Пожалуйста, попробуйте позже."
        )

# Успешная оплата
async def process_successful_payment(user_id: int, amount: int, package_id: str):
    package = STAR_PACKAGES.get(str(amount), STAR_PACKAGES["1"])
    stars = amount
    cookies = package["cookies"]
    
    # Обновляем данные пользователя
    update_data = {
        "$inc": {
            "stars": stars,
            "cookies": cookies,
            "total_donated": stars  # Для статистики
        },
        "$set": {
            "is_donator": True,
            "last_donation": datetime.utcnow()
        }
    }
    
    # Если это первый донат, даем бонус
    user = await get_user_data(user_id)
    if not user.get("is_donator"):
        update_data["$inc"]["sea_stars"] = 10
        first_time_bonus = True
    else:
        first_time_bonus = False
    
    await users_collection.update_one({"user_id": user_id}, update_data, upsert=True)
    
    logging.info("✅ %d звёзд куплено пользователем %d (+%d печенек)", stars, user_id, cookies)
    
    return first_time_bonus

@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    try:
        payload = json.loads(payment_info.invoice_payload)
        stars_amount = payload.get("amount", payment_info.total_amount // 100)  # Переводим из копеек
        package_id = payload.get("package", str(stars_amount))
        
        first_time_bonus = await process_successful_payment(user_id, stars_amount, package_id)
        
        package = STAR_PACKAGES.get(package_id, STAR_PACKAGES["1"])
        cookies = package["cookies"]
        
        text = (
            f"✅ <b>Успешная оплата!</b>\n\n"
            f"🎁 Вы получили:\n"
            f"⭐ {stars_amount} Telegram Stars\n"
            f"🍪 {cookies} печенек\n"
        )
        
        if first_time_bonus:
            text += f"🌟 +10 морских звёзд (бонус за первый донат)\n"
        
        text += "\n💡 Спасибо за поддержку бота!"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="🛍️ Донат магазин", callback_data="open_donate_shop")
        kb.button(text="🎣 В меню", callback_data="back_to_main")
        
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Ошибка при обработке платежа: {e}")
        await message.answer("✅ Оплата прошла успешно! Награды выданы.")

@router.callback_query(F.data == "open_donate_shop")
async def open_donate_shop(callback: CallbackQuery):
    await callback.message.answer("🛍️ Донат магазин", reply_markup=main_menu_keyboard())
    await callback.message.delete()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())
    await callback.message.delete()
