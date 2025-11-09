# modules/guilds.py - Система рыбацких гильдий (обновленная с чатом)

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import users_collection, db
from modules.keyboards import main_menu_keyboard, guild_main_keyboard, guild_management_keyboard
from datetime import datetime, timedelta
import random
import logging

router = Router(name="guilds")

# Коллекция кланов
guilds_collection = db["guilds"]

class GuildState(StatesGroup):
    creating_name = State()
    creating_description = State()
    editing_announcement = State()
    creating_task = State()

# Ранги в гильдии
GUILD_RANKS = {
    "member": {"name": "🐟 Рыбак", "permissions": ["fish", "view", "chat"]},
    "officer": {"name": "⚓ Боцман", "permissions": ["fish", "view", "chat", "invite", "kick_member", "moderate_chat"]},
    "captain": {"name": "👑 Капитан", "permissions": ["all"]}
}

# Бонусы гильдии по уровню
GUILD_BONUSES = {
    1: {"fish_bonus": 0.05, "star_bonus": 0.02, "members": 10},
    2: {"fish_bonus": 0.10, "star_bonus": 0.05, "members": 15},
    3: {"fish_bonus": 0.15, "star_bonus": 0.08, "members": 20},
    4: {"fish_bonus": 0.20, "star_bonus": 0.12, "members": 25},
    5: {"fish_bonus": 0.30, "star_bonus": 0.20, "members": 30}
}

