# modules/admin/player_list.py

from aiogram import Router, types
from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import users_collection, logger
from modules.nick import get_nickname
from modules.user_stats import create_progress_bar
from decimal import Decimal

router = Router(name="player_list")


def build_user_list_keyboard(users_on_page, page, total_pages):
    keyboard = []

    for user in users_on_page:
        uid = user["user_id"]
        nickname = user.get("nickname")
        username = user.get("username")

        if nickname:
            button_text = nickname
        elif username:
            button_text = f"@{username}"
        else:
            button_text = f"ID: {uid}"

        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"view_stats:{uid}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_page:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"next_page:{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "👥 Список игроков")
async def list_players(message: Message):
    try:
        page = 1
        users_per_page = 5

        total_users = await users_collection.count_documents({})
        total_pages = (total_users + users_per_page - 1) // users_per_page

        users_cursor = users_collection.find().skip((page - 1) * users_per_page).limit(users_per_page)
        users_on_page = await users_cursor.to_list(length=users_per_page)

        if not users_on_page:
            await message.answer("❌ Пользователи не найдены.")
            return

        await message.answer(
            f"👥 Страница {page}/{total_pages}\nВыберите ID, чтобы посмотреть статистику игрока:",
            reply_markup=build_user_list_keyboard(users_on_page, page, total_pages)
        )
    except Exception as e:
        logger.exception("Ошибка при выводе списка игроков")
        await message.answer("❌ Произошла ошибка при загрузке списка игроков.")


@router.callback_query(F.data.startswith("next_page:") | F.data.startswith("prev_page:"))
async def change_page(callback: CallbackQuery):
    try:
        page = int(callback.data.split(":")[1])
        users_per_page = 10

        total_users = await users_collection.count_documents({})
        total_pages = (total_users + users_per_page - 1) // users_per_page

        users_cursor = users_collection.find().skip((page - 1) * users_per_page).limit(users_per_page)
        users_on_page = await users_cursor.to_list(length=users_per_page)

        if not users_on_page:
            await callback.answer("❌ Нет пользователей на этой странице.")
            return

        await callback.message.edit_text(
            f"👥 Страница {page}/{total_pages}\nВыберите ID, чтобы посмотреть статистику игрока:",
            reply_markup=build_user_list_keyboard(users_on_page, page, total_pages)
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка при переключении страницы")
        await callback.answer("❌ Ошибка при загрузке страницы.", show_alert=True)


@router.callback_query(F.data.startswith("view_stats:"))
async def view_user_stats(callback: CallbackQuery):
    try:
        user_id_str = callback.data.split(":")[1]
        if not user_id_str.isdigit():
            await callback.answer("❌ Неверный ID пользователя.", show_alert=True)
            return

        user_id = int(user_id_str)
        user = await users_collection.find_one({"user_id": user_id})

        if not user:
            await callback.answer(f"❌ Игрок с ID {user_id} не найден.", show_alert=True)
            return

        nickname = user.get("nickname")
        username = user.get("username")

        stats = f"📊 Статистика игрока"
        if nickname:
            stats += f" {nickname}:\n"
        else:
            stats += f" ID {user_id}:\n"
        
        stats += f"🆔 : {user_id}\n"
        if username:
            stats += f"👤 username: {username}\n"
        stats += f"💰 Деньги: {user.get('money', 0)}$\n"
        stats += f"⛏️ Руда: {user.get('ore', 0)}\n"
        stats += f"🍪 Печеньки: {user.get('cookies', 0)}\n"
        stats += f"⛏ Уровень кирки: {user.get('pickaxe_level', 1)}\n"
        stats += f"🔒 Заблокирован: {'Да' if user.get('banned', False) else 'Нет'}"

        await callback.message.edit_text(stats, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_list")]
        ]))
        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка при просмотре статистики игрока")
        await callback.answer("❌ Ошибка при получении данных.", show_alert=True)


@router.callback_query(F.data == "back_to_list")
async def back_to_user_list(callback: CallbackQuery):
    try:
        page = 1
        users_per_page = 10

        total_users = await users_collection.count_documents({})
        total_pages = (total_users + users_per_page - 1) // users_per_page

        users_cursor = users_collection.find().skip((page - 1) * users_per_page).limit(users_per_page)
        users_on_page = await users_cursor.to_list(length=users_per_page)

        if not users_on_page:
            await callback.message.edit_text("❌ Пользователи не найдены.")
            return

        await callback.message.edit_text(
            f"👥 Страница {page}/{total_pages}\nВыберите ID, чтобы посмотреть статистику игрока:",
            reply_markup=build_user_list_keyboard(users_on_page, page, total_pages)
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка при возврате к списку игроков")
        await callback.answer("❌ Не удалось вернуться к списку.", show_alert=True)
