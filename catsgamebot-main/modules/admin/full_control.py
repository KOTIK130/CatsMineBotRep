# modules/admin/full_control.py - Полный контроль админ панели (обновленный с рассылкой)
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import users_collection, db, MAINTENANCE_MODE, ADMIN_IDS
from modules.admin.panel import is_admin, admin_main_keyboard
from datetime import datetime

router = Router(name="full_control")

class AdminControlState(StatesGroup):
    create_promo = State()
    edit_user = State()
    maintenance_toggle = State()
    awaiting_user_id = State()

promocodes_collection = db["promocodes"]

def full_control_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура полного контроля"""
    buttons = [
        ["🎫 Создать промокод", "👤 Редактировать игрока"],
        ["🔧 Режим тех.работ", "📊 Статистика бота"],
        ["🗑 Очистить базу", "📋 Список промокодов"],
        ["📤 Рассылка", "🔄 Перезагрузить бота"],
        ["◀️ Назад в админ панель"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

async def show_full_control_menu(message: Message):
    """Показать меню полного контроля"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    global MAINTENANCE_MODE
    maintenance_status = "🟢 Включён" if MAINTENANCE_MODE else "🔴 Выключен"
    
    text = (
        "🔧 <b>Полный контроль бота</b>\n\n"
        f"🛠 Режим тех.работ: {maintenance_status}\n"
        f"👑 Админ ID: <code>{message.from_user.id}</code>\n\n"
        "Выберите действие для управления ботом:"
    )
    
    await message.answer(text, reply_markup=full_control_keyboard(), parse_mode="HTML")

@router.message(F.text == "📤 Рассылка")
async def broadcast_handler(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Импортируем и вызываем функцию рассылки
    from modules.admin.broadcast import broadcast_menu
    await broadcast_menu(message)

@router.message(F.text == "🎫 Создать промокод")
async def create_promocode_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎫 <b>Создание промокода</b>\n\n"
        "Введите данные в формате:\n"
        "<code>КОД|деньги:сумма|звёзды:сумма|печеньки:сумма|лимит:число</code>\n\n"
        "Пример:\n"
        "<code>FISH2024|money:1000|sea_stars:10|cookies:5|limit:100</code>\n\n"
        "Доступные награды: money, sea_stars, cookies, fish",
        parse_mode="HTML"
    )
    await state.set_state(AdminControlState.create_promo)

