# modules/guild_chat.py - Внутриигровой чат гильдии

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import users_collection, db
from modules.nick import get_nickname
from datetime import datetime, timedelta
import re

router = Router(name="guild_chat")

# Коллекции
guilds_collection = db["guilds"]
guild_messages_collection = db["guild_messages"]

class GuildChatState(StatesGroup):
    writing_message = State()
    moderating_message = State()

# Настройки чата
CHAT_SETTINGS = {
    "max_message_length": 500,
    "messages_per_page": 10,
    "cooldown_seconds": 5,
    "max_messages_per_hour": 20
}

@router.message(F.text == "💬 Гильд-чат")
async def guild_chat_menu(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await message.answer("❌ Вы не состоите в гильдии!")
        return

    guild = await guilds_collection.find_one({"_id": guild_id})
    if not guild:
        await message.answer("❌ Гильдия не найдена!")
        return

    # Получаем информацию о участнике
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break

    if not member_info:
        await message.answer("❌ Вы не найдены в списке участников!")
        return

    # Показываем последние сообщения
    await show_chat_messages(message, guild_id, guild["name"], member_info["rank"])

async def show_chat_messages(target, guild_id: str, guild_name: str, user_rank: str, page: int = 1):
    """Показать сообщения чата"""
    
    # Получаем последние сообщения
    skip = (page - 1) * CHAT_SETTINGS["messages_per_page"]
    messages = await guild_messages_collection.find(
        {"guild_id": guild_id, "is_deleted": {"$ne": True}}
    ).sort("timestamp", -1).skip(skip).limit(CHAT_SETTINGS["messages_per_page"]).to_list(length=CHAT_SETTINGS["messages_per_page"])
    
    # Считаем общее количество сообщений
    total_messages = await guild_messages_collection.count_documents(
        {"guild_id": guild_id, "is_deleted": {"$ne": True}}
    )
    total_pages = (total_messages + CHAT_SETTINGS["messages_per_page"] - 1) // CHAT_SETTINGS["messages_per_page"]
    
    text = (
        f"💬 <b>Чат гильдии {guild_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if not messages:
        text += "\n📭 <i>Чат пуст. Будьте первым, кто напишет сообщение!</i>\n"
    else:
        # Переворачиваем список для правильного порядка (старые сверху)
        messages.reverse()
        
        for msg in messages:
            user_data = await users_collection.find_one({"user_id": msg["user_id"]})
            nickname = await get_nickname(msg["user_id"], fallback_name=user_data.get("name", "Неизвестный"))
            
            # Получаем ранг отправителя
            guild = await guilds_collection.find_one({"_id": guild_id})
            sender_rank = "member"
            for member in guild.get("members", []):
                if member["user_id"] == msg["user_id"]:
                    sender_rank = member["rank"]
                    break
            
            # Эмодзи для рангов
            rank_emoji = {"captain": "👑", "officer": "⚓", "member": "🐟"}.get(sender_rank, "🐟")
            
            # Форматируем время
            time_str = msg["timestamp"].strftime("%H:%M")
            
            # Обрезаем длинные сообщения
            message_text = msg["message"]
            if len(message_text) > 100:
                message_text = message_text[:97] + "..."
            
            text += f"\n{rank_emoji} <b>{nickname}</b> <i>({time_str})</i>\n💭 {message_text}\n"
    
    if total_pages > 1:
        text += f"\n📄 Страница {page}/{total_pages}"
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Навигация по страницам
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"chat_page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"chat_page:{page+1}"))
    
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    
    # Основные кнопки
    main_buttons = [
        InlineKeyboardButton(text="✍️ Написать", callback_data="write_message"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_chat")
    ]
    keyboard.inline_keyboard.append(main_buttons)
    
    # Кнопки модерации для офицеров и капитанов
    if user_rank in ["captain", "officer"]:
        mod_buttons = [
            InlineKeyboardButton(text="🗑️ Удалить сообщение", callback_data="moderate_message"),
            InlineKeyboardButton(text="🧹 Очистить чат", callback_data="clear_chat")
        ]
        keyboard.inline_keyboard.append(mod_buttons)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ К гильдии", callback_data="back_to_guild")
    ])
    
    if hasattr(target, 'edit_text'):
        await target.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("chat_page:"))
async def change_chat_page(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data.split(":")[1])
    
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в гильдии!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    await show_chat_messages(callback.message, guild_id, guild["name"], member_info["rank"], page)
    await callback.answer()

