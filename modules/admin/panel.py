# modules/admin/panel.py - Модернизированная админ панель
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from modules.keyboards import main_menu_keyboard
from config import OWNER_ID, users_collection
from datetime import datetime

router = Router()

def is_admin(uid: int) -> bool:
    return uid == OWNER_ID

class AdminState(StatesGroup):
    await_stats = State()
    await_money = State()
    await_fish = State()
    await_level = State()
    await_reset = State()
    await_ban = State()
    await_unban = State()
    await_cookies = State()
    await_reset_boosts = State()
    await_stars = State()
    await_multiplier = State()

def admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная админ клавиатура"""
    buttons = [
        ["👥 Управление игроками", "💰 Экономика"],
        ["📊 Аналитика", "🎫 Промокоды"],
        ["📤 Рассылки", "🔧 Система"],
        ["🎮 Игровые функции", "🛡️ Модерация"],
        ["🔙 Выход из админки"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def players_management_keyboard() -> ReplyKeyboardMarkup:
    """Управление игроками"""
    buttons = [
        ["👤 Найти игрока", "👥 Список игроков"],
        ["📊 Статистика игрока", "✏️ Редактировать игрока"],
        ["🚫 Забанить игрока", "✅ Разбанить игрока"],
        ["🔄 Сбросить прогресс", "🏆 Топ игроки"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def economy_keyboard() -> ReplyKeyboardMarkup:
    """Экономические функции"""
    buttons = [
        ["💰 Выдать деньги", "🐟 Выдать рыбу"],
        ["⭐ Выдать звёзды", "🍪 Выдать печеньки"],
        ["📈 Установить уровень", "⚡ Установить множители"],
        ["🔄 Сбросить бусты", "💎 Выдать материалы"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def analytics_keyboard() -> ReplyKeyboardMarkup:
    """Аналитика и статистика"""
    buttons = [
        ["📊 Общая статистика", "📈 Активность игроков"],
        ["💰 Экономическая сводка", "🎣 Статистика рыбалки"],
        ["🏆 Рейтинги", "⛵ Статистика гильдий"],
        ["📅 Ежедневная сводка", "📋 Отчеты"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def system_keyboard() -> ReplyKeyboardMarkup:
    """Системные функции"""
    buttons = [
        ["🔧 Режим тех.работ", "🗑️ Очистка базы"],
        ["🔄 Перезагрузка", "⚙️ Настройки бота"],
        ["📝 Логи системы", "🛡️ Безопасность"],
        ["💾 Бэкап данных", "🔍 Диагностика"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def game_functions_keyboard() -> ReplyKeyboardMarkup:
    """Игровые функции"""
    buttons = [
        ["🐉 Управление боссами", "🎯 События"],
        ["🏗️ Управление постройками", "📦 Управление кейсами"],
        ["🎁 Специальные награды", "🌟 Достижения"],
        ["⚡ Бустеры", "🎮 Игровой баланс"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def moderation_keyboard() -> ReplyKeyboardMarkup:
    """Модерация"""
    buttons = [
        ["🚫 Массовый бан", "✅ Массовая разблокировка"],
        ["💬 Модерация чатов", "📢 Предупреждения"],
        ["🔍 Поиск нарушений", "📋 Жалобы"],
        ["⚖️ Апелляции", "🛡️ Антиспам"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

@router.message(Command("admin"))
async def admin_panel_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    # Получаем статистику для приветствия
    total_users = await users_collection.count_documents({})
    
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = await users_collection.count_documents({
        "created_at": {"$gte": today}
    })

    help_text = (
        f"🔐 <b>Админ-панель рыбацкого бота</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 Администратор: <code>{message.from_user.first_name}</code>\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"🕐 Время входа: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>\n\n"
        f"📊 <b>Быстрая статистика:</b>\n"
        f"👥 Всего пользователей: <b>{total_users:,}</b>\n"
        f"🆕 Новых сегодня: <b>{new_users_today}</b>\n\n"
        f"🎛️ Выберите раздел для управления:"
    )
    
    await message.answer(help_text, reply_markup=admin_main_keyboard(), parse_mode="HTML")

# ===== ОСНОВНЫЕ РАЗДЕЛЫ =====

@router.message(F.text == "👥 Управление игроками")
async def players_management(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👥 <b>Управление игроками</b>\n\n"
        "Здесь вы можете управлять пользователями бота:\n"
        "• Поиск и просмотр профилей\n"
        "• Редактирование данных игроков\n"
        "• Блокировка и разблокировка\n"
        "• Сброс прогресса\n"
        "• Просмотр топов",
        reply_markup=players_management_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "💰 Экономика")
async def economy_management(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💰 <b>Управление экономикой</b>\n\n"
        "Управление игровой экономикой:\n"
        "• Выдача валют и ресурсов\n"
        "• Установка уровней и множителей\n"
        "• Сброс бустеров\n"
        "• Управление материалами",
        reply_markup=economy_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Аналитика")
async def analytics_management(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📊 <b>Аналитика и статистика</b>\n\n"
        "Подробная аналитика бота:\n"
        "• Общая статистика пользователей\n"
        "• Активность и вовлеченность\n"
        "• Экономические показатели\n"
        "• Игровая статистика",
        reply_markup=analytics_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "🔧 Система")
async def system_management(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔧 <b>Системное управление</b>\n\n"
        "Управление системой бота:\n"
        "• Режим технических работ\n"
        "• Очистка и бэкап данных\n"
        "• Настройки и конфигурация\n"
        "• Диагностика и логи",
        reply_markup=system_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "🎮 Игровые функции")
async def game_functions(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎮 <b>Игровые функции</b>\n\n"
        "Управление игровым контентом:\n"
        "• Боссы и события\n"
        "• Постройки и кейсы\n"
        "• Награды и достижения\n"
        "• Игровой баланс",
        reply_markup=game_functions_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "🛡️ Модерация")
async def moderation_management(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🛡️ <b>Модерация</b>\n\n"
        "Инструменты модерации:\n"
        "• Массовые действия\n"
        "• Модерация чатов\n"
        "• Обработка жалоб\n"
        "• Антиспам системы",
        reply_markup=moderation_keyboard(),
        parse_mode="HTML"
    )

# ===== НАВИГАЦИЯ =====

@router.message(F.text == "◀️ Назад в админку")
async def back_to_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await admin_panel_handler(message)

@router.message(F.text == "🔙 Выход из админки")
async def admin_exit(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await message.answer(
        "👋 <b>Выход из админ-панели</b>\n\n"
        "Вы вышли из режима администратора.\n"
        "Для повторного входа используйте /admin",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

# ===== ЭКОНОМИЧЕСКИЕ ФУНКЦИИ =====

@router.message(F.text == "💰 Выдать деньги")
async def give_money(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID СУММА\nПример: <code>5045429385 250000</code>", parse_mode="HTML")
    await state.set_state(AdminState.await_money)

@router.message(F.text == "🐟 Выдать рыбу")
async def give_fish(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID КОЛИЧЕСТВО рыбы\nПример: <code>5045429385 1000</code>", parse_mode="HTML")
    await state.set_state(AdminState.await_fish)

@router.message(F.text == "⭐ Выдать звёзды")
async def give_stars(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID КОЛИЧЕСТВО звёзд\nПример: <code>5045429385 50</code>", parse_mode="HTML")
    await state.set_state(AdminState.await_stars)

@router.message(F.text == "🍪 Выдать печеньки")
async def give_cookies(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID КОЛИЧЕСТВО печенек\nПример: <code>5045429385 100</code>", parse_mode="HTML")
    await state.set_state(AdminState.await_cookies)

@router.message(F.text == "📈 Установить уровень")
async def set_level(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID УРОВЕНЬ (от 1 до 60)\nПример: <code>5045429385 30</code>", parse_mode="HTML")
    await state.set_state(AdminState.await_level)

@router.message(F.text == "⚡ Установить множители")
async def set_multiplier(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Введите: ID МНОЖИТЕЛЬ\nПример: <code>5045429385 2.5</code>\n\n"
        "Установит множитель рыбы для игрока",
        parse_mode="HTML"
    )
    await state.set_state(AdminState.await_multiplier)

# ===== ОБРАБОТЧИКИ СОСТОЯНИЙ =====

@router.message(AdminState.await_money)
async def handle_money(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат")
        
        uid = int(parts[0])
        amount = int(parts[1])
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"money": amount}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ {amount:,}$ выдано пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()

@router.message(AdminState.await_fish)
async def handle_fish(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"fish": amount}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ {amount:,} рыбы выдано пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()

@router.message(AdminState.await_stars)
async def handle_stars(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"sea_stars": amount}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ {amount} морских звёзд выдано пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()

@router.message(AdminState.await_cookies)
async def handle_cookies(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"cookies": amount}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ {amount} печенек выдано пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()

@router.message(AdminState.await_level)
async def handle_level(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        level = int(parts[1])
        
        if level < 1 or level > 60:
            await message.answer("❌ Уровень должен быть от 1 до 60", reply_markup=economy_keyboard())
            return
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {"rod_level": level}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ Уровень удочки {level} установлен пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()

@router.message(AdminState.await_multiplier)
async def handle_multiplier(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        multiplier = float(parts[1])
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {"fish_multiplier": multiplier}}
        )
        
        if result.matched_count == 0:
            await message.answer("❌ Пользователь не найден", reply_markup=economy_keyboard())
        else:
            await message.answer(f"✅ Множитель рыбы {multiplier}x установлен пользователю {uid}", reply_markup=economy_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=economy_keyboard())
    finally:
        await state.clear()