@router.message(F.text == "⛵ Кланы")
async def guild_menu(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("🚫 Сначала напиши /start.")
        return

    guild_id = user.get("guild_id")
    
    if guild_id:
        guild = await guilds_collection.find_one({"_id": guild_id})
        if guild:
            # Получаем количество непрочитанных сообщений
            try:
                from modules.guild_chat import get_unread_messages_count
                unread_count = await get_unread_messages_count(user_id)
                unread_text = f" ({unread_count} новых)" if unread_count > 0 else ""
            except Exception as e:
                logging.error(f"Ошибка при получении непрочитанных сообщений: {e}")
                unread_text = ""
            
            text = (
                f"⛵ <b>Добро пожаловать в кланы!</b>\n\n"
                f"🏴‍☠️ Ваш клан: <b>{guild['name']}</b>\n"
                f"⭐ Уровень: <b>{guild.get('level', 1)}</b>\n"
                f"👥 Участников: <b>{len(guild.get('members', []))}/{GUILD_BONUSES[guild.get('level', 1)]['members']}</b>\n"
                f"💬 Чат: активен{unread_text}\n\n"
                f"🎣 Бонус к рыбе: <b>+{GUILD_BONUSES[guild.get('level', 1)]['fish_bonus']*100:.0f}%</b>\n"
                f"⭐ Бонус к звёздам: <b>+{GUILD_BONUSES[guild.get('level', 1)]['star_bonus']*100:.0f}%</b>"
            )
        else:
            text = "⛵ <b>Система кланов</b>\n\nВаш клан был расформирован."
            await users_collection.update_one({"user_id": user_id}, {"$unset": {"guild_id": ""}})
    else:
        text = (
            f"⛵ <b>Добро пожаловать в систему кланов!</b>\n\n"
            f"🌊 Объединяйтесь с другими рыбаками в мощные флотилии!\n\n"
            f"🎁 <b>Преимущества кланов:</b>\n"
            f"• 🎣 Бонус к улову рыбы\n"
            f"• ⭐ Бонус к морским звёздам\n"
            f"• 💬 Внутриигровой чат\n"
            f"• 🎯 Совместные задания\n"
            f"• 💰 Общая казна\n"
            f"• 🏆 Клановые турниры\n"
            f"• 🤝 Общение с единомышленниками\n\n"
            f"🚀 Создайте свой клан или присоединитесь к существующему!"
        )

    await message.answer(text, reply_markup=guild_main_keyboard(), parse_mode="HTML")

@router.message(F.text == "⛵ Мой клан")
async def my_guild(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await message.answer("❌ Вы не состоите в клане!", reply_markup=guild_main_keyboard())
        return

    guild = await guilds_collection.find_one({"_id": guild_id})
    if not guild:
        await message.answer("❌ Клан не найден!", reply_markup=guild_main_keyboard())
        return

    # Получаем информацию о участнике
    member_info = None
    for member in guild.get("members", []):
        if member["user_id"] == user_id:
            member_info = member
            break

    if not member_info:
        await message.answer("❌ Вы не найдены в списке участников клана!", reply_markup=guild_main_keyboard())
        return

    rank_info = GUILD_RANKS[member_info["rank"]]
    guild_level = guild.get("level", 1)
    bonuses = GUILD_BONUSES[guild_level]
    
    # Статистика гильдии
    total_fish = sum(member.get("contribution_fish", 0) for member in guild.get("members", []))
    total_stars = sum(member.get("contribution_stars", 0) for member in guild.get("members", []))
    
    # Получаем количество непрочитанных сообщений
    try:
        from modules.guild_chat import get_unread_messages_count
        unread_count = await get_unread_messages_count(user_id)
    except Exception as e:
        logging.error(f"Ошибка при получении непрочитанных сообщений: {e}")
        unread_count = 0
    
    text = (
        f"⛵ <b>{guild['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {guild.get('description', 'Описание отсутствует')}\n\n"
        f"📊 <b>Информация о клане:</b>\n"
        f"⭐ Уровень: <b>{guild_level}/5</b>\n"
        f"👥 Участников: <b>{len(guild.get('members', []))}/{bonuses['members']}</b>\n"
        f"💰 Казна: <b>{guild.get('treasury', 0):,}$</b>\n"
        f"🐟 Общий улов: <b>{total_fish:,}</b>\n"
        f"⭐ Общие звёзды: <b>{total_stars:,}</b>\n\n"
        f"🎁 <b>Бонусы клана:</b>\n"
        f"🎣 Рыба: <b>+{bonuses['fish_bonus']*100:.0f}%</b>\n"
        f"⭐ Звёзды: <b>+{bonuses['star_bonus']*100:.0f}%</b>\n\n"
        f"👤 <b>Ваш статус:</b>\n"
        f"🏅 Ранг: {rank_info['name']}\n"
        f"🐟 Вклад рыбой: <b>{member_info.get('contribution_fish', 0):,}</b>\n"
        f"⭐ Вклад звёздами: <b>{member_info.get('contribution_stars', 0):,}</b>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Кнопка чата с индикатором новых сообщений
    chat_text = "💬 Клан-чат"
    if unread_count > 0:
        chat_text += f" ({unread_count})"
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text=chat_text, callback_data="guild_chat")
    ])
    
    # Кнопки в зависимости от ранга
    if member_info["rank"] == "captain":
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⚙️ Управление", callback_data="guild_manage")
        ])
    
    keyboard.inline_keyboard.extend([
        [InlineKeyboardButton(text="👥 Участники", callback_data="guild_members")],
        [InlineKeyboardButton(text="💰 Пожертвовать", callback_data="guild_donate")],
        [InlineKeyboardButton(text="🚪 Покинуть клан", callback_data="guild_leave")]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "guild_chat")
async def open_guild_chat(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        # Обновляем время последнего посещения чата
        from modules.guild_chat import update_last_chat_visit, show_chat_messages
        await update_last_chat_visit(user_id)
        
        user = await users_collection.find_one({"user_id": user_id})
        guild_id = user.get("guild_id")
        
        if not guild_id:
            await callback.answer("❌ Вы не состоите в клане!")
            return

        guild = await guilds_collection.find_one({"_id": guild_id})
        member_info = None
        for member in guild.get("members", []):
            if member["user_id"] == user_id:
                member_info = member
                break

        await show_chat_messages(callback.message, guild_id, guild["name"], member_info["rank"])
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка при открытии клан-чата: {e}")
        await callback.answer("❌ Произошла ошибка при открытии чата")

@router.message(F.text == "🔍 Найти клан")
async def find_guild(message: Message):
    # Получаем список открытых гильдий
    guilds = await guilds_collection.find({"is_open": True}).sort("level", -1).limit(10).to_list(length=10)
    
    if not guilds:
        await message.answer(
            "🔍 <b>Поиск кланов</b>\n\n"
            "❌ Открытых кланов не найдено.\n"
            "Создайте свой собственный клан!",
            reply_markup=guild_main_keyboard(),
            parse_mode="HTML"
        )
        return

    text = "🔍 <b>Открытые кланы:</b>\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for guild in guilds:
        members_count = len(guild.get("members", []))
        max_members = GUILD_BONUSES[guild.get("level", 1)]["members"]
        
        text += (
            f"⛵ <b>{guild['name']}</b>\n"
            f"⭐ Уровень {guild.get('level', 1)} | "
            f"👥 {members_count}/{max_members} | "
            f"💬 Чат активен\n"
            f"📝 {guild.get('description', 'Без описания')[:50]}...\n\n"
        )
        
        if members_count < max_members:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"⛵ Вступить в клан {guild['name']}", 
                    callback_data=f"join_guild:{guild['_id']}"
                )
            ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_guild_menu")
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "back_to_guild_menu")
async def back_to_guild_menu(callback: CallbackQuery):
    await guild_menu(callback.message)
    await callback.answer()