@router.message(AdminControlState.create_promo)
async def create_promocode_finish(message: Message, state: FSMContext):
    try:
        parts = message.text.split("|")
        code = parts[0].upper()
        
        # Проверяем существование промокода
        existing = await promocodes_collection.find_one({"code": code})
        if existing:
            await message.answer("❌ Промокод с таким названием уже существует!")
            return
        
        rewards = {}
        max_uses = None
        
        for part in parts[1:]:
            if ":" in part:
                key, value = part.split(":")
                if key == "limit":
                    max_uses = int(value)
                elif key in ["money", "sea_stars", "cookies", "fish"]:
                    rewards[key] = int(value)
        
        # Создаем промокод
        promo_data = {
            "code": code,
            "rewards": rewards,
            "max_uses": max_uses,
            "used_count": 0,
            "created_at": datetime.utcnow(),
            "created_by": message.from_user.id
        }
        
        await promocodes_collection.insert_one(promo_data)
        
        reward_text = "\n".join([f"• {k}: {v}" for k, v in rewards.items()])
        await message.answer(
            f"✅ <b>Промокод создан!</b>\n\n"
            f"🎫 Код: <code>{code}</code>\n"
            f"🎁 Награды:\n{reward_text}\n"
            f"📊 Лимит: {max_uses or 'Без лимита'}",
            reply_markup=full_control_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания промокода: {e}", reply_markup=full_control_keyboard())
    
    await state.clear()

@router.message(F.text == "📋 Список промокодов")
async def list_promocodes(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    promos = await promocodes_collection.find().sort("created_at", -1).limit(10).to_list(length=10)
    
    if not promos:
        await message.answer("📋 Промокодов нет", reply_markup=full_control_keyboard())
        return
    
    text = "📋 <b>Последние промокоды:</b>\n\n"
    
    for promo in promos:
        code = promo["code"]
        used = promo.get("used_count", 0)
        limit = promo.get("max_uses", "∞")
        rewards = promo.get("rewards", {})
        
        reward_text = ", ".join([f"{k}:{v}" for k, v in rewards.items()])
        text += f"🎫 <code>{code}</code>\n📊 {used}/{limit} | 🎁 {reward_text}\n\n"
    
    await message.answer(text, reply_markup=full_control_keyboard(), parse_mode="HTML")

@router.message(F.text == "🔧 Режим тех.работ")
async def toggle_maintenance_mode(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = not MAINTENANCE_MODE
    
    status = "🟢 включён" if MAINTENANCE_MODE else "🔴 выключен"
    await message.answer(
        f"🔧 <b>Режим технических работ {status}</b>\n\n"
        f"{'⚠️ Бот недоступен для обычных пользователей' if MAINTENANCE_MODE else '✅ Бот доступен для всех пользователей'}",
        reply_markup=full_control_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Статистика бота")
async def show_bot_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        total_users = await users_collection.count_documents({})
        total_promos = await promocodes_collection.count_documents({})
        
        # Статистика по уровням удочек
        pipeline = [
            {"$group": {"_id": "$rod_level", "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
            {"$limit": 5}
        ]
        level_stats = await users_collection.aggregate(pipeline).to_list(length=5)
        
        # Статистика по деньгам
        rich_users = await users_collection.find().sort("money", -1).limit(3).to_list(length=3)
        
        # Статистика по рыбе
        fish_leaders = await users_collection.find().sort("total_fish_caught", -1).limit(3).to_list(length=3)
        
        text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{total_users:,}</b>\n"
            f"🎫 Промокодов: <b>{total_promos}</b>\n\n"
            f"🎣 <b>Топ уровни удочек:</b>\n"
        )
        
        for stat in level_stats:
            text += f"Уровень {stat['_id']}: {stat['count']} игроков\n"
        
        text += f"\n💰 <b>Самые богатые:</b>\n"
        for i, user in enumerate(rich_users, 1):
            name = user.get("nickname") or user.get("name") or f"ID{user['user_id']}"
            text += f"{i}. {name}: {user.get('money', 0):,}$\n"
        
        text += f"\n🐟 <b>Лучшие рыбаки:</b>\n"
        for i, user in enumerate(fish_leaders, 1):
            name = user.get("nickname") or user.get("name") or f"ID{user['user_id']}"
            text += f"{i}. {name}: {user.get('total_fish_caught', 0):,} рыб\n"
        
        await message.answer(text, reply_markup=full_control_keyboard(), parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}", reply_markup=full_control_keyboard())

@router.message(F.text == "👤 Редактировать игрока")
async def edit_user_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👤 <b>Редактирование игрока</b>\n\n"
        "Введите ID игрока для редактирования:",
        parse_mode="HTML"
    )
    await state.set_state(AdminControlState.awaiting_user_id)

@router.message(AdminControlState.awaiting_user_id)
async def edit_user_show_info(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        user = await users_collection.find_one({"user_id": user_id})
        
        if not user:
            await message.answer("❌ Пользователь не найден!", reply_markup=full_control_keyboard())
            await state.clear()
            return
        
        name = user.get("nickname") or user.get("name") or f"ID{user_id}"
        
        text = (
            f"👤 <b>Информация о игроке</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Имя: {name}\n"
            f"🎣 Уровень удочки: {user.get('rod_level', 1)}\n"
            f"💰 Деньги: {user.get('money', 0):,}$\n"
            f"🐟 Рыба: {user.get('fish', 0):,}\n"
            f"⭐ Морские звёзды: {user.get('sea_stars', 0)}\n"
            f"🍪 Печеньки: {user.get('cookies', 0)}\n"
            f"🚫 Забанен: {'Да' if user.get('banned', False) else 'Нет'}\n\n"
            f"Для редактирования используйте команды из основной админ панели."
        )
        
        await message.answer(text, reply_markup=full_control_keyboard(), parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Неверный формат ID!", reply_markup=full_control_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=full_control_keyboard())
    
    await state.clear()

@router.message(F.text == "🗑 Очистить базу")
async def confirm_clear_db(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if message.from_user.id != ADMIN_IDS[0]:  # Только главный админ
        await message.answer("❌ Только главный администратор может очистить базу!", reply_markup=full_control_keyboard())
        return
    
    await message.answer(
        "⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        "Вы собираетесь удалить ВСЕ данные из базы!\n"
        "Это действие НЕОБРАТИМО!\n\n"
        "Для подтверждения напишите: <code>УДАЛИТЬ ВСЁ</code>",
        reply_markup=full_control_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "УДАЛИТЬ ВСЁ")
async def clear_database(message: Message):
    if not is_admin(message.from_user.id) or message.from_user.id != ADMIN_IDS[0]:
        return
    
    try:
        # Очищаем все коллекции
        await users_collection.delete_many({})
        await promocodes_collection.delete_many({})
        
        # Очищаем коллекции гильдий если есть
        try:
            guilds_collection = db["guilds"]
            guild_messages_collection = db["guild_messages"]
            await guilds_collection.delete_many({})
            await guild_messages_collection.delete_many({})
        except:
            pass
        
        await message.answer(
            "✅ <b>База данных полностью очищена!</b>\n\n"
            "Все пользователи, промокоды и гильдии удалены.",
            reply_markup=full_control_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при очистке базы данных:\n<code>{e}</code>",
            reply_markup=full_control_keyboard(),
            parse_mode="HTML"
        )

@router.message(F.text == "🔄 Перезагрузить бота")
async def restart_bot(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔄 <b>Перезагрузка бота</b>\n\n"
        "⚠️ Функция перезагрузки недоступна в текущей конфигурации.\n"
        "Для перезагрузки обратитесь к хостинг-провайдеру.",
        reply_markup=full_control_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "◀️ Назад в админку")
async def back_to_admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\nВы вернулись в основную админ панель.",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
