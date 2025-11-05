# modules/admin/ban_unban_users.py

from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection  # Используем уже готовую коллекцию пользователей
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "🚫 Забанить игрока")
async def ban_user(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    await message.answer("Введите ID игрока, которого хотите забанить:\nПример: <code>12345</code>")
    await state.set_state(AdminState.await_ban)

@router.message(F.text == "✅ Разбанить игрока")
async def unban_user(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    await message.answer("Введите ID игрока, которого хотите разбанить:\nПример: <code>12345</code>")
    await state.set_state(AdminState.await_unban)

@router.message(AdminState.await_ban)
async def handle_ban(message: types.Message, state: FSMContext):
    try:
        # Получаем ID игрока
        uid = int(message.text.strip())

        # Проверяем, существует ли пользователь с таким ID
        user = await users_collection.find_one({"user_id": uid})
        if not user:
            await message.answer(f"❌ Ошибка: Пользователь с ID {uid} не найден.")
            return

        # Блокируем пользователя, если он найден
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {"banned": True}}
        )

        if result.matched_count == 0:
            await message.answer(f"❌ Ошибка: Не удалось заблокировать пользователя с ID {uid}.")
        else:
            await message.answer(f"🚫 Игрок с ID {uid} был успешно забанен.")

    except ValueError:
        await message.answer("❌ Ошибка: Пожалуйста, введите корректный числовой ID пользователя.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        await state.clear()

@router.message(AdminState.await_unban)
async def handle_unban(message: types.Message, state: FSMContext):
    try:
        # Получаем ID игрока
        uid = int(message.text.strip())

        # Проверяем, существует ли пользователь с таким ID
        user = await users_collection.find_one({"user_id": uid})
        if not user:
            await message.answer(f"❌ Ошибка: Пользователь с ID {uid} не найден.")
            return

        # Разблокируем пользователя, если он найден
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {"banned": False}}
        )

        if result.matched_count == 0:
            await message.answer(f"❌ Ошибка: Не удалось разбанить пользователя с ID {uid}.")
        else:
            await message.answer(f"✅ Игрок с ID {uid} был успешно разбанен.")

    except ValueError:
        await message.answer("❌ Ошибка: Пожалуйста, введите корректный числовой ID пользователя.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        await state.clear()
