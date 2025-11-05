# modules/admin/analytics.py - Расширенная аналитика

from aiogram import Router, F
from aiogram.types import Message
from config import users_collection, db
from modules.admin.panel import is_admin, analytics_keyboard
from datetime import datetime, timedelta
import asyncio

router = Router(name="analytics")

@router.message(F.text == "📊 Общая статистика")
async def general_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Получаем общую статистику
    total_users = await users_collection.count_documents({})
    
    # Временные периоды
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Новые пользователи
    new_today = await users_collection.count_documents({"created_at": {"$gte": today}})
    new_week = await users_collection.count_documents({"created_at": {"$gte": week_ago}})
    new_month = await users_collection.count_documents({"created_at": {"$gte": month_ago}})
    
    # Активность
    active_today = await users_collection.count_documents({"last_fish_time": {"$gte": today}})
    active_week = await users_collection.count_documents({"last_fish_time": {"$gte": week_ago}})
    active_month = await users_collection.count_documents({"last_fish_time": {"$gte": month_ago}})
    
    # Донатеры
    donators = await users_collection.count_documents({
        "$or": [{"cookies": {"$gt": 0}}, {"is_donator": True}]
    })
    
    # Участники гильдий
    guild_members = await users_collection.count_documents({
        "guild_id": {"$exists": True, "$ne": None}
    })
    
    text = (
        f"📊 <b>Общая статистика бота</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"├ Всего: <b>{total_users:,}</b>\n"
        f"├ Новых сегодня: <b>{new_today}</b>\n"
        f"├ Новых за неделю: <b>{new_week}</b>\n"
        f"└ Новых за месяц: <b>{new_month}</b>\n\n"
        f"🎣 <b>Активность:</b>\n"
        f"├ Активных сегодня: <b>{active_today}</b> ({(active_today/total_users*100):.1f}%)\n"
        f"├ Активных за неделю: <b>{active_week}</b> ({(active_week/total_users*100):.1f}%)\n"
        f"└ Активных за месяц: <b>{active_month}</b> ({(active_month/total_users*100):.1f}%)\n\n"
        f"💎 <b>Монетизация:</b>\n"
        f"├ Донатеров: <b>{donators}</b> ({(donators/total_users*100):.1f}%)\n"
        f"└ Участников гильдий: <b>{guild_members}</b> ({(guild_members/total_users*100):.1f}%)\n\n"
        f"🕐 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "📈 Активность игроков")
async def activity_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Анализ активности по дням
    stats_by_days = []
    for days_ago in range(7):
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
        day_end = day_start + timedelta(days=1)
        
        active_count = await users_collection.count_documents({
            "last_fish_time": {"$gte": day_start, "$lt": day_end}
        })
        
        stats_by_days.append({
            "date": day_start.strftime("%d.%m"),
            "active": active_count
        })
    
    # Топ активных игроков
    top_active = await users_collection.find(
        {"total_fish_caught": {"$gt": 0}},
        {"user_id": 1, "nickname": 1, "name": 1, "total_fish_caught": 1, "last_fish_time": 1}
    ).sort("total_fish_caught", -1).limit(5).to_list(length=5)
    
    text = (
        f"📈 <b>Активность игроков</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 <b>Активность по дням:</b>\n"
    )
    
    for day_stat in reversed(stats_by_days):
        text += f"├ {day_stat['date']}: <b>{day_stat['active']}</b> игроков\n"
    
    text += f"\n🏆 <b>Топ активных игроков:</b>\n"
    
    for i, player in enumerate(top_active, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        fish_count = player.get("total_fish_caught", 0)
        last_active = player.get("last_fish_time")
        
        if last_active:
            days_ago = (datetime.utcnow() - last_active).days
            activity_text = f"({days_ago}д назад)" if days_ago > 0 else "(сегодня)"
        else:
            activity_text = "(никогда)"
        
        text += f"{i}. {name}: <b>{fish_count:,}</b> рыб {activity_text}\n"
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "💰 Экономическая сводка")
async def economy_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Экономическая статистика
    pipeline_money = [
        {"$group": {
            "_id": None,
            "total_money": {"$sum": "$money"},
            "avg_money": {"$avg": "$money"},
            "max_money": {"$max": "$money"}
        }}
    ]
    
    pipeline_fish = [
        {"$group": {
            "_id": None,
            "total_fish": {"$sum": "$total_fish_caught"},
            "avg_fish": {"$avg": "$total_fish_caught"}
        }}
    ]
    
    money_stats = await users_collection.aggregate(pipeline_money).to_list(length=1)
    fish_stats = await users_collection.aggregate(pipeline_fish).to_list(length=1)
    
    # Топ богачей
    rich_players = await users_collection.find(
        {"money": {"$gt": 0}},
        {"user_id": 1, "nickname": 1, "name": 1, "money": 1}
    ).sort("money", -1).limit(5).to_list(length=5)
    
    # Статистика по уровням
    level_stats = await users_collection.aggregate([
        {"$group": {"_id": "$rod_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}},
        {"$limit": 5}
    ]).to_list(length=5)
    
    money_data = money_stats[0] if money_stats else {}
    fish_data = fish_stats[0] if fish_stats else {}
    
    text = (
        f"💰 <b>Экономическая сводка</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💵 <b>Деньги в экономике:</b>\n"
        f"├ Общая сумма: <b>{money_data.get('total_money', 0):,.0f}$</b>\n"
        f"├ Средний баланс: <b>{money_data.get('avg_money', 0):,.0f}$</b>\n"
        f"└ Максимальный: <b>{money_data.get('max_money', 0):,.0f}$</b>\n\n"
        f"🐟 <b>Рыба:</b>\n"
        f"├ Всего поймано: <b>{fish_data.get('total_fish', 0):,.0f}</b>\n"
        f"└ В среднем на игрока: <b>{fish_data.get('avg_fish', 0):,.0f}</b>\n\n"
        f"🏆 <b>Топ богачей:</b>\n"
    )
    
    for i, player in enumerate(rich_players, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        money = player.get("money", 0)
        text += f"{i}. {name}: <b>{money:,}$</b>\n"
    
    text += f"\n🎣 <b>Распределение по уровням:</b>\n"
    for level_stat in level_stats:
        text += f"├ Уровень {level_stat['_id']}: <b>{level_stat['count']}</b> игроков\n"
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "🎣 Статистика рыбалки")
async def fishing_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Статистика рыбалки
    total_fish_caught = await users_collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_fish_caught"}}}
    ]).to_list(length=1)
    
    # Топ рыбаков
    top_fishers = await users_collection.find(
        {"total_fish_caught": {"$gt": 0}},
        {"user_id": 1, "nickname": 1, "name": 1, "total_fish_caught": 1, "rod_level": 1}
    ).sort("total_fish_caught", -1).limit(5).to_list(length=5)
    
    # Статистика по престижу
    prestige_stats = await users_collection.aggregate([
        {"$group": {"_id": "$prestige_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}}
    ]).to_list(length=None)
    
    total_fish = total_fish_caught[0]["total"] if total_fish_caught else 0
    
    text = (
        f"🎣 <b>Статистика рыбалки</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🐟 <b>Общая статистика:</b>\n"
        f"└ Всего поймано рыбы: <b>{total_fish:,}</b>\n\n"
        f"🏆 <b>Топ рыбаков:</b>\n"
    )
    
    for i, fisher in enumerate(top_fishers, 1):
        name = fisher.get("nickname") or fisher.get("name") or f"ID{fisher['user_id']}"
        fish_count = fisher.get("total_fish_caught", 0)
        rod_level = fisher.get("rod_level", 1)
        text += f"{i}. {name}: <b>{fish_count:,}</b> рыб (ур.{rod_level})\n"
    
    text += f"\n🏆 <b>Статистика престижа:</b>\n"
    for prestige_stat in prestige_stats:
        prestige_level = prestige_stat["_id"]
        count = prestige_stat["count"]
        if prestige_level == 0:
            text += f"├ Без престижа: <b>{count}</b> игроков\n"
        else:
            text += f"├ Престиж {prestige_level}: <b>{count}</b> игроков\n"
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "🏆 Рейтинги")
async def rankings_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Топ по разным категориям
    top_money = await users_collection.find().sort("money", -1).limit(3).to_list(length=3)
    top_fish = await users_collection.find().sort("total_fish_caught", -1).limit(3).to_list(length=3)
    top_stars = await users_collection.find().sort("sea_stars", -1).limit(3).to_list(length=3)
    top_cookies = await users_collection.find().sort("cookies", -1).limit(3).to_list(length=3)
    
    text = (
        f"🏆 <b>Рейтинги игроков</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Топ по деньгам:</b>\n"
    )
    
    for i, player in enumerate(top_money, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        money = player.get("money", 0)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        text += f"{medal} {name}: <b>{money:,}$</b>\n"
    
    text += f"\n🐟 <b>Топ по рыбе:</b>\n"
    for i, player in enumerate(top_fish, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        fish = player.get("total_fish_caught", 0)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        text += f"{medal} {name}: <b>{fish:,}</b> рыб\n"
    
    text += f"\n⭐ <b>Топ по звёздам:</b>\n"
    for i, player in enumerate(top_stars, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        stars = player.get("sea_stars", 0)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        text += f"{medal} {name}: <b>{stars}</b> ⭐\n"
    
    text += f"\n🍪 <b>Топ по печенькам:</b>\n"
    for i, player in enumerate(top_cookies, 1):
        name = player.get("nickname") or player.get("name") or f"ID{player['user_id']}"
        cookies = player.get("cookies", 0)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        text += f"{medal} {name}: <b>{cookies}</b> 🍪\n"
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "⛵ Статистика гильдий")
async def guild_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        guilds_collection = db["guilds"]
        
        # Общая статистика гильдий
        total_guilds = await guilds_collection.count_documents({})
        
        # Топ гильдий
        top_guilds = await guilds_collection.find().sort("level", -1).limit(5).to_list(length=5)
        
        # Статистика участников
        guild_members = await users_collection.count_documents({
            "guild_id": {"$exists": True, "$ne": None}
        })
        
        total_users = await users_collection.count_documents({})
        
        text = (
            f"⛵ <b>Статистика гильдий</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>Общая информация:</b>\n"
            f"├ Всего гильдий: <b>{total_guilds}</b>\n"
            f"├ Участников гильдий: <b>{guild_members}</b>\n"
            f"└ Охват: <b>{(guild_members/total_users*100):.1f}%</b>\n\n"
            f"🏆 <b>Топ гильдий:</b>\n"
        )
        
        for i, guild in enumerate(top_guilds, 1):
            name = guild.get("name", "Неизвестная")
            level = guild.get("level", 1)
            members_count = len(guild.get("members", []))
            text += f"{i}. <b>{name}</b> (ур.{level}) - {members_count} участников\n"
        
        if not top_guilds:
            text += "Гильдий пока нет\n"
        
    except Exception as e:
        text = (
            f"⛵ <b>Статистика гильдий</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ Ошибка получения данных о гильдиях\n"
            f"Возможно, система гильдий еще не инициализирована"
        )
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

@router.message(F.text == "📅 Ежедневная сводка")
async def daily_summary(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Сводка за сегодня
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    new_users_today = await users_collection.count_documents({"created_at": {"$gte": today}})
    active_today = await users_collection.count_documents({"last_fish_time": {"$gte": today}})
    
    # Статистика по времени (по часам)
    hourly_stats = []
    for hour in range(24):
        hour_start = today + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        
        if hour_end > datetime.utcnow():
            break
            
        active_hour = await users_collection.count_documents({
            "last_fish_time": {"$gte": hour_start, "$lt": hour_end}
        })
        
        if active_hour > 0:
            hourly_stats.append(f"{hour:02d}:00 - {active_hour} игроков")
    
    text = (
        f"📅 <b>Ежедневная сводка</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Сегодня ({today.strftime('%d.%m.%Y')}):</b>\n"
        f"├ Новых пользователей: <b>{new_users_today}</b>\n"
        f"└ Активных игроков: <b>{active_today}</b>\n\n"
        f"🕐 <b>Активность по часам:</b>\n"
    )
    
    if hourly_stats:
        for stat in hourly_stats[-10:]:  # Показываем последние 10 часов
            text += f"├ {stat}\n"
    else:
        text += "├ Нет данных за сегодня\n"
    
    text += f"\n🔄 Обновлено: {datetime.now().strftime('%H:%M')}"
    
    await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="HTML")

# Заглушки для будущих функций
@router.message(F.text == "📋 Отчеты")
async def reports_coming_soon(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📋 <b>Система отчетов</b>\n\n"
        "🚧 В разработке:\n"
        "• Еженедельные отчеты\n"
        "• Экспорт данных\n"
        "• Графики и диаграммы\n"
        "• Сравнительная аналитика\n\n"
        "Функция будет добавлена в следующих обновлениях!",
        reply_markup=analytics_keyboard(),
        parse_mode="HTML"
    )
