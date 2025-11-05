# modules/admin/reset_boost.py

from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "🔄 Сбросить бусты")
async def reset_boosts(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    await message.answer("Введите ID игрока:")
    await state.set_state(AdminState.await_reset_boosts)

@router.message(AdminState.await_reset_boosts)
async def handle_reset_boosts(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text)

        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {
                "fish_multiplier": 1.0,
                "star_chance": 5.0,
                "luck_x2": 10.0,
                "boosters": {}
            }}
        )

        if result.matched_count == 0:
            await message.answer(f"❌ Игрок с ID {uid} не найден.")
        else:
            await message.answer(f"🔄 Бусты рыбака {uid} сброшены.")
    except ValueError:
        await message.answer("❌ Неверный формат ID. Пожалуйста, введите числовое значение.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        await state.clear()