@router.message(F.text == "🏗️ Создать клан")
async def create_guild_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if user.get("guild_id"):
        await message.answer("❌ Вы уже состоите в клане!", reply_markup=guild_main_keyboard())
        return

    if user.get("money", 0) < 50000:
        await message.answer(
            "❌ <b>Недостаточно средств!</b>\n\n"
            "💰 Для создания клана нужно: <b>50,000$</b>\n"
            f"💰 У вас: <b>{user.get('money', 0):,}$</b>",
            reply_markup=guild_main_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🏗️ <b>Создание клана</b>\n\n"
        "⛵ Введите название вашего клана:\n"
        "(от 3 до 30 символов)",
        parse_mode="HTML"
    )
    await state.set_state(GuildState.creating_name)

@router.message(GuildState.creating_name)
async def create_guild_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 3 or len(name) > 30:
        await message.answer("❌ Название должно быть от 3 до 30 символов!")
        return

    # Проверяем уникальность названия
    existing = await guilds_collection.find_one({"name": name})
    if existing:
        await message.answer("❌ Клан с таким названием уже существует!")
        return

    await state.update_data(name=name)
    await message.answer(
        f"✅ Название принято: <b>{name}</b>\n\n"
        "📝 Теперь введите описание клана:\n"
        "(до 200 символов)",
        parse_mode="HTML"
    )
    await state.set_state(GuildState.creating_description)

@router.message(GuildState.creating_description)
async def create_guild_description(message: Message, state: FSMContext):
    description = message.text.strip()
    
    if len(description) > 200:
        await message.answer("❌ Описание должно быть не более 200 символов!")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    
    # Создаем гильдию
    guild_data = {
        "name": data["name"],
        "description": description,
        "captain_id": user_id,
        "level": 1,
        "experience": 0,
        "treasury": 0,
        "created_at": datetime.utcnow(),
        "is_open": True,
        "members": [{
            "user_id": user_id,
            "rank": "captain",
            "joined_at": datetime.utcnow(),
            "contribution_fish": 0,
            "contribution_stars": 0
        }],
        "tasks": [],
        "announcement": "",
        "chat_settings": {
            "enabled": True,
            "moderated": False,
            "slow_mode": False
        }
    }
    
    result = await guilds_collection.insert_one(guild_data)
    guild_id = result.inserted_id
    
    # Обновляем пользователя
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"guild_id": guild_id},
            "$inc": {"money": -50000}
        }
    )
    
    await message.answer(
        f"🎉 <b>Гильдия создана!</b>\n\n"
        f"⛵ Название: <b>{data['name']}</b>\n"
        f"📝 Описание: {description}\n"
        f"👑 Капитан: Вы\n"
        f"💬 Чат: активирован\n\n"
        f"💰 Потрачено: <b>50,000$</b>\n\n"
        f"🚀 Теперь вы можете приглашать участников, общаться в чате и развивать свою гильдию!",
        reply_markup=guild_main_keyboard(),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("join_guild:"))
