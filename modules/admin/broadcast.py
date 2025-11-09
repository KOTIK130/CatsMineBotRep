# modules/admin/broadcast.py - Расширенная система рассылки

from aiogram import Router
from aiogram import F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import users_collection, bot, logger
from modules.admin.panel import is_admin, admin_main_keyboard
import asyncio
from datetime import datetime, timedelta

router = Router(name="broadcast")

class BroadcastState(StatesGroup):
    waiting_message = State()
    waiting_confirmation = State()
    waiting_target_selection = State()
    waiting_template_name = State()
    waiting_schedule_time = State()

def broadcast_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню рассылок"""
    buttons = [
        ["📢 Быстрая рассылка", "📋 Шаблоны сообщений"],
        ["⏰ Отложенные рассылки", "📊 Статистика рассылок"],
        ["🎯 Целевые аудитории", "📝 История рассылок"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def broadcast_types_keyboard() -> ReplyKeyboardMarkup:
    """Типы рассылок"""
    buttons = [
        ["📢 Объявление", "🎉 Обновление"],
        ["🎁 Акция/Промо", "⚠️ Важное уведомление"],
        ["🎮 Игровое событие", "💰 Экономические изменения"],
        ["🔧 Техническая информация", "📰 Новости"],
        ["◀️ Назад к рассылкам"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def audience_keyboard() -> ReplyKeyboardMarkup:
    """Выбор аудитории"""
    buttons = [
        ["👥 Все пользователи", "🎣 Активные рыбаки"],
        ["👑 Донатеры", "🏆 Топ игроки"],
        ["⛵ Участники гильдий", "🆕 Новички"],
        ["💤 Неактивные", "🆔 По списку ID"],
        ["◀️ Назад к типам"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Подтверждение рассылки"""
    buttons = [
        ["✅ Отправить сейчас", "⏰ Отложить"],
        ["📝 Редактировать", "💾 Сохранить шаблон"],
        ["❌ Отменить"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

# Шаблоны сообщений для разных типов рассылок
BROADCAST_TEMPLATES = {
    "announcement": {
        "name": "📢 Объявление",
        "template": "📢 <b>ОБЪЯВЛЕНИЕ</b>\n\n{content}\n\n🎣 Команда Рыбацкого Рая",
        "emoji": "📢"
    },
    "update": {
        "name": "🎉 Обновление",
        "template": "🎉 <b>ОБНОВЛЕНИЕ БОТА!</b>\n\n✨ <b>Что нового:</b>\n{content}\n\n🚀 Обновляйтесь и наслаждайтесь новыми возможностями!\n\n🎣 Команда разработки",
        "emoji": "🎉"
    },
    "promo": {
        "name": "🎁 Акция/Промо",
        "template": "🎁 <b>СПЕЦИАЛЬНАЯ АКЦИЯ!</b>\n\n🔥 {content}\n\n⏰ Не упустите возможность!\n\n🎣 Удачной рыбалки!",
        "emoji": "🎁"
    },
    "warning": {
        "name": "⚠️ Важное уведомление",
        "template": "⚠️ <b>ВАЖНОЕ УВЕДОМЛЕНИЕ</b>\n\n{content}\n\n📞 При вопросах обращайтесь в поддержку.\n\n🎣 Администрация",
        "emoji": "⚠️"
    },
    "event": {
        "name": "🎮 Игровое событие",
        "template": "🎮 <b>ИГРОВОЕ СОБЫТИЕ!</b>\n\n🌟 {content}\n\n🏆 Участвуйте и получайте награды!\n\n🎣 Удачи в событии!",
        "emoji": "🎮"
    },
    "economy": {
        "name": "💰 Экономические изменения",
        "template": "💰 <b>ИЗМЕНЕНИЯ В ЭКОНОМИКЕ</b>\n\n📊 {content}\n\n💡 Адаптируйтесь к изменениям для максимальной выгоды!\n\n🎣 Команда баланса",
        "emoji": "💰"
    },
    "technical": {
        "name": "🔧 Техническая информация",
        "template": "🔧 <b>ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ</b>\n\n{content}\n\n🛠️ Спасибо за понимание!\n\n🎣 Техническая поддержка",
        "emoji": "🔧"
    },
    "news": {
        "name": "📰 Новости",
        "template": "📰 <b>НОВОСТИ РЫБАЦКОГО РАЯ</b>\n\n{content}\n\n📢 Следите за обновлениями!\n\n🎣 Редакция новостей",
        "emoji": "📰"
    }
}

@router.message(F.text == "📤 Рассылки")
async def broadcast_main_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Получаем статистику
    total_users = await users_collection.count_documents({})
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = await users_collection.count_documents({
        "last_fish_time": {"$gte": week_ago}
    })
    
    donators = await users_collection.count_documents({
        "$or": [{"cookies": {"$gt": 0}}, {"is_donator": True}]
    })
    
    text = (
        f"📤 <b>Система рассылок</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Статистика аудиторий:</b>\n"
        f"👥 Всего пользователей: <b>{total_users:,}</b>\n"
        f"🎣 Активных за неделю: <b>{active_users:,}</b>\n"
        f"👑 Донатеров: <b>{donators:,}</b>\n\n"
        f"🎯 Выберите действие:"
    )
    
    await message.answer(text, reply_markup=broadcast_main_keyboard(), parse_mode="HTML")

@router.message(F.text == "📢 Быстрая рассылка")
async def quick_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = (
        "📢 <b>Быстрая рассылка</b>\n\n"
        "Выберите тип сообщения для рассылки:\n\n"
        "📢 <b>Объявление</b> - общие объявления\n"
        "🎉 <b>Обновление</b> - информация об обновлениях\n"
        "🎁 <b>Акция/Промо</b> - промо-акции и скидки\n"
        "⚠️ <b>Важное уведомление</b> - критичная информация\n"
        "🎮 <b>Игровое событие</b> - события в игре\n"
        "💰 <b>Экономические изменения</b> - изменения баланса\n"
        "🔧 <b>Техническая информация</b> - тех. работы\n"
        "📰 <b>Новости</b> - новости проекта"
    )
    
    await message.answer(text, reply_markup=broadcast_types_keyboard(), parse_mode="HTML")

# Обработчики типов рассылок
@router.message(F.text.in_(["📢 Объявление", "🎉 Обновление", "🎁 Акция/Промо", "⚠️ Важное уведомление", 
                            "🎮 Игровое событие", "💰 Экономические изменения", "🔧 Техническая информация", "📰 Новости"]))
async def select_broadcast_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Определяем тип рассылки
    type_mapping = {
        "📢 Объявление": "announcement",
        "🎉 Обновление": "update", 
        "🎁 Акция/Промо": "promo",
        "⚠️ Важное уведомление": "warning",
        "🎮 Игровое событие": "event",
        "💰 Экономические изменения": "economy",
        "🔧 Техническая информация": "technical",
        "📰 Новости": "news"
    }
    
    broadcast_type = type_mapping.get(message.text)
    template_info = BROADCAST_TEMPLATES[broadcast_type]
    
    await state.update_data(broadcast_type=broadcast_type)
    
    text = (
        f"{template_info['emoji']} <b>{template_info['name']}</b>\n\n"
        f"Выберите целевую аудиторию:\n\n"
        f"👥 <b>Все пользователи</b> - массовая рассылка\n"
        f"🎣 <b>Активные рыбаки</b> - активность за неделю\n"
        f"👑 <b>Донатеры</b> - пользователи с печеньками\n"
        f"🏆 <b>Топ игроки</b> - лучшие рыбаки\n"
        f"⛵ <b>Участники гильдий</b> - члены гильдий\n"
        f"🆕 <b>Новички</b> - регистрация за 3 дня\n"
        f"💤 <b>Неактивные</b> - нет активности 30+ дней\n"
        f"🆔 <b>По списку ID</b> - конкретные пользователи"
    )
    
    await message.answer(text, reply_markup=audience_keyboard(), parse_mode="HTML")

# Обработчики аудиторий
@router.message(F.text.in_(["👥 Все пользователи", "🎣 Активные рыбаки", "👑 Донатеры", "🏆 Топ игроки",
                            "⛵ Участники гильдий", "🆕 Новички", "💤 Неактивные", "🆔 По списку ID"]))
async def select_audience(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Определяем аудиторию и подсчитываем количество
    audience_mapping = {
        "👥 Все пользователи": ("all", {}),
        "🎣 Активные рыбаки": ("active", {"last_fish_time": {"$gte": datetime.utcnow() - timedelta(days=7)}}),
        "👑 Донатеры": ("donators", {"$or": [{"cookies": {"$gt": 0}}, {"is_donator": True}]}),
        "🏆 Топ игроки": ("top", {"total_fish_caught": {"$gte": 1000}}),
        "⛵ Участники гильдий": ("guild_members", {"guild_id": {"$exists": True, "$ne": None}}),
        "🆕 Новички": ("newbies", {"created_at": {"$gte": datetime.utcnow() - timedelta(days=3)}}),
        "💤 Неактивные": ("inactive", {"$or": [
            {"last_fish_time": {"$lt": datetime.utcnow() - timedelta(days=30)}},
            {"last_fish_time": {"$exists": False}}
        ]}),
        "🆔 По списку ID": ("ids", {})
    }
    
    audience_type, query = audience_mapping.get(message.text, ("all", {}))
    
    if audience_type == "ids":
        await message.answer(
            "🆔 <b>Рассылка по списку ID</b>\n\n"
            "Введите ID пользователей через запятую:\n"
            "Пример: <code>123456789, 987654321, 555666777</code>",
            parse_mode="HTML"
        )
        await state.update_data(audience_type=audience_type)
        await state.set_state(BroadcastState.waiting_target_selection)
        return
    
    # Подсчитываем количество получателей
    target_count = await users_collection.count_documents(query)
    
    await state.update_data(
        audience_type=audience_type,
        target_count=target_count,
        query=query
    )
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type")
    template_info = BROADCAST_TEMPLATES[broadcast_type]
    
    text = (
        f"{template_info['emoji']} <b>{template_info['name']}</b>\n"
        f"🎯 Аудитория: <b>{message.text}</b>\n"
        f"👥 Получателей: <b>{target_count:,}</b>\n\n"
        f"📝 Введите содержание сообщения:\n"
        f"(текст будет вставлен в шаблон)"
    )
    
    await message.answer(text, parse_mode="HTML")
    await state.set_state(BroadcastState.waiting_message)

@router.message(BroadcastState.waiting_target_selection)
async def process_id_list(message: Message, state: FSMContext):
    try:
        # Парсим ID из сообщения
        id_text = message.text.replace(" ", "")
        user_ids = [int(uid.strip()) for uid in id_text.split(",") if uid.strip().isdigit()]
        
        if not user_ids:
            await message.answer("❌ Не найдено корректных ID! Попробуйте еще раз.")
            return
        
        # Проверяем существование пользователей
        existing_users = await users_collection.count_documents({
            "user_id": {"$in": user_ids}
        })
        
        await state.update_data(
            target_count=existing_users,
            target_ids=user_ids
        )
        
        data = await state.get_data()
        broadcast_type = data.get("broadcast_type")
        template_info = BROADCAST_TEMPLATES[broadcast_type]
        
        text = (
            f"{template_info['emoji']} <b>{template_info['name']}</b>\n"
            f"🆔 ID указано: <b>{len(user_ids)}</b>\n"
            f"✅ Найдено пользователей: <b>{existing_users}</b>\n\n"
            f"📝 Введите содержание сообщения:"
        )
        
        await message.answer(text, parse_mode="HTML")
        await state.set_state(BroadcastState.waiting_message)
        
    except ValueError:
        await message.answer("❌ Ошибка в формате ID! Используйте только числа через запятую.")

@router.message(BroadcastState.waiting_message)
async def process_broadcast_content(message: Message, state: FSMContext):
    content = message.text.strip()
    
    if len(content) > 3000:
        await message.answer("❌ Содержание слишком длинное! Максимум 3000 символов.")
        return
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type")
    template_info = BROADCAST_TEMPLATES[broadcast_type]
    
    # Формируем финальное сообщение
    final_message = template_info["template"].format(content=content)
    
    await state.update_data(
        content=content,
        final_message=final_message
    )
    
    # Показываем превью
    audience_names = {
        "all": "Всем пользователям",
        "active": "Активным рыбакам",
        "donators": "Донатерам", 
        "top": "Топ игрокам",
        "guild_members": "Участникам гильдий",
        "newbies": "Новичкам",
        "inactive": "Неактивным пользователям",
        "ids": "По списку ID"
    }
    
    audience_type = data.get("audience_type")
    target_count = data.get("target_count", 0)
    
    preview_text = (
        f"📤 <b>Подтверждение рассылки</b>\n\n"
        f"{template_info['emoji']} Тип: <b>{template_info['name']}</b>\n"
        f"🎯 Аудитория: <b>{audience_names.get(audience_type, 'Неизвестно')}</b>\n"
        f"👥 Получателей: <b>{target_count:,}</b>\n\n"
        f"📝 <b>Превью сообщения:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{final_message}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ Подтвердите действие:"
    )
    
    await message.answer(preview_text, reply_markup=confirm_keyboard(), parse_mode="HTML")
    await state.set_state(BroadcastState.waiting_confirmation)

@router.message(F.text == "✅ Отправить сейчас", BroadcastState.waiting_confirmation)
async def confirm_broadcast_now(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    await execute_broadcast(message, data)
    await state.clear()

async def execute_broadcast(message: Message, data: dict):
    """Выполнение рассылки"""
    audience_type = data.get("audience_type")
    final_message = data.get("final_message")
    target_ids = data.get("target_ids", [])
    query = data.get("query", {})
    
    # Получаем список получателей
    if audience_type == "ids":
        users = await users_collection.find(
            {"user_id": {"$in": target_ids}}, 
            {"user_id": 1}
        ).to_list(length=None)
    else:
        users = await users_collection.find(query, {"user_id": 1}).to_list(length=None)
    
    total_users = len(users)
    
    if total_users == 0:
        await message.answer("❌ Не найдено пользователей для рассылки!", reply_markup=broadcast_main_keyboard())
        return
    
    # Начинаем рассылку
    progress_msg = await message.answer(
        f"📤 <b>Начинаем рассылку...</b>\n\n"
        f"👥 Получателей: {total_users:,}\n"
        f"📊 Прогресс: 0/{total_users} (0%)",
        parse_mode="HTML"
    )
    
    sent_count = 0
    failed_count = 0
    batch_size = 25  # Уменьшили для стабильности
    
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        
        # Отправляем батч
        tasks = []
        for user in batch:
            user_id = user["user_id"]
            task = send_message_safe(user_id, final_message)
            tasks.append(task)
        
        # Ждем выполнения батча
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Подсчитываем результаты
        for result in results:
            if result is True:
                sent_count += 1
            else:
                failed_count += 1
        
        # Обновляем прогресс каждые 25 сообщений
        processed = sent_count + failed_count
        progress = (processed / total_users) * 100
        
        try:
            await progress_msg.edit_text(
                f"📤 <b>Рассылка в процессе...</b>\n\n"
                f"👥 Получателей: {total_users:,}\n"
                f"📊 Прогресс: {processed}/{total_users} ({progress:.1f}%)\n"
                f"✅ Отправлено: {sent_count}\n"
                f"❌ Ошибок: {failed_count}",
                parse_mode="HTML"
            )
        except:
            pass
        
        # Пауза между батчами
        await asyncio.sleep(1.2)
    
    # Финальный отчет
    success_rate = (sent_count / total_users) * 100 if total_users > 0 else 0
    
    final_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Итоговая статистика:</b>\n"
        f"👥 Всего получателей: <b>{total_users:,}</b>\n"
        f"✅ Успешно доставлено: <b>{sent_count:,}</b>\n"
        f"❌ Ошибок доставки: <b>{failed_count:,}</b>\n"
        f"📈 Успешность: <b>{success_rate:.1f}%</b>\n\n"
        f"🕐 Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await progress_msg.edit_text(final_text, parse_mode="HTML")
    await message.answer("📤 Возвращаемся в меню рассылок", reply_markup=broadcast_main_keyboard())
    
    # Логируем рассылку
    logger.info(f"Broadcast completed by {message.from_user.id}: {sent_count}/{total_users} sent, type: {data.get('broadcast_type')}")

async def send_message_safe(user_id: int, text: str) -> bool:
    """Безопасная отправка сообщения"""
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
        return True
    except Exception as e:
        if "bot was blocked" not in str(e).lower() and "chat not found" not in str(e).lower():
            logger.warning(f"Failed to send message to {user_id}: {e}")
        return False

# Навигация
@router.message(F.text == "◀️ Назад к рассылкам")
async def back_to_broadcasts(message: Message, state: FSMContext):
    await state.clear()
    await broadcast_main_menu(message)

@router.message(F.text == "◀️ Назад к типам")
async def back_to_types(message: Message, state: FSMContext):
    await quick_broadcast(message)

@router.message(F.text == "◀️ Назад в админку")
async def back_to_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔐 Возвращаемся в админ-панель", reply_markup=admin_main_keyboard())

@router.message(F.text == "❌ Отменить", BroadcastState.waiting_confirmation)
async def cancel_broadcast(message: Message, state: FSMContext):
    await message.answer("❌ Рассылка отменена", reply_markup=broadcast_main_keyboard())
    await state.clear()

# Заглушки для будущих функций
@router.message(F.text.in_(["📋 Шаблоны сообщений", "⏰ Отложенные рассылки", "📊 Статистика рассылок", 
                            "🎯 Целевые аудитории", "📝 История рассылок"]))
async def coming_soon(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🚧 <b>В разработке</b>\n\n"
        "Эта функция будет добавлена в следующих обновлениях!",
        reply_markup=broadcast_main_keyboard(),
        parse_mode="HTML"
    )
