# modules/admin/give_cookies.py

from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "🍪 Выдать печеньки")
async def give_cookies(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    await message.answer("Введите: ID количество печенек\nПример: <code>12345 100</code>")
    await state.set_state(AdminState.await_cookies)

@router.message(AdminState.await_cookies)
async def handle_cookies(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат. Используйте: ID КОЛИЧЕСТВО печенек")

        uid = int(parts[0])
        value = int(parts[1])

        # Проверка на положительное количество
        if value <= 0:
            raise ValueError("Количество печенек должно быть положительным числом.")

        # Проверяем, существует ли пользователь в базе
        user = await users_collection.find_one({"user_id": uid})
        if not user:
            await message.answer(f"❌ Ошибка: Пользователь с ID {uid} не найден.")
            return

        # Выдаем печеньки пользователю
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"cookies": value}}
        )

        if result.matched_count == 0:
            await message.answer(f"❌ Ошибка: Не удалось выдать печеньки пользователю с ID {uid}.")
        else:
            await message.answer(f"✅ {value} печенек успешно выдано пользователю <code>{uid}</code>.")

    except ValueError as e:
        await message.answer(f"❌ Ошибка: {e}")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        await state.clear()