async def join_guild(callback: CallbackQuery):
    user_id = callback.from_user.id
    guild_id = callback.data.split(":")[1]
    
    user = await users_collection.find_one({"user_id": user_id})
    if user.get("guild_id"):
        await callback.answer("❌ Вы уже состоите в гильдии!")
        return

    guild = await guilds_collection.find_one({"_id": guild_id})
    if not guild:
        await callback.answer("❌ Гильдия не найдена!")
        return

    members_count = len(guild.get("members", []))
    max_members = GUILD_BONUSES[guild.get("level", 1)]["members"]
    
    if members_count >= max_members:
        await callback.answer("❌ В гильдии нет свободных мест!")
        return

    # Добавляем участника
    new_member = {
        "user_id": user_id,
        "rank": "member",
        "joined_at": datetime.utcnow(),
        "contribution_fish": 0,
        "contribution_stars": 0
    }
    
    await guilds_collection.update_one(
        {"_id": guild_id},
        {"$push": {"members": new_member}}
    )
    
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"guild_id": guild_id}}
    )
    
    await callback.message.edit_text(
        f"🎉 <b>Добро пожаловать в гильдию!</b>\n\n"
        f"⛵ Вы вступили в гильдию: <b>{guild['name']}</b>\n"
        f"🏅 Ваш ранг: {GUILD_RANKS['member']['name']}\n"
        f"💬 Теперь у вас есть доступ к гильд-чату!\n\n"
        f"🎣 Теперь вы получаете бонусы гильдии к улову!",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "guild_members")
async def show_guild_members(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в клане!")
        return

    guild = await guilds_collection.find_one({"_id": guild_id})
    members = guild.get("members", [])
    
    text = f"👥 <b>Участники гильдии {guild['name']}</b>\n\n"
    
    # Сортируем по рангу и вкладу
    sorted_members = sorted(members, key=lambda x: (
        0 if x["rank"] == "captain" else 1 if x["rank"] == "officer" else 2,
        -x.get("contribution_fish", 0)
    ))
    
    for i, member in enumerate(sorted_members, 1):
        member_user = await users_collection.find_one({"user_id": member["user_id"]})
        name = member_user.get("nickname") or member_user.get("name") or f"Рыбак {member['user_id']}"
        rank_info = GUILD_RANKS[member["rank"]]
        
        # Показываем статус онлайн (упрощенно)
        last_visit = member_user.get("last_chat_visit")
        online_status = ""
        if last_visit and (datetime.utcnow() - last_visit).total_seconds() < 300:  # 5 минут
            online_status = " 🟢"
        
        text += (
            f"{i}. {rank_info['name']} <b>{name}</b>{online_status}\n"
            f"   🐟 {member.get('contribution_fish', 0):,} | "
            f"⭐ {member.get('contribution_stars', 0):,}\n\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_guild")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "back_to_guild")
async def back_to_guild(callback: CallbackQuery):
    # Возвращаемся к интерфейсу гильдии
    await my_guild(callback.message)
    await callback.answer()

