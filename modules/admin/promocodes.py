# modules/admin/promocodes.py - Расширенное управление промокодами

from aiogram import Router
from aiogram import F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import db, users_collection
from modules.admin.panel import is_admin, admin_main_keyboard
from datetime import datetime, timedelta

router = Router(name="promocodes_admin")

promocodes_collection = db["promocodes"]

class PromoState(StatesGroup):
    creating_promo = State()
    editing_promo = State()
    mass_create = State()

def promocodes_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления промокодами"""
    buttons = [
        ["🎫 Создать промокод", "📋 Список промокодов"],
        ["📊 Статистика промокодов", "🔍 Поиск промокода"],
        ["✏️ Редактировать промокод", "🗑️ Удалить промокод"],
        ["📦 Массовое создание", "⏰ Временные промокоды"],
        ["◀️ Назад в админку"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )

@router.message(F.text == "🎫 Промокоды")
async def promocodes_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Статистика промокодов
    total_promos = await promocodes_collection.count_documents({})
    active_promos = await promocodes_collection.count_documents({
        "$or": [
            {"expires_at": {"$exists": False}},
            {"expires_at": {"$gte": datetime.utcnow()}}
        ]
    })
    
    # Использованные промокоды
    used_stats = await promocodes_collection.aggregate([
        {"$group": {"_id": None, "total_used": {"$sum": "$used_count"}}}
    ]).to_list(length=1)
    
    total_used = used_stats[0]["total_used"] if used_stats else 0
    
    text = (
        f"🎫 <b>Управление промокодами</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"├ Всего промокодов: <b>{total_promos}</b>\n"
        f"├ Активных: <b>{active_promos}</b>\n"
        f"└ Всего использований: <b>{total_used}</b>\n\n"
        f"🛠️ Выберите действие:"
    )
    
    await message.answer(text, reply_markup=promocodes_keyboard(), parse_mode="HTML")

@router.message(F.text == "🎫 Создать промокод")
async def create_promocode_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    text = (
        f"🎫 <b>Создание промокода</b>\n\n"
        f"📝 Введите данные в формате:\n"
        f"<code>КОД|награды|лимит|срок</code>\n\n"
        f"📋 <b>Примеры:</b>\n"
        f"<code>FISH2024|money:1000,sea_stars:10|100|7d</code>\n"
        f"<code>NEWBIE|cookies:5,fish:100|50|30d</code>\n"
        f"<code>WEEKEND|money:500|unlimited|2d</code>\n\n"
        f"💡 <b>Доступные награды:</b>\n"
        f"• money - деньги\n"
        f"• sea_stars - морские звёзды\n"
        f"• cookies - печеньки\n"
        f"• fish - рыба\n\n"
        f"⏰ <b>Формат срока:</b> 1d, 7d, 30d (дни) или unlimited"
    )
    
    await message.answer(text, parse_mode="HTML")
    await state.set_state(PromoState.creating_promo)

@router.message(PromoState.creating_promo)
async def create_promocode_finish(message: Message, state: FSMContext):
    try:
        parts = message.text.split("|")
        if len(parts) < 2:
            await message.answer("❌ Неверный формат! Минимум: КОД|награды")
            return
        
        code = parts[0].upper().strip()
        
        # Проверяем уникальность
        existing = await promocodes_collection.find_one({"code": code})
        if existing:
            await message.answer("❌ Промокод с таким названием уже существует!")
            return
        
        # Парсим награды
        rewards = {}
        if len(parts) > 1:
            rewards_str = parts[1]
            for reward in rewards_str.split(","):
                if ":" in reward:
                    key, value = reward.split(":")
                    key = key.strip()
                    if key in ["money", "sea_stars", "cookies", "fish"]:
                        rewards[key] = int(value.strip())
        
        # Парсим лимит
        max_uses = None
        if len(parts) > 2 and parts[2].strip().lower() != "unlimited":
            try:
                max_uses = int(parts[2].strip())
            except ValueError:
                pass
        
        # Парсим срок действия
        expires_at = None
        if len(parts) > 3 and parts[3].strip().lower() != "unlimited":
            try:
                days = int(parts[3].strip().replace("d", ""))
                expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                pass
        
        # Создаем промокод
        promo_data = {
            "code": code,
            "rewards": rewards,
            "max_uses": max_uses,
            "used_count": 0,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "created_by": message.from_user.id,
            "is_active": True
        }
        
        await promocodes_collection.insert_one(promo_data)
        
        # Формируем ответ
        reward_text = ", ".join([f"{k}:{v}" for k, v in rewards.items()])
        limit_text = str(max_uses) if max_uses else "Без лимита"
        expire_text = expires_at.strftime("%d.%m.%Y") if expires_at else "Без срока"
        
        text = (
            f"✅ <b>Промокод создан!</b>\n\n"
            f"🎫 Код: <code>{code}</code>\n"
            f"🎁 Награды: {reward_text}\n"
            f"📊 Лимит: {limit_text}\n"
            f"⏰ Действует до: {expire_text}"
        )
        
        await message.answer(text, reply_markup=promocodes_keyboard(), parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания промокода: {e}", reply_markup=promocodes_keyboard())
    
    await state.clear()

@router.message(F.text == "📋 Список промокодов")
async def list_promocodes(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Получаем промокоды с пагинацией
    promos = await promocodes_collection.find().sort("created_at", -1).limit(15).to_list(length=15)
    
    if not promos:
        await message.answer("📋 Промокодов нет", reply_markup=promocodes_keyboard())
        return
    
    text = "📋 <b>Список промокодов:</b>\n\n"
    
    for promo in promos:
        code = promo["code"]
        used = promo.get("used_count", 0)
        limit = promo.get("max_uses", "∞")
        rewards = promo.get("rewards", {})
        expires_at = promo.get("expires_at")
        is_active = promo.get("is_active", True)
        
        # Статус
        status = "🟢"
        if not is_active:
            status = "🔴"
        elif expires_at and expires_at < datetime.utcnow():
            status = "⏰"
        elif limit != "∞" and used >= limit:
            status = "📊"
        
        reward_text = ", ".join([f"{k}:{v}" for k, v in rewards.items()])
        expire_text = expires_at.strftime("%d.%m") if expires_at else "∞"
        
        text += (
            f"{status} <code>{code}</code>\n"
            f"├ {used}/{limit} | {reward_text}\n"
            f"└ До: {expire_text}\n\n"
        )
    
    await message.answer(text, reply_markup=promocodes_keyboard(), parse_mode="HTML")

@router.message(F.text == "📊 Статистика промокодов")
async def promocodes_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Общая статистика
    total_promos = await promocodes_collection.count_documents({})
    active_promos = await promocodes_collection.count_documents({"is_active": True})
    
    # Статистика использования
    usage_stats = await promocodes_collection.aggregate([
        {"$group": {
            "_id": None,
            "total_used": {"$sum": "$used_count"},
            "avg_used": {"$avg": "$used_count"}
        }}
    ]).to_list(length=1)
    
    # Топ промокодов по использованию
    top_promos = await promocodes_collection.find().sort("used_count", -1).limit(5).to_list(length=5)
    
    # Статистика по типам наград
    reward_stats = {}
    async for promo in promocodes_collection.find():
        for reward_type in promo.get("rewards", {}):
            reward_stats[reward_type] = reward_stats.get(reward_type, 0) + 1
    
    usage_data = usage_stats[0] if usage_stats else {}
    
    text = (
        f"📊 <b>Статистика промокодов</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 <b>Общая статистика:</b>\n"
        f"├ Всего промокодов: <b>{total_promos}</b>\n"
        f"├ Активных: <b>{active_promos}</b>\n"
        f"├ Всего использований: <b>{usage_data.get('total_used', 0)}</b>\n"
        f"└ Среднее использование: <b>{usage_data.get('avg_used', 0):.1f}</b>\n\n"
        f"🏆 <b>Топ промокодов:</b>\n"
    )
    
    for i, promo in enumerate(top_promos, 1):
        code = promo["code"]
        used = promo.get("used_count", 0)
        text += f"{i}. <code>{code}</code> - {used} использований\n"
    
    if reward_stats:
        text += f"\n🎁 <b>Популярные награды:</b>\n"
        for reward_type, count in sorted(reward_stats.items(), key=lambda x: x[1], reverse=True):
            text += f"├ {reward_type}: <b>{count}</b> промокодов\n"
    
    await message.answer(text, reply_markup=promocodes_keyboard(), parse_mode="HTML")

@router.message(F.text == "📦 Массовое создание")
async def mass_create_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    text = (
        f"📦 <b>Массовое создание промокодов</b>\n\n"
        f"📝 Введите данные в формате:\n"
        f"<code>ПРЕФИКС|количество|награды|лимит_на_код</code>\n\n"
        f"📋 <b>Пример:</b>\n"
        f"<code>EVENT|10|money:500,cookies:2|1</code>\n\n"
        f"Будет создано 10 промокодов:\n"
        f"EVENT001, EVENT002, ..., EVENT010\n"
        f"Каждый можно использовать 1 раз"
    )
    
    await message.answer(text, parse_mode="HTML")
    await state.set_state(PromoState.mass_create)

@router.message(PromoState.mass_create)
async def mass_create_finish(message: Message, state: FSMContext):
    try:
        parts = message.text.split("|")
        if len(parts) < 3:
            await message.answer("❌ Неверный формат!")
            return
        
        prefix = parts[0].upper().strip()
        count = int(parts[1].strip())
        
        if count > 100:
            await message.answer("❌ Максимум 100 промокодов за раз!")
            return
        
        # Парсим награды
        rewards = {}
        rewards_str = parts[2]
        for reward in rewards_str.split(","):
            if ":" in reward:
                key, value = reward.split(":")
                key = key.strip()
                if key in ["money", "sea_stars", "cookies", "fish"]:
                    rewards[key] = int(value.strip())
        
        # Лимит на код
        max_uses = 1
        if len(parts) > 3:
            try:
                max_uses = int(parts[3].strip())
            except ValueError:
                pass
        
        # Создаем промокоды
        created_codes = []
        for i in range(1, count + 1):
            code = f"{prefix}{i:03d}"
            
            # Проверяем уникальность
            existing = await promocodes_collection.find_one({"code": code})
            if existing:
                continue
            
            promo_data = {
                "code": code,
                "rewards": rewards,
                "max_uses": max_uses,
                "used_count": 0,
                "created_at": datetime.utcnow(),
                "created_by": message.from_user.id,
                "is_active": True,
                "is_mass_created": True,
                "mass_prefix": prefix
            }
            
            await promocodes_collection.insert_one(promo_data)
            created_codes.append(code)
        
        reward_text = ", ".join([f"{k}:{v}" for k, v in rewards.items()])
        
        text = (
            f"✅ <b>Массовое создание завершено!</b>\n\n"
            f"📦 Создано промокодов: <b>{len(created_codes)}</b>\n"
            f"🎁 Награды: {reward_text}\n"
            f"📊 Лимит на код: {max_uses}\n\n"
            f"🎫 Примеры кодов:\n"
        )
        
        # Показываем первые 5 кодов
        for code in created_codes[:5]:
            text += f"• <code>{code}</code>\n"
        
        if len(created_codes) > 5:
            text += f"• ... и еще {len(created_codes) - 5} кодов"
        
        await message.answer(text, reply_markup=promocodes_keyboard(), parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=promocodes_keyboard())
    
    await state.clear()

# Заглушки для будущих функций
@router.message(F.text.in_(["🔍 Поиск промокода", "✏️ Редактировать промокод", "🗑️ Удалить промокод", "⏰ Временные промокоды"]))
async def promocodes_coming_soon(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🚧 <b>В разработке</b>\n\n"
        "Эта функция будет добавлена в следующих обновлениях!",
        reply_markup=promocodes_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "◀️ Назад в админку")
async def back_to_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔐 Возвращаемся в админ-панель", reply_markup=admin_main_keyboard())