@router.callback_query(F.data == "write_message")
async def write_message_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Проверяем кулдаун
    last_message = await guild_messages_collection.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )
    
    if last_message:
        time_diff = (datetime.utcnow() - last_message["timestamp"]).total_seconds()
        if time_diff < CHAT_SETTINGS["cooldown_seconds"]:
            remaining = CHAT_SETTINGS["cooldown_seconds"] - int(time_diff)
            await callback.answer(f"⏰ Подождите {remaining} сек. перед отправкой нового сообщения!")
            return
    
    # Проверяем лимит сообщений в час
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_messages = await guild_messages_collection.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": hour_ago}
    })
    
    if recent_messages >= CHAT_SETTINGS["max_messages_per_hour"]:
        await callback.answer(f"⚠️ Превышен лимит сообщений в час ({CHAT_SETTINGS['max_messages_per_hour']})!")
        return
    
    await callback.message.edit_text(
        "✍️ <b>Написать сообщение в гильд-чат</b>\n\n"
        f"📝 Введите ваше сообщение (до {CHAT_SETTINGS['max_message_length']} символов):\n\n"
        "🚫 <i>Запрещены: спам, реклама, оскорбления</i>\n"
        "⏰ <i>Кулдаун между сообщениями: 5 секунд</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(GuildChatState.writing_message)

@router.message(GuildChatState.writing_message)
async def write_message_finish(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Валидация сообщения
    if len(text) > CHAT_SETTINGS["max_message_length"]:
        await message.answer(f"❌ Сообщение слишком длинное! Максимум {CHAT_SETTINGS['max_message_length']} символов.")
        return
    
    if len(text) < 1:
        await message.answer("❌ Сообщение не может быть пустым!")
        return
    
    # Простая фильтрация
    forbidden_words = ["спам", "реклама", "продам", "куплю", "@", "t.me", "http"]
    text_lower = text.lower()
    for word in forbidden_words:
        if word in text_lower:
            await message.answer("❌ Сообщение содержит запрещенные слова!")
            return
    
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await message.answer("❌ Вы не состоите в гильдии!")
        await state.clear()
        return
    
    # Сохраняем сообщение
    message_data = {
        "guild_id": guild_id,
        "user_id": user_id,
        "message": text,
        "timestamp": datetime.utcnow(),
        "is_deleted": False
    }
    
    await guild_messages_collection.insert_one(message_data)
    
    # Получаем информацию о гильдии и участнике
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    await message.answer("✅ Сообщение отправлено в гильд-чат!")
    
    # Показываем обновленный чат
    await show_chat_messages(message, guild_id, guild["name"], member_info["rank"])
    
    await state.clear()

@router.callback_query(F.data == "refresh_chat")
async def refresh_chat(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в гильдии!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    await show_chat_messages(callback.message, guild_id, guild["name"], member_info["rank"])
    await callback.answer("🔄 Чат обновлен!")

@router.callback_query(F.data == "moderate_message")
async def moderate_message_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в гильдии!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    if member_info["rank"] not in ["captain", "officer"]:
        await callback.answer("❌ У вас нет прав модерации!")
        return
    
    # Получаем последние сообщения для модерации
    messages = await guild_messages_collection.find(
        {"guild_id": guild_id, "is_deleted": {"$ne": True}}
    ).sort("timestamp", -1).limit(5).to_list(length=5)
    
    if not messages:
        await callback.answer("❌ Нет сообщений для модерации!")
        return
    
    text = "🗑️ <b>Модерация сообщений</b>\n\nВыберите сообщение для удаления:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, msg in enumerate(messages):
        user_data = await users_collection.find_one({"user_id": msg["user_id"]})
        nickname = await get_nickname(msg["user_id"], fallback_name=user_data.get("name", "Неизвестный"))
        
        time_str = msg["timestamp"].strftime("%H:%M")
        preview = msg["message"][:30] + "..." if len(msg["message"]) > 30 else msg["message"]
        
        text += f"{i+1}. <b>{nickname}</b> ({time_str}): {preview}\n"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🗑️ Удалить сообщение {i+1}",
                callback_data=f"delete_msg:{msg['_id']}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="refresh_chat")
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("delete_msg:"))
async def delete_message(callback: CallbackQuery):
    user_id = callback.from_user.id
    message_id = callback.data.split(":")[1]
    
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в гильдии!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    if member_info["rank"] not in ["captain", "officer"]:
        await callback.answer("❌ У вас нет прав модерации!")
        return
    
    # Помечаем сообщение как удаленное
    result = await guild_messages_collection.update_one(
        {"_id": message_id, "guild_id": guild_id},
        {
            "$set": {
                "is_deleted": True,
                "deleted_by": user_id,
                "deleted_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        await callback.answer("✅ Сообщение удалено!")
        
        # Возвращаемся к чату
        await show_chat_messages(callback.message, guild_id, guild["name"], member_info["rank"])
    else:
        await callback.answer("❌ Не удалось удалить сообщение!")

@router.callback_query(F.data == "clear_chat")
async def clear_chat_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в гильдии!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    if member_info["rank"] != "captain":
        await callback.answer("❌ Только капитан может очистить чат!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear_chat"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="refresh_chat")
        ]
    ])
    
    await callback.message.edit_text(
        "⚠️ <b>Очистка чата клана</b>\n\n"
        "Вы уверены, что хотите удалить ВСЕ сообщения в чате?\n"
        "Это действие необратимо!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm_clear_chat")
async def clear_chat_execute(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    # Помечаем все сообщения как удаленные
    result = await guild_messages_collection.update_many(
        {"guild_id": guild_id, "is_deleted": {"$ne": True}},
        {
            "$set": {
                "is_deleted": True,
                "deleted_by": user_id,
                "deleted_at": datetime.utcnow()
            }
        }
    )
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break
    
    await callback.answer(f"✅ Удалено {result.modified_count} сообщений!")
    await show_chat_messages(callback.message, guild_id, guild["name"], member_info["rank"])

@router.callback_query(F.data == "back_to_guild")
async def back_to_guild(callback: CallbackQuery):
    # Возвращаемся к интерфейсу гильдии
    from modules.guilds import my_guild
    await my_guild(callback.message)

# Функция для получения количества непрочитанных сообщений
async def get_unread_messages_count(user_id: int) -> int:
    """Получить количество непрочитанных сообщений в гильд-чате"""
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        return 0
    
    # Получаем время последнего посещения чата
    last_visit = user.get("last_chat_visit", datetime.utcnow() - timedelta(days=1))
    
    # Считаем сообщения после последнего посещения
    unread_count = await guild_messages_collection.count_documents({
        "guild_id": guild_id,
        "user_id": {"$ne": user_id},  # Не считаем свои сообщения
        "timestamp": {"$gt": last_visit},
        "is_deleted": {"$ne": True}
    })
    
    return unread_count

# Функция для обновления времени последнего посещения чата
async def update_last_chat_visit(user_id: int):
    """Обновить время последнего посещения чата"""
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_chat_visit": datetime.utcnow()}}
    )
