from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from modules.keyboards import main_menu_keyboard

router = Router(name="donate_panel")

# Главное меню донат-магазина
@router.message(F.text == "🛍️ Донат магазин")
async def show_donation_shop_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍪 Купить множитель"), KeyboardButton(text="⭐ Telegram Звёзды")],
            [KeyboardButton(text="🛠 Авто-клик"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в донат-магазин!", reply_markup=kb)

# Назад в главное меню игры
@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await message.answer(text="↩️ Главное меню", reply_markup=main_menu_keyboard())

# Обработчик для кнопки "⭐ Telegram Звёзды"
@router.message(F.text == "⭐ Telegram Звёзды")
async def show_telegram_stars(message: Message):
    from modules.donate.replenish_balance import show_donate_menu
    await show_donate_menu(message)