@router.callback_query(F.data == "guild_donate")
async def guild_donate(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в клане!")
        return

    money = user.get("money", 0)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 1,000$", callback_data="donate_guild:1000")],
        [InlineKeyboardButton(text="💰 5,000$", callback_data="donate_guild:5000")],
        [InlineKeyboardButton(text="💰 10,000$", callback_data="donate_guild:10000")],
        [InlineKeyboardButton(text="💰 50,000$", callback_data="donate_guild:50000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_guild")]
    ])
    
    await callback.message.edit_text(
        f"💰 <b>Пожертвование в казну гильдии</b>\n\n"
        f"Выберите сумму для пожертвования:\n\n"
        f"💰 Ваши деньги: <b>{money:,}$</b>\n\n"
        f"💡 Пожертвования помогают развивать гильдию!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("donate_guild:"))
async def handle_guild_donate(callback: CallbackQuery):
    user_id = callback.from_user.id
    amount = int(callback.data.split(":")[1])
    
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    money = user.get("money", 0)
    
    if money < amount:
        await callback.answer("❌ Недостаточно денег!")
        return
    
    # Обновляем казну гильдии и деньги пользователя
    await guilds_collection.update_one(
        {"_id": guild_id},
        {"$inc": {"treasury": amount}}
    )
    
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"money": -amount}}
    )
    
    # Обновляем вклад участника
    await guilds_collection.update_one(
        {"_id": guild_id, "members.user_id": user_id},
        {"$inc": {"members.$.contribution_fish": amount // 10}}  # Условный вклад
    )
    
    await callback.answer(f"✅ Вы пожертвовали {amount:,}$ в казну гильдии!")
    
    # Возвращаемся к интерфейсу гильдии
    await my_guild(callback.message)

@router.callback_query(F.data == "guild_leave")
async def confirm_leave_guild(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, покинуть", callback_data="confirm_leave_guild"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_guild")
        ]
    ])
    
    await callback.message.edit_text(
        "🚪 <b>Покинуть гильдию</b>\n\n"
        "Вы уверены, что хотите покинуть гильдию?\n\n"
        "⚠️ Вы потеряете все гильдейские бонусы и доступ к чату.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm_leave_guild")
