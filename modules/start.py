# modules/start.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import users_collection, logger, SUPPORT_CHAT_URL, UPDATES_CHANNEL_URL, MAINTENANCE_MODE, OWNER_ID
from datetime import datetime
from modules.keyboards import main_menu_keyboard
from modules.nick import get_nickname

router = Router(name="start")

@router.message(F.text == "/start")
async def send_welcome(message: Message):
    user_id = message.from_user.id
    
    # Проверка режима тех.работ
    if MAINTENANCE_MODE and user_id != OWNER_ID:
        await message.answer("🔧 Бот находится на техническом обслуживании. Попробуйте позже.")
        return
    
    default_name = message.from_user.first_name

    # Получаем никнейм
    nickname = await get_nickname(user_id)
    name_to_display = nickname if nickname != f"Игрок {user_id}" else default_name

    # Новое приветствие для рыбалки с улучшенным дизайном
    # text = (
    #     f"🌊 <b>Добро пожаловать в Рыбацкий Рай, {name_to_display}!</b> 🌊\n"
    #     f"━━━━━━━━━━━━━━━━━━━━\n\n"
    #     f"🎣 <b>Основные команды:</b>\n"
    #     f"┣ 🎣 <b>Рыбачить</b> — ловля рыбы (0.8 сек)\n"
    #     f"┣ 🎒 <b>Инвентарь</b> — ваши ресурсы и улов\n"
    #     f"┣ 💰 <b>Продать</b> — 1 рыба = 1$ + бонусы\n"
    #     f"┣ ⚡ <b>Улучшения</b> — прокачка удочки и навыков\n"
    #     f"┣ 👤 <b>Профиль</b> — ваш прогресс и статистика\n"
    #     f"┣ 🐉 <b>Боссы</b> — сражения с морскими чудовищами\n"
    #     f"┣ ⛵ <b>Гильдии</b> — объединяйтесь с другими рыбаками\n"
    #     f"┣ 🌊 <b>Болото</b> — ст��ойте и развивайтесь\n"
    #     f"┣ 🏪 <b>Магазин</b> — покупки за разные валюты\n"
    #     f"┣ 📦 <b>Кейсы</b> — открывайте сундуки с наградами\n"
    #     f"┗ 🎁 <b>Донат</b> — особые улучшения за печеньки\n\n"
    #     f"💎 <b>Валюты игры:</b>\n"
    #     f"┣ 💰 Деньги — основная валюта\n"
    #     f"┣ ⭐ Морские звёзды — редкая валюта\n"
    #     f"┗ 🍪 Печеньки — донат валюта\n\n"
    #     f"🛠️ <b>Полезные команды:</b>\n"
    #     f"┣ 📊 <b>/nick</b> — изменить ник\n"
    #     f"┣ 📋 <b>/guide</b> — подробный гайд\n"
    #     f"┣ 🐛 <b>/report</b> — сообщить об ошибке\n"
    #     f"┣ ♻️ <b>/reset</b> — сбросить прогресс\n"
    #     f"┗ ❓ <b>/help</b> — справка по командам\n\n"
    #     f"🎉 <b>Удачной рыбалки, капи��ан!</b> 🎉"
    # )
    text = (
        f"🌊 <b>Добро пожаловать в Рыбацкий Рай, {name_to_display}!</b> 🌊\n\n"
        f"Здесь вы можете ловить рыбу, улучшать свою удочку, соревноваться с другими игроками и стать лучшим рыбаком!\n\n"
        f"Используйте кнопки ниже, чтобы начать свое приключение."
    )

    # Inline-кнопки
    inline_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Обновления", url=UPDATES_CHANNEL_URL),
            InlineKeyboardButton(text="💬 Поддержка", url=SUPPORT_CHAT_URL),
        ]
    ])

    # Приветствие с inline-кнопками
    await message.answer(
        text=text,
        reply_markup=inline_buttons,
        parse_mode="HTML"
    )

    # Создание/проверка профиля
    existing_user = await users_collection.find_one({"user_id": user_id})
    if not existing_user:
        profile = {
            "user_id": user_id,
            "name": default_name,
            "nickname": default_name,
            "created_at": datetime.utcnow(),
            "rod_level": 1,
            "money": 0,
            "fish_inventory": {},
            "total_fish_caught": 0,
            "sea_stars": 0,
            "cookies": 0,
            "fish_multiplier": 1.0,
            "star_chance": 5.0,  # 5% базовый шанс
            "luck_x2": 10.0,     # 10% шанс на х2 улов
            "materials": {"wood": 0, "rope": 0, "metal": 0, "crystal": 0},
            "cases": {"can": 0, "chest": 0, "star_box": 0, "material_bag": 0, "weapon_box": 0, "legendary_safe": 0},
            "achievements": [],
            "boosters": {},
            "workers": [],
            "buildings": [],
            "boss_battles": {},
            "last_fish_time": None,
            "banned": False
        }
        await users_collection.insert_one(profile)
        logger.info(f"Создан новый профиль рыбака: {user_id}")

    # Основное меню
    await message.answer(
        text="🎣 Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "◀️ В меню")
async def back_to_main_menu(message: Message):
    await message.answer(
        text="🎣 Главное меню",
        reply_markup=main_menu_keyboard()
    )