async def leave_guild(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await callback.answer("❌ Вы не состоите в клане!")
        return
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    
    # Проверяем, является ли пользователь капитаном
    is_captain = False
    for member in guild.get("members", []):
        if member["user_id"] == user_id and member["rank"] == "captain":
            is_captain = True
            break
    
    if is_captain:
        # Если капитан уходит, находим нового капитана среди офицеров
        officers = [m for m in guild.get("members", []) if m["rank"] == "officer" and m["user_id"] != user_id]
        
        if officers:
            # Назначаем первого офицера капитаном
            new_captain = officers[0]["user_id"]
            await guilds_collection.update_one(
                {"_id": guild_id, "members.user_id": new_captain},
                {"$set": {"members.$.rank": "captain"}}
            )
            
            # Удаляем пользователя из гильдии
            await guilds_collection.update_one(
                {"_id": guild_id},
                {"$pull": {"members": {"user_id": user_id}}}
            )
        else:
            # Если нет офицеров, находим участника с наибольшим вкладом
            members = [m for m in guild.get("members", []) if m["user_id"] != user_id]
            
            if members:
                # Сортируем по вкладу
                members.sort(key=lambda x: x.get("contribution_fish", 0) + x.get("contribution_stars", 0) * 10, reverse=True)
                new_captain = members[0]["user_id"]
                
                await guilds_collection.update_one(
                    {"_id": guild_id, "members.user_id": new_captain},
                    {"$set": {"members.$.rank": "captain"}}
                )
                
                # Удаляем пользователя из гильдии
                await guilds_collection.update_one(
                    {"_id": guild_id},
                    {"$pull": {"members": {"user_id": user_id}}}
                )
            else:
                # Если пользователь последний в гильдии, удаляем гильдию
                await guilds_collection.delete_one({"_id": guild_id})
    else:
        # Если обычный участник, просто удаляем его из гильдии
        await guilds_collection.update_one(
            {"_id": guild_id},
            {"$pull": {"members": {"user_id": user_id}}}
        )
    
    # Удаляем гильдию из профиля пользователя
    await users_collection.update_one(
        {"user_id": user_id},
        {"$unset": {"guild_id": ""}}
    )
    
    await callback.message.edit_text(
        "🚪 <b>Вы покинули гильдию</b>\n\n"
        "Теперь вы можете вступить в другую гильдию или создать свою.",
        parse_mode="HTML"
    )
    
    # Показываем меню гильдий
    await guild_menu(callback.message)

@router.message(F.text == "🏆 Рейтинг гильдий")
async def guild_rating(message: Message):
    guilds = await guilds_collection.find().sort("level", -1).limit(10).to_list(length=10)
    
    if not guilds:
        await message.answer("📊 Гильдий пока нет!", reply_markup=guild_main_keyboard())
        return

    text = "🏆 <b>Топ-10 гильдий:</b>\n\n"
    
    for i, guild in enumerate(guilds, 1):
        members_count = len(guild.get("members", []))
        total_fish = sum(member.get("contribution_fish", 0) for member in guild.get("members", []))
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        text += (
            f"{medal} <b>{guild['name']}</b>\n"
            f"⭐ Уровень {guild.get('level', 1)} | "
            f"👥 {members_count} участников | "
            f"💬 Чат активен\n"
            f"🐟 Общий улов: {total_fish:,}\n\n"
        )

    await message.answer(text, reply_markup=guild_main_keyboard(), parse_mode="HTML")

@router.message(F.text == "💬 Гильд-чат")
async def guild_chat_shortcut(message: Message):
    user_id = message.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        await message.answer("❌ Вы не состоите в клане!", reply_markup=guild_main_keyboard())
        return
    
    try:
        # Обновляем время последнего посещения чата
        from modules.guild_chat import update_last_chat_visit, show_chat_messages
        await update_last_chat_visit(user_id)
        
        guild = await guilds_collection.find_one({"_id": guild_id})
        member_info = None
        for member in guild.get("members", []):
            if member["user_id"] == user_id:
                member_info = member
                break
        
        await show_chat_messages(message, guild_id, guild["name"], member_info["rank"])
    except Exception as e:
        logging.error(f"Ошибка при открытии клан-чата: {e}")
        await message.answer("❌ Произошла ошибка при открытии чата", reply_markup=guild_main_keyboard())

@router.message(F.text == "◀️ В меню")
async def back_to_main_menu(message: Message):
    await message.answer("🎣 Главное меню", reply_markup=main_menu_keyboard())

# Функция для получения бонусов гильдии
async def get_guild_bonuses(user_id: int) -> dict:
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        return {"fish_bonus": 0, "star_bonus": 0}
    
    guild = await guilds_collection.find_one({"_id": guild_id})
    if not guild:
        return {"fish_bonus": 0, "star_bonus": 0}
    
    level = guild.get("level", 1)
    return GUILD_BONUSES[level]

# Функция для добавления вклада в гильдию
async def add_guild_contribution(user_id: int, fish: int = 0, stars: int = 0):
    user = await users_collection.find_one({"user_id": user_id})
    guild_id = user.get("guild_id")
    
    if not guild_id:
        return
    
    # Обновляем вклад участника
    await guilds_collection.update_one(
        {"_id": guild_id, "members.user_id": user_id},
        {
            "$inc": {
                "members.$.contribution_fish": fish,
                "members.$.contribution_stars": stars,
                "experience": fish + (stars * 10)  # Опыт гильдии
            }
        }
    )
    
    # Проверяем повышение уровня гильдии
    guild = await guilds_collection.find_one({"_id": guild_id})
    current_level = guild.get("level", 1)
    experience = guild.get("experience", 0)
    
    # Требования для повышения уровня
    level_requirements = {2: 10000, 3: 50000, 4: 150000, 5: 500000}
    
    for level, req_exp in level_requirements.items():
        if current_level < level and experience >= req_exp:
            await guilds_collection.update_one(
                {"_id": guild_id},
                {"$set": {"level": level}}
            )
            
            # Уведомляем всех участников о повышении уровня
            members = guild.get("members", [])
            for member in members:
                # Здесь можно отправить уведомление участникам
                pass
